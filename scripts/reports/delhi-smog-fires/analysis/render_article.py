# Fill article.en.tmpl.html with numbers from data.json, so no number in the text is typed by hand (draft 3).
# Tokens: {{entry_id.key.key}} or {{entry_id.key|,}} for thousands separators, {{...|+}} for a signed number, {{...|abs}}.
# Fails if a token has no value. python3 render_article.py
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, '..'); OUT = os.path.join(HERE, '..', '..', '..', '..', 'site', 'public', 'report', 'delhi-smog-fires')
E = {e['id']: e['value'] for e in json.load(open(os.path.join(OUT, 'data.json')))['evidence']}; used = set()
def sub(m):
    path, _, fmt = m.group(1).partition('|'); parts = path.strip().split('.'); v = E; used.add(parts[0])
    for p in parts:
        if isinstance(v, list): v = v[int(p)]
        elif p in v: v = v[p]
        else: sys.exit('no value for {{' + path + '}}')
    if v is None: sys.exit('empty value for {{' + path + '}}')
    if fmt == ',': return f'{v:,}'
    if fmt == '+': return ('+' if v > 0 else '−' if v < 0 else '') + f'{abs(v):g}'
    if fmt == 'abs': return f'{abs(v):g}'
    if isinstance(v, float): return f'{v:g}'.replace('-', '−')
    return str(v).replace('-', '−') if isinstance(v, int) else str(v)
n = 0
for L in ('en', 'ur', 'hi'):   # one template per language, same tokens; a language without a template falls back to English
    tp = os.path.join(REP, f'article.{L}.tmpl.html'); t = open(tp if os.path.exists(tp) else os.path.join(REP, 'article.en.tmpl.html'), encoding='utf-8').read()
    k = len(re.findall(r'\{\{', t)); n = n or k
    if k != n: sys.exit(f'{L} template has {k} tokens, English has {n}')
    open(os.path.join(REP, f'article.{L}.html'), 'w', encoding='utf-8').write(re.sub(r'\{\{([^}]+)\}\}', sub, t))
json.dump(sorted(used), open(os.path.join(HERE, 'data', 'entries_used_in_text.json'), 'w'))
print('tokens filled', n, 'entries used', len(used), 'entries not used in the text', sorted(set(E) - used))
