# Fill article.<lang>.tmpl.html with numbers from data.json, so no number in the text is typed by hand.
# Tokens: {{entry_id.key.key}}; {{...|,}} thousands separators; {{...|1}} one decimal; {{...|cell}} a rainfall table cell
# (number with one decimal, "trace" in the page's language, or an en dash where the report gave no figure).
# Fails if a token has no value or the three templates do not use the same tokens. python3 render_article.py
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, '..')
OUT = os.path.join(HERE, '..', '..', '..', '..', 'site', 'public', 'report', 'punjab-rain-nov-2026')
E = {e['id']: e['value'] for e in json.load(open(os.path.join(OUT, 'data.json'), encoding='utf-8'))['evidence']}
TRACE = {'en': 'trace', 'ur': 'برائے نام', 'hi': 'नाममात्र'}
def fill(t, L):
    toks = []
    def sub(m):
        path, _, fmt = m.group(1).partition('|'); v = E; toks.append(m.group(1))
        for p in path.strip().split('.'):
            if isinstance(v, list): v = v[int(p)]
            elif p in v: v = v[p]
            else: sys.exit(L + ': no value for {{' + path + '}}')
        if fmt == 'cell': return '–' if v is None else TRACE[L] if v == 'trace' else f'{v:.1f}'
        if v is None: sys.exit(L + ': empty value for {{' + path + '}}')
        if fmt == ',': return f'{v:,}'
        if fmt == '1': return f'{v:.1f}'
        if isinstance(v, float): return f'{v:g}'
        return str(v)
    return re.sub(r'\{\{([^}]+)\}\}', sub, t), toks
ref = None
for L in ('en', 'ur', 'hi'):
    out, toks = fill(open(os.path.join(REP, f'article.{L}.tmpl.html'), encoding='utf-8').read(), L)
    if ref is None: ref = sorted(toks)
    elif sorted(toks) != ref:
        a, b = set(ref), set(toks); sys.exit(f'{L} template tokens differ from English: missing {sorted(a - b)}, extra {sorted(b - a)}, counts {len(ref)} vs {len(toks)}')
    open(os.path.join(REP, f'article.{L}.html'), 'w', encoding='utf-8').write(out)
print('tokens filled per language:', len(ref))
