"""Thumbnails for resources.

Sources like the Kaggle CSVs ship no images at all (the CSV header has no image
column), and we only ever store URLs — never files — so a resource gets its
picture from, in order:

  1. ``thumbnail_url`` from the source metadata (YouTube API, curated JSON ...);
  2. a **topic-matched stock photo** from ``CATEGORY_PHOTOS`` below, hotlinked
     from the Unsplash / Pexels CDNs. Every URL here was verified to answer
     HTTP 200 with an ``image/*`` content type (see README "Images");
  3. a locally generated SVG gradient card (``placeholder_thumbnail``) as the
     final "never broken" fallback.

Photos are picked deterministically from the resource id, so a course always
shows the same picture and pagination never reshuffles the grid.
Credits: Unsplash (unsplash.com/license) + Pexels (pexels.com/license) — free to
hotlink; also listed in the README.
"""

import base64
import html
import re

# --- topic-matched photos -------------------------------------------------
# Grouped by category slug (resources.categories.CATEGORIES).
UNS = 'https://images.unsplash.com/'
PEX = 'https://images.pexels.com/photos/'
UNS_Q = '?auto=format&fit=crop&w=800&q=70'
PEX_Q = '?auto=compress&cs=tinysrgb&w=800'

CATEGORY_PHOTOS = {
    'python': [
        UNS + 'photo-1526374965328-7f61d4dc18c5' + UNS_Q,
        UNS + 'photo-1555066931-4365d14bab8c' + UNS_Q,
        UNS + 'photo-1515879218367-8466d910aaa4' + UNS_Q,
        UNS + 'photo-1542831371-29b0f74f9713' + UNS_Q,
        UNS + 'photo-1523800503107-5bc3ba2a6f81' + UNS_Q,
        UNS + 'photo-1516116216624-53e697fedbea' + UNS_Q,
        PEX + '577585/pexels-photo-577585.jpeg' + PEX_Q,
    ],
    'web-development': [
        UNS + 'photo-1498050108023-c5249f4df085' + UNS_Q,
        UNS + 'photo-1461749280684-dccba630e2f6' + UNS_Q,
        UNS + 'photo-1504639725590-34d0984388bd' + UNS_Q,
        UNS + 'photo-1526498460520-4c246339dccb' + UNS_Q,
        UNS + 'photo-1547658719-da2b51169166' + UNS_Q,
        UNS + 'photo-1555066932-e78dd8fb77bb' + UNS_Q,
        PEX + '1181671/pexels-photo-1181671.jpeg' + PEX_Q,
    ],
    'data-analytics': [
        UNS + 'photo-1551288049-bebda4e38f71' + UNS_Q,
        UNS + 'photo-1460925895917-afdab827c52f' + UNS_Q,
        UNS + 'photo-1543286386-713bdd548da4' + UNS_Q,
        UNS + 'photo-1504868584819-f8e8b4b6d7e3' + UNS_Q,
        UNS + 'photo-1591696205602-2f950c417cb9' + UNS_Q,
        UNS + 'photo-1542744173-8e7e53415bb0' + UNS_Q,
        PEX + '590022/pexels-photo-590022.jpeg' + PEX_Q,
    ],
    'ai-machine-learning': [
        UNS + 'photo-1620712943543-bcc4688e7485' + UNS_Q,
        UNS + 'photo-1677442136019-21780ecad995' + UNS_Q,
        UNS + 'photo-1531746790731-6c087fecd65a' + UNS_Q,
        UNS + 'photo-1507146426996-ef05306b995a' + UNS_Q,
        UNS + 'photo-1555255707-c07966088b7b' + UNS_Q,
        UNS + 'photo-1485827404703-89b55fcc595e' + UNS_Q,
        PEX + '8386440/pexels-photo-8386440.jpeg' + PEX_Q,
    ],
    'ui-ux-design': [
        UNS + 'photo-1561070791-2526d30994b5' + UNS_Q,
        UNS + 'photo-1559028012-481c04fa702d' + UNS_Q,
        UNS + 'photo-1581291518857-4e27b48ff24e' + UNS_Q,
        UNS + 'photo-1541462608143-67571c6738dd' + UNS_Q,
        UNS + 'photo-1586717791821-3f44a563fa4c' + UNS_Q,
        UNS + 'photo-1522542550221-31fd19575a2d' + UNS_Q,
        PEX + '196644/pexels-photo-196644.jpeg' + PEX_Q,
    ],
    'digital-marketing': [
        UNS + 'photo-1533750349088-cd871a92f312' + UNS_Q,
        UNS + 'photo-1557838923-2985c318be48' + UNS_Q,
        UNS + 'photo-1611926653458-09294b3142bf' + UNS_Q,
        UNS + 'photo-1553877522-43269d4ea984' + UNS_Q,
        UNS + 'photo-1432888622747-4eb9a8efeb07' + UNS_Q,
        UNS + 'photo-1563986768609-322da13575f3' + UNS_Q,
        PEX + '905163/pexels-photo-905163.jpeg' + PEX_Q,
    ],
}

