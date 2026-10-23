#!/usr/bin/env python3
"""Upload a rebuilt archive (backfill-days.py --rebuild) to KV a few hundred keys a day.

Cloudflare's free plan allows 1,000 KV writes a day (UTC) and the live feed uses about 350, so each run
uploads at most --max keys: whole seasons of day files, newest season first, then merges those dates'
entries into the live "days" index and "dist-YYYY" district lists. The index merge happens in the same run
as the day files, so a day page never pairs a new day file with an old summary.

The live feed rewrites "days" and "dist-<this year>" from its own copy every hour, so a merge that lands
while a feed run is in flight can be undone. Run this again later with --max 0: it re-reads the live
indexes and writes them only if a rebuilt entry is missing or different.

Uses wrangler (logged in), not an API token. Progress is kept in <dir>/pushed.json.

Usage:
  python3 -I scripts/push-archive.py --dir ~/.cache/hamarihawa/rebuild            # next chunk (400 keys)
  python3 -I scripts/push-archive.py --dir ~/.cache/hamarihawa/rebuild --max 0    # re-check the indexes only
  python3 -I scripts/push-archive.py --dir ... --dry-run                          # say what would be written
"""
import argparse, json, os, subprocess, sys, tempfile, time

NS = "80f0abe06205411bb5d4feb087c165f6"
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site")
BATCH_BYTES = 40 * 2**20  # wrangler's bulk upload takes up to 100 MB; stay well under


def wrangler(*args, capture=False):
    r = subprocess.run(["npx", "wrangler", "kv", *args, "--namespace-id", NS, "--remote"], cwd=SITE,
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"wrangler kv {args[0]} {args[1]} failed: {r.stderr.strip()[-300:]}")
    return r.stdout if capture else None


def get(key):
    out = wrangler("key", "get", key, capture=True)
    return json.loads(out) if out.strip().startswith("{") else {}


def put(key, value):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write(json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False))
    try:
        wrangler("key", "put", key, "--path", f.name)
    finally:
        os.unlink(f.name)


def feed_runs():
    """The fire feed's GitHub runs that haven't finished (the Worker's dispatches go through the same workflow)."""
    r = subprocess.run(["gh", "run", "list", "--workflow", "feed.yml", "-L", "20", "--json", "databaseId,status"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"gh run list failed: {r.stderr.strip()[-300:]}")
    return {x["databaseId"] for x in json.loads(r.stdout) if x["status"] != "completed"}


def wait_for_feed():
    for _ in range(60):
        if not feed_runs():
            return
        print("  waiting for a fire feed run to finish")
        time.sleep(30)
    sys.exit("the fire feed has been running for 30 minutes; try again later")


def merge(index, dist, done):
    """Merge the uploaded dates' entries into the live indexes, between feed runs. Each feed run reads "days" and
    dist-<this year> when it starts and writes them back at the end, so a merge landing inside a run would be undone
    by it (and the merge would overwrite what that run wrote). So wait until no run is going, read and write at once,
    and if a run started meanwhile, wait for it and check again. Returns the number of keys written."""
    writes = 0
    for attempt in range(3):
        wait_for_feed()
        live = get("days")
        if len(live) < 400:  # never replace the live index with a near-empty copy (a failed or garbled read)
            sys.exit(f"the live days index has {len(live)} entries; refusing to merge into it")
        stale = [x for x in sorted(done) if live.get(x) != index[x]]
        if stale:
            live.update({x: index[x] for x in done})
            put("days", live)
            writes += 1
            print(f"  days index: {len(stale)} entries updated")
        for y in sorted({x[:4] for x in done}):
            part = get(f"dist-{y}")
            if not part:
                sys.exit(f"dist-{y} is missing or unreadable; refusing to write it")
            mine = {x: dist[x] for x in done if x.startswith(y)}
            changed = sum(part.get(x) != v for x, v in mine.items())
            if changed:
                part.update(mine)
                put(f"dist-{y}", part)
                writes += 1
                print(f"  dist-{y}: {changed} dates updated")
        if not feed_runs():
            return writes
        print("  a fire feed run started during the merge; checking again after it")
    print("  the feed kept running; run this again with --max 0 later")
    return writes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--max", type=int, default=400, help="most KV writes this run, indexes included")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    d = os.path.expanduser(a.dir)
    index = json.load(open(os.path.join(d, "days.json")))
    dist = json.load(open(os.path.join(d, "dist.json"), encoding="utf-8"))
    state_path = os.path.join(d, "pushed.json")
    pushed = set(json.load(open(state_path))) if os.path.exists(state_path) else set()

    # Whole seasons (or months), newest first, as long as they fit with the index writes they need.
    groups = {}
    for date in sorted(index):
        if date not in pushed:
            groups.setdefault(date[:4] if date[5:7] in ("10", "11") and date[:4] < "2026" else date[:7], []).append(date)
    todo, years = [], {x[:4] for x in pushed}  # every uploaded year's dist key may need a repair write
    for g in sorted(groups, reverse=True):
        need = len(todo) + len(groups[g]) + 1 + len(years | {g[:4]})
        if need > a.max:
            break
        todo += groups[g]
        years.add(g[:4])
    left = sum(len(v) for v in groups.values()) - len(todo)
    print(f"{len(pushed)} days uploaded before; this run: {len(todo)} day files, then the indexes; {left} days left after")
    if a.dry_run:
        print("  dates:", ", ".join(f"{todo[0]}..{todo[-1]}" for _ in [0] if todo) or "none")
        return

    # 1. Day files, in batches.
    batch, size = [], 0
    def flush():
        nonlocal batch, size
        if not batch:
            return
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False)
        try:
            wrangler("bulk", "put", f.name)
        finally:
            os.unlink(f.name)
        print(f"  uploaded {len(batch)} day files ({size // 2**20} MB)")
        batch, size = [], 0
    for date in todo:
        body = open(os.path.join(d, "days", f"{date}.json"), encoding="utf-8").read()
        if size + len(body) > BATCH_BYTES:
            flush()
        batch.append({"key": f"day-{date}", "value": body})
        size += len(body)
    flush()
    # Recorded now, so a failure below doesn't cost a second upload: --max 0 merges every recorded date.
    done = pushed | set(todo)
    json.dump(sorted(done), open(state_path, "w"))

    # 2. Indexes: every uploaded date (this run's and earlier runs'), merged into the live copies.
    merge(index, dist, done)
    print(f"done: {len(done)} of {len(index)} rebuilt days are live")


if __name__ == "__main__":
    main()
