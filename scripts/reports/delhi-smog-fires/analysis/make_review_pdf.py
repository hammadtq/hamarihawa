# Print the review PDF of the built report page (draft 4). The site page is left as it is; this makes a print copy that
#   - drops the site header, menus, share buttons and footer, and the hidden Urdu/Hindi placeholders,
#   - numbers the pages, keeps headings with what follows them and keeps figures and tables whole,
#   - turns the two relative links (data.json, the animation) into the names of the packaged files, so nothing points at a local server,
# then checks the link annotations inside the PDF itself and fails if any is not an absolute https link.
# python3 make_review_pdf.py <out.pdf> [label]   (needs Google Chrome; serves site/public on a free local port while printing)
import os, re, sys, subprocess, zlib, http.server, socketserver, threading, functools
HERE = os.path.dirname(os.path.abspath(__file__)); PUB = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'site', 'public')); REP = os.path.join(PUB, 'report', 'delhi-smog-fires')
out = os.path.abspath(sys.argv[1]); label = sys.argv[2] if len(sys.argv) > 2 else 'review draft'
s = open(os.path.join(REP, 'index.html'), encoding='utf-8').read()
s = re.sub(r'<article data-lang="(ur|hi)" hidden>.*?</article>', '', s, flags=re.S)
s = re.sub(r'<header class="top">.*?</header>', '', s, flags=re.S); s = re.sub(r'<footer class="site-foot".*?</footer>', '', s, flags=re.S); s = re.sub(r'<div class="rshare">.*?</div>', '', s, flags=re.S)
s = re.sub(r'<a href="data\.json">(.*?)</a>', r'\1 (file <code>site/public/report/delhi-smog-fires/data.json</code> in the evidence ZIP)', s, flags=re.S)
s = re.sub(r'<a href="(smoke-[^"]+\.mp4)">(.*?)</a>', r'The full-size image and the animation are supplied separately as <code>smoke-november-2025.jpg</code> and <code>\1</code>.', s, flags=re.S)
css = '''<style>
@page { size: A4; margin: 16mm 14mm 18mm; @bottom-center { content: "HamariHawa · ''' + label + ''' · page " counter(page) " of " counter(pages); font: 9px Helvetica, Arial, sans-serif; color: #777; } }
html, body { background: #fff !important; } main.doc { max-width: none !important; padding: 0 !important; margin: 0 !important; }
h2, h3 { break-after: avoid-page; page-break-after: avoid; } figure, .table-wrap, .facts, .callout, li { break-inside: avoid; page-break-inside: avoid; }
h2 + figure, h2 + p { break-before: avoid-page; } p { break-inside: avoid; page-break-inside: avoid; } .rfig img { max-height: 235mm; object-fit: contain; }
.sketch > svg.rough { display: none !important; } .sketch { border: 1.2px solid #333 !important; border-radius: 6px; } .callout { padding: 10px 16px !important; }
ol.refs, main ul { padding-left: 2.2em !important; }
</style></head>'''
s = s.replace('</head>', css, 1)
left = re.findall(r'href="(?!https://|#)([^"]*)"', s[s.index('<body'):])
if left: sys.exit('relative links left in the print copy: ' + str(left))
tmp = os.path.join(REP, '_review_print.html'); open(tmp, 'w', encoding='utf-8').write(s)
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=PUB); H.log_message = lambda *a: None
srv = socketserver.TCPServer(('127.0.0.1', 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
try:
    subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--headless=new', '--no-pdf-header-footer', '--virtual-time-budget=8000', '--print-to-pdf=' + out,
                    f'http://127.0.0.1:{srv.server_address[1]}/report/delhi-smog-fires/_review_print.html'], check=True, capture_output=True, timeout=180)
finally:
    srv.shutdown(); os.remove(tmp)
raw = open(out, 'rb').read(); blob = raw
for m in re.finditer(rb'stream\r?\n(.*?)\r?\nendstream', raw, flags=re.S):
    try: blob += zlib.decompress(m.group(1))
    except Exception: pass
uris = sorted({u.decode('latin1') for u in re.findall(rb'/URI\s*\((.*?)\)', blob)})
bad = [u for u in uris if not u.startswith('https://')]
print(len(uris), 'distinct links in the PDF; not https:', bad); print('pages', len(re.findall(rb'/Type\s*/Page[^s]', blob)))
if bad: sys.exit('non-portable links in the PDF')