GENERIC_PHOTOS = CATEGORY_PHOTOS['web-development']

TOPIC_COLORS = {
    'python': ('#1d6ff2', '#7c3aed'),
    'web-development': ('#f97316', '#ef4444'),
    'data-analytics': ('#ef4460', '#f59e0b'),
    'ai-machine-learning': ('#3b82f6', '#22d3ee'),
    'ui-ux-design': ('#0891b2', '#22d3ee'),
    'digital-marketing': ('#6366f1', '#a855f7'),
}
DEFAULT_COLORS = ('#1d6ff2', '#0b1029')


def photo_thumbnail(category='', key=0):
    """A stable, topic-matched stock photo URL for this category + resource."""
    pool = CATEGORY_PHOTOS.get(category) or GENERIC_PHOTOS
    return pool[_hash(key) % len(pool)]


# --- real YouTube frames ---------------------------------------------------
# Every public YouTube video serves its own thumbnail from i.ytimg.com — no API
# key and no quota needed, so a YouTube row never needs generic artwork.
# hqdefault (480x360) exists for every video; maxresdefault often 404s.
YT_HOST = 'https://i.ytimg.com/vi/'
YT_ID_PATTERNS = (
    re.compile(r'youtube\.com/watch\?[^\s]*v=([A-Za-z0-9_-]{6,})'),
    re.compile(r'youtu\.be/([A-Za-z0-9_-]{6,})'),
    re.compile(r'youtube\.com/(?:embed|shorts|live)/([A-Za-z0-9_-]{6,})'),
)


def youtube_thumbnail(url):
    """The video's own thumbnail for a YouTube link ('' if it is not one)."""
    value = (url or '').strip()
    for pattern in YT_ID_PATTERNS:
        match = pattern.search(value)
        if match:
            return f'{YT_HOST}{match.group(1)}/hqdefault.jpg'
    return ''


def is_stock_art(value):
    """True for the CDN photos from ``CATEGORY_PHOTOS`` we generated ourselves."""
    value = (value or '').strip()
    return value.startswith((UNS, PEX))


def _hash(key):
    """Tiny stable hash — the same key always maps to the same photo."""
    if isinstance(key, bool):
        key = int(key)
    if isinstance(key, int):
        return abs(key)
    return sum((i + 1) * ord(ch) for i, ch in enumerate(str(key or '')))


def is_placeholder(value):
    """True for empty values and for the generated SVG data-URIs."""
    value = (value or '').strip()
    return not value or value.startswith('data:')


def resolve_thumbnail(thumbnail_url='', category='', key=0, title='', platform='', url=''):
    """Best image for a resource.

    Order: real YouTube frame → source thumbnail → topic-matched stock photo →
    SVG gradient. A YouTube link always wins over generic artwork (ours or a
    placeholder), because the video's own frame is the honest picture.
    """
    stored = (thumbnail_url or '').strip()
    frame = youtube_thumbnail(url)
    if frame and (is_placeholder(stored) or is_stock_art(stored)):
        return frame
    if not is_placeholder(stored):
        return stored
    if category in CATEGORY_PHOTOS or not category:
        return photo_thumbnail(category, key)
    return placeholder_thumbnail(title, platform, category)


def placeholder_thumbnail(title, platform='', category=''):
    c1, c2 = TOPIC_COLORS.get(category, DEFAULT_COLORS)
    words = [w for w in (title or 'Course').split() if w]
    initials = ''.join(w[0] for w in words[:2]).upper() or 'CS'
    label = html.escape((platform or 'CourseScout')[:44])
    safe_initials = html.escape(initials)

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="470" '
        'viewBox="0 0 800 470">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{c1}"/>'
        f'<stop offset="1" stop-color="{c2}"/>'
        '</linearGradient></defs>'
        f'<rect width="800" height="470" fill="url(#g)"/>'
        '<circle cx="660" cy="70" r="140" fill="#ffffff" opacity="0.08"/>'
        '<circle cx="110" cy="430" r="110" fill="#ffffff" opacity="0.07"/>'
        '<text x="400" y="245" font-family="Arial, Helvetica, sans-serif" '
        'font-size="130" font-weight="bold" fill="#ffffff" opacity="0.95" '
        f'text-anchor="middle">{safe_initials}</text>'
        '<text x="400" y="320" font-family="Arial, Helvetica, sans-serif" '
        'font-size="30" fill="#ffffff" opacity="0.75" '
        f'text-anchor="middle">{label}</text>'
        '</svg>'
    )
    b64 = base64.urlsafe_b64encode(svg.encode('utf-8')).decode('ascii')
    return f'data:image/svg+xml;base64,{b64}'
