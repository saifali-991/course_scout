"""Language detection — CourseScout keeps **English + Hindi** courses only.

Detection order (best signal first):

1. the language YouTube itself reports (``snippet.defaultAudioLanguage`` /
   ``defaultLanguage`` on the API item);
2. Devanagari script anywhere in the text → Hindi;
3. an explicit marker ("… in Hindi", "हिंदी") or a channel that publishes in Hindi
   (CodeWithHarry, Chai aur Code, CampusX …);
4. a foreign marker ("Curso", "Türkçe", "教程" …) → that language code, which is
   *not* supported, so ``apply_languages`` deactivates the row;
5. everything else counts as English — the Kaggle CSVs ship no language column
   at all and the catalog is English-first.
"""

import re
import unicodedata

SUPPORTED_LANGUAGES = [
    {'code': 'en', 'label': 'English'},
    {'code': 'hi', 'label': 'Hindi'},
]
SUPPORTED_CODES = {c['code'] for c in SUPPORTED_LANGUAGES}
LANGUAGE_LABELS = {c['code']: c['label'] for c in SUPPORTED_LANGUAGES}

# YouTube sometimes answers with ISO-639-2 codes instead of ISO-639-1.
_ALIASES = {'eng': 'en', 'hin': 'hi', 'ind': 'id', 'por': 'pt', 'spa': 'es',
            'deu': 'de', 'fra': 'fr', 'rus': 'ru', 'ara': 'ar', 'tur': 'tr',
            'ita': 'it', 'nld': 'nl', 'pol': 'pl', 'ukr': 'uk', 'vie': 'vi',
            'tha': 'th', 'kor': 'ko', 'jpn': 'ja', 'zho': 'zh', 'ces': 'cs',
            'ell': 'el', 'heb': 'he', 'pes': 'fa', 'ben': 'bn', 'urd': 'ur',
            'tam': 'ta', 'tel': 'te', 'mar': 'mr', 'guj': 'gu', 'kan': 'kn',
            'mal': 'ml', 'pan': 'pa'}

DEVANAGARI_RE = re.compile(r'[\u0900-\u097F]')

# Non-Latin writing systems in a title or channel name are a reliable language
# signal — "Entri Coding മലയാളം" is Malayalam whatever the title says. Anything
# outside en/hi is deactivated by apply_languages, so the site only ever offers
# the two languages it claims to.
SCRIPT_RANGES = [
    (re.compile(r'[\u0d00-\u0d7f]'), 'ml'),   # Malayalam
    (re.compile(r'[\u0b80-\u0bff]'), 'ta'),   # Tamil
    (re.compile(r'[\u0c00-\u0c7f]'), 'te'),   # Telugu
    (re.compile(r'[\u0c80-\u0cff]'), 'kn'),   # Kannada
    (re.compile(r'[\u0980-\u09ff]'), 'bn'),   # Bengali / Assamese
    (re.compile(r'[\u0a80-\u0aff]'), 'gu'),   # Gujarati
    (re.compile(r'[\u0a00-\u0a7f]'), 'pa'),   # Punjabi (Gurmukhi)
    (re.compile(r'[\u0b00-\u0b7f]'), 'or'),   # Odia
    (re.compile(r'[\u0600-\u06ff]'), 'ar'),   # Arabic script (ar / fa / ur)
    (re.compile(r'[\u4e00-\u9fff]'), 'zh'),   # Chinese
    (re.compile(r'[\uac00-\ud7af]'), 'ko'),   # Korean
    (re.compile(r'[\u3040-\u30ff]'), 'ja'),   # Japanese kana
    (re.compile(r'[\u0e00-\u0e7f]'), 'th'),   # Thai
    (re.compile(r'[\u0400-\u04ff]'), 'ru'),   # Cyrillic
    (re.compile(r'[\u0370-\u03ff]'), 'el'),   # Greek
    (re.compile(r'[\u0590-\u05ff]'), 'he'),   # Hebrew
]
HINDI_MARKERS = ('hindi', 'हिंदी', 'हिन्दी', 'हिनदी', 'हिन्य')

# Channels that teach in Hindi — used when the title/API gives nothing away.
HINDI_CREATORS = {
    'codewithharry', 'code with harry', 'apna college', 'apna notes',
    'chaiaurcode', 'chai aur code', 'chai aur code with dev sharma', 'campusx',
    'campus x', 'wscube tech', 'wscubetech', 'thapa technical', 'codehelp',
    'codehelp - by babbar', 'sumit khandelwal', 'codebasics hindi',
    'technical guruji', 'simplilearn hindi', 'javat_point hindi',
}

