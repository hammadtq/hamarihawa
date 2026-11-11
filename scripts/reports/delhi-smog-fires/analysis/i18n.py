# Chart labels in English, Urdu or Hindi: python3.12 <chart>.py [en|ur|hi]
# Translations live in strings.<lang>.json, keyed by the English text.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
LANG = sys.argv[1] if len(sys.argv) > 1 else "en"
_D = {} if LANG == "en" else json.load(open(os.path.join(HERE, f"strings.{LANG}.json"), encoding="utf-8"))
MISSING = []
SUFFIX = "" if LANG == "en" else "." + LANG
FONT = {"en": "Helvetica, Arial, sans-serif",
        "ur": "'Noto Naskh Arabic', 'Geeza Pro', Tahoma, Arial, sans-serif",  # Naskh: Nastaliq is too tall for chart labels
        "hi": "'Noto Sans Devanagari', 'Kohinoor Devanagari', Mangal, Nirmala UI, Arial, sans-serif"}[LANG]
OUT = os.path.join(HERE, "..", "..", "..", "..", "site", "public", "report", "delhi-smog-fires")


def T(s):
    if LANG == "en":
        return s
    if s not in _D:
        MISSING.append(s)
        return s
    return _D[s]


def save(name, svg):
    open(os.path.join(OUT, f"{name}{SUFFIX}.svg"), "w", encoding="utf-8").write(svg)
    if MISSING:
        sys.exit(f"{name}: missing {LANG} strings: {MISSING}")
