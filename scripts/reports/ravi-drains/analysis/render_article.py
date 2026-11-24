# Fill article.<lang>.tmpl.html with numbers from data.json, so no number in the text is typed by hand.
# Tokens: {{entry_id.key.key}}; {{...|,}} thousands separators; {{...|1}} one decimal; {{...|dt}} a "YYYY-MM-DD HH:MM"
# value as day, month, year and time in the page's language; {{...|t}} a text value translated; {{...|d}} the same without the time. Fails if a token has no value or the templates that
# exist do not use the same tokens. python3 render_article.py
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); REP = os.path.join(HERE, '..')
OUT = os.path.join(HERE, '..', '..', '..', '..', 'site', 'public', 'report', 'ravi-drains')
E = {e['id']: e['value'] for e in json.load(open(os.path.join(OUT, 'data.json'), encoding='utf-8'))['evidence']}
MON = {'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
       'ur': ['جنوری', 'فروری', 'مارچ', 'اپریل', 'مئی', 'جون', 'جولائی', 'اگست', 'ستمبر', 'اکتوبر', 'نومبر', 'دسمبر'],
       'hi': ['जनवरी', 'फ़रवरी', 'मार्च', 'अप्रैल', 'मई', 'जून', 'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर']}
EN_MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
TR = {'ur': {'EMIT (space station)': 'EMIT (خلائی اسٹیشن)', 'Sundar': 'سندر', 'Tibba': 'ٹبہ', 'Saggian': 'سگیاں'},
      'hi': {'EMIT (space station)': 'EMIT (अंतरिक्ष स्टेशन)', 'Sundar': 'सुंदर', 'Tibba': 'टिब्बा', 'Saggian': 'सग्गियां'}}
def tr(v, L):  # {{...|t}}: a text value (a month and year, an instrument, a place name) in the page's language
    if L == 'en': return v
    if v in TR[L]: return TR[L][v]
    for i, m in enumerate(EN_MON): v = v.replace(m, MON[L][i])
    if re.search('[A-Za-z]{3}', v) and v != 'Tanager-1': sys.exit(L + ': no translation for ' + v)
    return v
def fill(t, L):
    toks = []
    def sub(m):
        path, _, fmt = m.group(1).partition('|'); v = E; toks.append(m.group(1))
        for p in path.strip().split('.'):
            if isinstance(v, list): v = v[int(p)]
            elif p in v: v = v[p]
            else: sys.exit(L + ': no value for {{' + path + '}}')
        if v is None: sys.exit(L + ': empty value for {{' + path + '}}')
        if fmt == 'dt': return f'{int(v[8:10])} {MON[L][int(v[5:7]) - 1]} {v[:4]}, {v[11:]}'
        if fmt == 'd': return f'{int(v[8:10])} {MON[L][int(v[5:7]) - 1]} {v[:4]}'
        if fmt == 't': return tr(v, L)
        if fmt == ',': return f'{v:,}'
        if fmt == '1': return f'{v:.1f}'
        if isinstance(v, float): return f'{v:g}'
        return str(v)
    return re.sub(r'\{\{([^}]+)\}\}', sub, t), toks
ref = None
for L in ('en', 'ur', 'hi'):
    p = os.path.join(REP, f'article.{L}.tmpl.html')
    if not os.path.exists(p): print('no', L, 'template yet'); continue
    out, toks = fill(open(p, encoding='utf-8').read(), L)
    if ref is None: ref = sorted(toks)
    elif sorted(toks) != ref:
        a, b = set(ref), set(toks); sys.exit(f'{L} template tokens differ from English: missing {sorted(a - b)}, extra {sorted(b - a)}, counts {len(ref)} vs {len(toks)}')
    open(os.path.join(REP, f'article.{L}.html'), 'w', encoding='utf-8').write(out)
print('tokens filled per language:', len(ref))