# Markers that prove a course is *not* English/Hindi → dropped from the catalog.
FOREIGN_MARKERS = {
    'es': ['curso ', 'curso de', 'course español', 'en español', 'spanish'],
    'pt': ['curso ', 'português', 'portugues', 'em português'],
    'tr': ['türkçe', 'turkce', 'ders'],
    'de': ['deutsch', 'auf deutsch', 'anleitung'],
    'fr': ['français', 'francais', 'en français', 'formation '],
    'ru': ['на русском', 'русский', 'русском'],
    'ar': ['عربي', 'بالعربي'],
    'ja': ['日本語', 'チュートリアル'],
    'ko': ['한국어', '강의'],
    'zh': ['中文', '教程', '简体中文'],
    'id': ['bahasa indonesia'],
    'it': ['corso ', 'italiano'],
    'nl': ['nederlands'],
    'pl': ['polski', 'po polsku'],
    'uk': ['українськ'],
    'vi': ['tiếng việt', 'tien viet'],
    'th': ['ภาษาไทย'],
    'fa': ['فارسی'],
    'bn': ['বাংলা'],
    'ur': ['اردو'],
}


def _norm(code):
    """'en-US' → 'en', 'hin' → 'hi', '' → ''."""
    code = (code or '').strip().lower().replace('_', '-')[:3]
    if not code:
        return ''
    return _ALIASES.get(code, code[:2])


def is_supported(code):
    return _norm(code) in SUPPORTED_CODES


def language_label(code):
    return LANGUAGE_LABELS.get(_norm(code), _norm(code) or 'unknown')


def detect_language(*texts, api_language='', channel=''):
    """Return an ISO-639-1 code ('en', 'hi', 'es', …) for a resource."""
    api_code = _norm(api_language)
    if api_code:
        return api_code

    blob = ' '.join(t for t in texts if t)
    lowered = blob.lower()
    if DEVANAGARI_RE.search(blob):
        return 'hi'
    if any(marker in lowered for marker in HINDI_MARKERS):
        return 'hi'
    if (channel or '').strip().lower().replace('  ', ' ') in HINDI_CREATORS:
        return 'hi'
    for pattern, code in SCRIPT_RANGES:
        if pattern.search(blob):
            return code
    for code, markers in FOREIGN_MARKERS.items():
        if any(marker in lowered for marker in markers):
            return code
    return 'en'


# --- writing-system audit -----------------------------------------------------
# The catalog serves two languages, written in exactly two scripts: Latin
# (English) and Devanagari (Hindi). A title whose *letters* are written in any
# other script (CJK, kana, Hangul, Thai, Arabic, Cyrillic, Greek, Hebrew, the
# other Indic scripts, …) came from a search that ran without a language or a
# region, and `manage.py clean_invalid_titles` removes those rows.
SAFE_SCRIPTS = ('Latin', 'Devanagari')

# unicodedata.name() heads that are not a script name on their own.
_SCRIPT_ALIASES = {
    'Cjk': 'CJK',                       # CJK UNIFIED IDEOGRAPH-4E00
    'Kangxi': 'CJK',                    # KANGXI RADICAL ONE
    'Ideographic': 'CJK',               # IDEOGRAPHIC ITERATION MARK 々
    'Katakana-Hiragana': 'Katakana',    # KATAKANA-HIRAGANA PROLONGED SOUND MARK ー
    'Hangul-Jamo': 'Hangul',
}
# Width prefixes: HALFWIDTH KATAKANA LETTER A is still Katakana.
_NAME_NOISE = {'HALFWIDTH', 'FULLWIDTH'}
# Scripts whose letters double as maths symbols in English titles ("e^(πi)"):
# only a whole word (that many letters) proves the language, a lone π does not.
_SYMBOL_SCRIPTS = {'Greek': 3}


def _script_of(ch):
    """'あ' → 'Hiragana', 'a' → 'Latin', 'ह' → 'Devanagari', '' when unknown."""
    name = unicodedata.name(ch, '')
    if not name:
        return ''
    if 'ORDINAL INDICATOR' in name:  # ª º — Latin letter-ish punctuation
        return 'Latin'
    words = [w for w in name.split(' ') if w not in _NAME_NOISE]
    head = words[0].title() if words else ''
    return _SCRIPT_ALIASES.get(head, head)


def script_counts(text):
    """``{script: letters}`` for the letters of ``text``.

    Digits, spaces, punctuation, currency signs and emoji are skipped on purpose:
    "Python 45 ⚡️ सीखें" is Devanagari, not "some unknown script".
    """
    counts = {}
    for ch in unicodedata.normalize('NFC', text or ''):
        if unicodedata.category(ch)[0] != 'L':
            continue
        script = _script_of(ch)
        if script:
            counts[script] = counts.get(script, 0) + 1
    return counts


def letter_scripts(text):
    """Set of writing systems used by the *letters* of ``text`` ('' → empty set)."""
    return set(script_counts(text))


def foreign_scripts(text):
    """Sorted writing systems in ``text`` that are neither Latin nor Devanagari.

    Greek carries one footnote: ``π``, ``Σ`` and ``μ`` live inside English maths
    titles ("The dynamics of e^(πi)"), so a one-letter Greek symbol in an
    otherwise Latin title is treated as a symbol, while a real Greek course
    (whole Greek words) is still reported.
    """
    counts = script_counts(text)
    latin = counts.get('Latin', 0)
    return sorted(s for s, n in counts.items()
                  if s not in SAFE_SCRIPTS
                  and not (latin and n < _SYMBOL_SCRIPTS.get(s, 0)))


def is_english_or_hindi_title(text):
    """True when a title is written in Latin and/or Devanagari script only."""
    return not foreign_scripts(text)
