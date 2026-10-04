"""Single source of truth for category classification.

Used by:
  * ``import_resources``  — CSV/JSON entries → category slug
  * ``recategorize``      — repairs categories already stored in MySQL

A weighted keyword table is used instead of plain substring counting, so a
title like "Machine Learning with Python" lands in *ai-machine-learning*
rather than *python*.
"""

import re

DEFAULT_CATEGORY = 'web-development'

# slug → {keyword: weight}. Multi-word / unambiguous terms weigh more.
CATEGORY_KEYWORDS = {
    'python': {
        'python': 3, 'django': 3, 'flask': 3, 'pandas': 3, 'numpy': 3,
        'scipy': 2, 'tkinter': 2, 'web scraping': 3,
        'automation': 2, 'oop': 2, 'scripting': 1,
    },
    'web-development': {
        'web development': 5, 'full stack': 5, 'web app': 3, 'html': 2,
        'css': 2, 'javascript': 3, 'jquery': 2, 'bootstrap': 2, 'react': 2,
        'angular': 2, 'vue': 2, 'node': 2, 'php': 2, 'laravel': 3,
        'wordpress': 3, 'responsive': 2, 'front end': 2, 'back end': 2,
        'web design': 3, 'web service': 2, 'api': 1, 'git ': 1,
    },
    'data-analytics': {
        'data analysis': 5, 'analytics': 3, 'sql': 3, 'mysql': 3, 'excel': 3,
        'power bi': 4, 'tableau': 4, 'pivot': 2, 'business intelligence': 4,
        'statistics': 2, 'dashboard': 2, 'financial': 2, 'finance': 2,
        'accounting': 3, 'banking': 1, 'stock market': 2, 'investment': 1,
        'bookkeeping': 3, 'database': 2, 'data mining': 3, 'reporting': 1,
        'ms office': 5, 'microsoft office': 5, 'ms excel': 5, 'office 365': 5,
        'microsoft excel': 5, 'powerpoint': 4, 'google sheets': 4, 'outlook': 3,
        'microsoft word': 4, 'word excel': 4,
    },
    'ai-machine-learning': {
        'machine learning': 6, 'deep learning': 6, 'artificial intelligence': 6,
        'neural network': 6, 'data science': 4, 'nlp': 4, 'natural language': 4,
        'computer vision': 6, 'tensorflow': 5, 'pytorch': 5, 'scikit': 5,
        'kaggle': 4, 'chatgpt': 5, 'llm': 4, 'generative ai': 6, 'openai': 4,
        'reinforcement learning': 6, 'ai model': 4, 'machine learn': 6,
        'predictive model': 4, 'model training': 3,
    },
    'ui-ux-design': {
        'ui/ux': 6, 'ux design': 6, 'ui design': 6, 'user experience': 6,
        'user interface': 5, 'figma': 6, 'adobe xd': 5, 'photoshop': 4,
        'illustrator': 4, 'indesign': 4, 'graphic design': 5, 'logo design': 5,
        'design thinking': 4, 'typography': 3, 'color theory': 3,
        'wireframe': 4, 'mockup': 3, 'blender': 3, 'autocad': 4, '3d model': 4,
        'after effects': 3, 'premiere pro': 3, 'animation': 2, 'sketch': 2,
    },
    'digital-marketing': {
        'digital marketing': 6, 'marketing': 3, 'seo': 5, 'social media': 5,
        'facebook ads': 6, 'google ads': 6, 'adwords': 5, 'affiliate': 5,
        'copywriting': 5, 'content marketing': 6, 'email marketing': 6,
        'branding': 4, 'dropshipping': 5, 'sales funnel': 5, 'instagram': 4,
        'youtube marketing': 5, 'growth hacking': 4, 'public relations': 3,
        'advertising': 3, 'e-commerce': 2, 'freelancing': 2, 'amazon fba': 5,
    },
}

# Kaggle "Udemy Courses" subject → our slug. '' = out of scope (row dropped).
SUBJECT_MAP = {
    'web development': 'web-development',
    'business finance': 'data-analytics',
    'graphic design': 'ui-ux-design',
    'it & software': 'python',
    'office productivity': 'data-analytics',
    'academics': 'ai-machine-learning',
    'personal development': 'digital-marketing',
    'design': 'ui-ux-design',
    'marketing': 'digital-marketing',
    # off-topic for a coding / design / data hub
    'musical instruments': '',
    'health & fitness': '',
    'lifestyle': '',
    'music': '',
    'photography': '',
}

DESC_PREFIX = 'Udemy course — '
DESC_SUFFIX = ' subject area.'


def keyword_scores(text):
    """slug → weighted keyword score for a piece of text."""
    hay = f' {str(text).lower()} '
    return {slug: sum(weight * hay.count(word) for word, weight in words.items())
            for slug, words in CATEGORY_KEYWORDS.items()}


def best_slug(text):
    """Winning slug for ``text`` (or '' when nothing matches)."""
    scores = keyword_scores(text)
    slug, score = max(scores.items(), key=lambda kv: kv[1])
    return slug if score > 0 else ''


def subject_is_offtopic(subject):
    return (subject or '').strip().lower() in SUBJECT_MAP and \
        SUBJECT_MAP[(subject or '').strip().lower()] == ''


def detect_category(text, subject=''):
    """Generic entry point for JSON / Coursera / YouTube rows.

    Always returns a valid slug (falls back to the subject map, then the
    default category) because those sources must never lose a resource.
    """
    slug = best_slug(text)
    if slug:
        return slug
    fallback = SUBJECT_MAP.get((subject or '').strip().lower(), '')
    return fallback or DEFAULT_CATEGORY


def classify_csv_title(title, subject=''):
    """Category for a Kaggle row; '' means the row is out of scope (drop it)."""
    subject_key = (subject or '').strip().lower()
    if subject_key in SUBJECT_MAP and SUBJECT_MAP[subject_key] == '':
        return ''
    slug = best_slug(title)
    if slug:
        return slug
    if subject_key in SUBJECT_MAP:
        return SUBJECT_MAP[subject_key]
    return ''  # unknown subject + no title signal → drop instead of guessing


def classify_from_description(description, title=''):
    """Recover the category of an already-imported Udemy row.

    The subject is embedded in the stored description, so re-categorising
    existing rows needs no extra column.
    """
    subject = subject_from_description(description)
    if subject:
        return classify_csv_title(title or '', subject)
    return best_slug(title or '')


def subject_from_description(description):
    """Extract the Kaggle subject kept inside a stored Udemy description."""
    text = description or ''
    if text.startswith(DESC_PREFIX) and text.endswith(DESC_SUFFIX):
        return text[len(DESC_PREFIX):-len(DESC_SUFFIX)]
    m = re.match(r'^Udemy course\s+\S+\s+(.+?) subject area\.$', text)
    return m.group(1) if m else ''


def subject_offtopic_from_description(description):
    return subject_is_offtopic(subject_from_description(description))

