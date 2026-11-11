# Build the evidence ZIP for review. Its root mirrors the repository, with the raw downloads under raw/ and an empty out/, so that
#   sh scripts/reports/delhi-smog-fires/analysis/run_all.sh
# works from the unpacked folder with nothing else. python3 package_evidence.py <out.zip> H
import os, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
out, H = os.path.abspath(sys.argv[1]), sys.argv[2]
REP = 'scripts/reports/delhi-smog-fires'; SITE = 'site/public/report/delhi-smog-fires'
RAW = ['openaq', 'openaq_hours', 'openaq_days_full', 'openaq_probe', 'firms', 'era5', 'windgrid', 'windouter']
n = 0
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    def add(src, arc):
        global n
        if os.path.basename(src).startswith('.') or src.endswith('.pyc'): return
        z.write(src, arc); n += 1
    def tree(src, arc, skip=()):
        for root, dirs, files in os.walk(src):
            dirs[:] = sorted(d for d in dirs if d not in skip and d != '__pycache__')
            for f in sorted(files): add(os.path.join(root, f), os.path.join(arc, os.path.relpath(os.path.join(root, f), src)))
    for f in ('article.en.tmpl.html', 'article.en.html', 'meta.json'): add(os.path.join(REPO, REP, f), f'{REP}/{f}')
    tree(os.path.join(REPO, REP, 'analysis'), f'{REP}/analysis')
    for f in sorted(os.listdir(os.path.join(REPO, SITE))):
        if f.endswith(('.json', '.svg', '.jpg')): add(os.path.join(REPO, SITE, f), f'{SITE}/{f}')
    for d in RAW:
        if not os.path.isdir(os.path.join(H, 'raw', d)): sys.exit('missing raw/' + d)
        tree(os.path.join(H, 'raw', d), f'raw/{d}')
    add(os.path.join(REPO, REP, 'analysis', 'README.md'), 'README.md'); add(os.path.join(REPO, REP, 'analysis', 'MANIFEST.json'), 'MANIFEST.json')
    z.writestr('out/README.txt', 'run_all.sh writes its intermediate files and logs here.\n')
print('files', n, 'MB', round(os.path.getsize(out) / 1e6, 1))
