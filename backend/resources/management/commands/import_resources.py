"""python manage.py import_resources — aggregate learning resources into MySQL.

Sources (in order):
  curated  data/curated*.json          bundled, hand-verified free courses
  csv      data/udemy_courses.csv      Kaggle "Udemy Courses" dataset (if present)
           data/coursera_courses.csv   Kaggle "Coursera Courses" dataset (if present)
  manual   data/manual_seed.json       user-filled Unacademy / Physics Wallah
  youtube  YouTube Data API v3         needs YOUTUBE_API_KEY in backend/.env
  creators  hand-picked channels       resources/creators.py (CodeWithHarry,
                                         Apna College, codebasics, Gohar …) —
                                         run with --only creators, needs the key

Guarantees:
  * dedupe by normalized link (DB unique url + in-run cache)
  * invalid URLs / empty titles are skipped
  * missing thumbnails resolve to a topic-matched stock photo URL
    (resources.thumbnails.CATEGORY_PHOTOS), else an SVG gradient data-URI
  * with --verify on (default), 404/410/unreachable links are skipped
  * every row is tagged 'en' or 'hi' (resources/langs.py): the site only offers
    English + Hindi, apply_languages hides anything else
  * the keyword search is pinned to regionCode=IN and run once per language
    (relevanceLanguage=en, then =hi) so no Japanese / Chinese / Korean result
    can slip in; leftovers from older runs are removed with
    `manage.py clean_invalid_titles --apply`

Usage:
  python manage.py import_resources                # all sources
  python manage.py import_resources --only csv     # curated|csv|manual|youtube|creators
  python manage.py import_resources --skip-verify  # faster, no HTTP checks
  python manage.py import_resources --dry-run      # report only, no writes
  python manage.py import_resources --only creators --videos-per-creator 30
  python manage.py import_resources --only creators --creators "CodeWithHarry,codebasics"
"""

import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from django.core.management.base import BaseCommand

from resources.categories import CATEGORY_SLUGS
from resources.classify import (best_slug, classify_csv_title, detect_category,
                                subject_is_offtopic)
from resources.creators import CREATOR_SOURCES
from resources.langs import detect_language
from resources.models import Resource
from resources.thumbnails import resolve_thumbnail

DATA_DIR = Path(__file__).resolve().parents[3] / 'data'
UA = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CourseScout/1.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

TRACKING_PARAMS = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                   'fbclid', 'gclid', 'ref', 'couponcode', 'coupon_code'}


def normalize_url(url):
    """Stable dedupe key: lowercase scheme/host, drop tracking params & slash."""
    try:
        p = urlparse(url.strip())
    except ValueError:
        return ''
    if p.scheme not in ('http', 'https') or not p.netloc:
        return ''
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if k.lower() not in TRACKING_PARAMS]
    path = p.path or '/'
    if path != '/':
        path = path.rstrip('/')
    return urlunparse((p.scheme.lower(), p.netloc.lower(), path, '', urlencode(query), ''))


def valid_url(url):
    p = urlparse(url.strip())
    if p.scheme not in ('http', 'https') or not p.netloc:
        return False
    return bool(re.match(r'^[\w.-]+\.[a-z]{2,}$', p.netloc.split(':')[0], re.I))


# ==== CHUNK1B ====


def norm_level(text):
    t = (text or '').lower()
    if not t:
        return ''
    if 'begin' in t or 'entry' in t or 'no prior' in t:
        return Resource.Level.BEGINNER
    if 'inter' in t or 'middle' in t:
        return Resource.Level.INTERMEDIATE
    if 'advan' in t or 'expert' in t or 'specialist' in t:
        return Resource.Level.ADVANCED
    if 'all' in t:
        return Resource.Level.ALL
    return ''


def clamp_rating(value):
    try:
        r = float(value)
    except (TypeError, ValueError):
        return None
    if r <= 0 or r > 5:
        return None
    return round(min(r, 5.0), 1)


def parse_duration_hours(text):
    """'3.5 total hours'→3.5, '12 weeks'→60, '2 months'→60, '45 min'→0.75."""
    if not text:
        return None
    t = str(text).lower()
    m = re.search(r'(\d+(?:\.\d+)?)\s*(hour|hr|week|month|day|minute|min)', t)
    if not m:
        return None
    n, unit = float(m.group(1)), m.group(2)
    if 'hour' in unit or unit == 'hr':
        return n
    if 'week' in unit:
        return n * 5
    if 'month' in unit:
        return n * 30
    if 'day' in unit:
        return n * 8
    return n / 60.0


# Category classification lives in resources/classify.py (shared with the
# `recategorize` command). It is imported at the top of this module.


# ==== CHUNK1C ====


def entry_to_resource(entry, default_provider='', default_platform='other',
                      default_category='web-development', source=''):
    """Validate a dict entry → (kwargs, reason). Returns (None, reason) if skipped."""
    title = str(entry.get('title') or '').strip()[:300]
    url = str(entry.get('url') or '').strip()
    if not title:
        return None, 'no title'
    if not valid_url(url):
        return None, 'invalid url'
    category = str(entry.get('category') or default_category).strip()
    if category not in CATEGORY_SLUGS:
        category = detect_category(title)
    is_free = entry.get('is_free')
    if is_free is None:
        is_free = True
    try:
        price = round(float(entry['price']), 2) if entry.get('price') not in (None, '') else None
    except (TypeError, ValueError):
        price = None
    platform = str(entry.get('platform') or default_platform).strip()
    provider = str(entry.get('provider') or default_provider).strip()
    resource_type = str(entry.get('resource_type') or 'course').strip()
    if resource_type not in Resource.ResourceType.values:
        resource_type = Resource.ResourceType.COURSE
    duration_text = str(entry.get('duration_text') or '').strip()[:100]
    kwargs = dict(
        title=title, url=url,
        thumbnail_url=str(entry.get('thumbnail_url') or '').strip(),
        provider=provider,
        platform=platform if platform in Resource.Platform.values else Resource.Platform.OTHER,
        category=category, resource_type=resource_type,
        is_free=bool(is_free), price=price, rating=clamp_rating(entry.get('rating')),
        level=norm_level(entry.get('level')), duration_text=duration_text,
        duration_hours=parse_duration_hours(duration_text),
        description=str(entry.get('description') or '').strip()[:2000],
        # English / Hindi only — see resources/langs.py
        language=str(entry.get('language') or '').strip()[:8]
        or detect_language(title, provider, channel=provider),
        source=source,
    )
    return kwargs, ''


def load_json_entries(path):
    try:
        with open(path, encoding='utf-8') as f:
            payload = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        raise CommandError(f'{path.name} is not valid JSON: {exc}')
    entries = payload.get('entries', []) if isinstance(payload, dict) else payload
    return [e for e in entries if isinstance(e, dict)]


def load_udemy_csv(path):
    """Kaggle 'Udemy Courses' — flexible column mapping.

    Rows whose subject is out of scope (e.g. Musical Instruments) or that
    cannot be mapped to one of our six categories are dropped instead of
    being lumped into a wrong category.
    """
    rows = []
    skipped_offtopic = 0
    with open(path, newline='', encoding='utf-8-sig') as f:
        for raw in csv.DictReader(f):
            row = {(k or '').strip().lower(): (v or '').strip() for k, v in raw.items()}
            title = row.get('course_title') or row.get('title')
            url = row.get('url') or row.get('course_url')
            if not title or not url:
                continue
            subject = row.get('subject', '')
            category = classify_csv_title(title, subject)
            if not category:
                skipped_offtopic += 1
                continue
            price_raw = row.get('price', '')
            try:
                price = float(re.sub(r'[^0-9.]', '', price_raw) or 0)
            except ValueError:
                price = 0
            is_paid = row.get('is_paid', '').lower() in ('true', '1', 'paid')
            rows.append(dict(
                title=title, url=url, provider='Udemy', platform='other',
                category=category,
                is_free=(not is_paid) or price == 0,
                price=price or None, rating=None,
                level=row.get('level', ''), duration_text=row.get('content_duration', ''),
                resource_type='course', description=f"Udemy course — {row.get('subject', 'General')} subject area.",
            ))
    load_udemy_csv.last_skipped = skipped_offtopic
    return rows


def load_coursera_csv(path):
    """Kaggle 'Coursera Courses' — flexible column mapping."""
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for raw in csv.DictReader(f):
            row = {(k or '').strip().lower(): (v or '').strip() for k, v in raw.items()}
            title = row.get('course_title') or row.get('title') or row.get('name')
            url = row.get('course_url') or row.get('url') or row.get('link')
            if not title or not url:
                continue
            org = row.get('course_organization') or row.get('organization') or row.get('partner')
            rating = row.get('course_rating') or row.get('rating')
            enrolled = row.get('course_students_enrolled', '')
            m = re.search(r'([\d.]+)\s*([kKmM]?)', enrolled)
            if m:
                n = float(m.group(1))
                enrolled = int(n * (1000 if m.group(2) in 'kK' else 1000000 if m.group(2) in 'mM' else 1))
            else:
                enrolled = 0
            rows.append(dict(
                title=title, url=url, provider=org or 'Coursera', platform='coursera',
                category=detect_category(title),
                is_free=True,  # Coursera pages are free to audit
                rating=clamp_rating(rating) if rating else None,
                level=row.get('course_difficulty') or row.get('difficulty_level') or '',
                resource_type='course',
                description=f"Offered by {org or 'Coursera'}"
                + (f" — {enrolled:,}+ learners enrolled." if enrolled else ""),
            ))
    return rows


# ==== CHUNK2_YOUTUBE ====

import os  # noqa: E402  (module-level, used by the YouTube loader)

YOUTUBE_CATEGORY_QUERIES = {
    'python': ['python full course for beginners', 'python tutorial for beginners project'],
    'web-development': ['full stack web development course', 'html css javascript full course'],
    'data-analytics': ['data analysis full course', 'sql full course for beginners'],
    'ai-machine-learning': ['machine learning full course', 'deep learning full course'],
    'ui-ux-design': ['ui ux design course figma', 'ux design course'],
    'digital-marketing': ['digital marketing full course', 'seo full course'],
}

# Without these two the search returns whatever YouTube ranks globally, which is
# how Japanese / Chinese / Korean tutorials ended up in the catalog. Every query
# therefore runs twice — once biased to English, once to Hindi — inside India.
# Costs 100 quota units per search: 12 queries × 2 languages = 2,400 units.
YOUTUBE_SEARCH_REGION = 'IN'
YOUTUBE_SEARCH_LANGUAGES = ('en', 'hi')

ISO8601_RE = re.compile(
    r'^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$'
)


def iso8601_to_hours(text):
    m = ISO8601_RE.match(text or '')
    if not m:
        return 0.0
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 24 + h + mi / 60 + s / 3600


def humanize_hours(hours):
    if hours >= 1:
        whole = int(hours)
        mins = round((hours - whole) * 60)
        return f'{whole} hr {mins} min' if mins else f'{whole} hours'
    return f'{round(hours * 60)} min'


def fetch_youtube_entries(api_key, log):
    """Search + details via YouTube Data API v3 → list[dict] entries.

    Each query is issued once per supported language (``en`` then ``hi``) with
    ``regionCode=IN``, so the crawler cannot pull a Japanese or Spanish result
    just because it ranks well worldwide.
    """
    found = {}
    for cat, queries in YOUTUBE_CATEGORY_QUERIES.items():
        for q in queries:
            for lang in YOUTUBE_SEARCH_LANGUAGES:
                try:
                    r = requests.get(
                        'https://www.googleapis.com/youtube/v3/search',
                        params=dict(key=api_key, part='snippet', type='video',
                                    maxResults=12, q=q, relevanceLanguage=lang,
                                    regionCode=YOUTUBE_SEARCH_REGION),
                        timeout=20,
                    )
                    r.raise_for_status()
                    items = r.json().get('items', [])
                except (requests.RequestException, ValueError) as exc:
                    log(f'  ! search "{q}" ({lang}) failed: {exc}')
                    continue
                for item in items:
                    vid = (item.get('id') or {}).get('videoId')
                    if vid and vid not in found:
                        found[vid] = cat
    log(f'  ~ {len(found)} unique candidate videos found '
        f'(region={YOUTUBE_SEARCH_REGION}, languages={"+".join(YOUTUBE_SEARCH_LANGUAGES)})')

    entries = []
    ids = list(found)
    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        try:
            r = requests.get(
                'https://www.googleapis.com/youtube/v3/videos',
                params=dict(key=api_key, part='snippet,contentDetails,statistics',
                            id=','.join(batch)),
                timeout=20,
            )
            r.raise_for_status()
        except (requests.RequestException, ValueError) as exc:
            log(f'  ! videos lookup failed: {exc}')
            continue
        for item in r.json().get('items', []):
            vid = item.get('id', '')
            sn = item.get('snippet', {})
            st = item.get('statistics', {})
            hours = iso8601_to_hours(item.get('contentDetails', {}).get('duration'))
            try:
                views = int(st.get('viewCount') or 0)
                likes = int(st.get('likeCount') or 0)
            except ValueError:
                views = likes = 0
            if hours < 0.6 or views < 5000:
                continue  # skip shorts/clips and low-reach videos
            rating = round(4 + min(0.9, (likes / views) * 12), 1) if views else None
            thumbs = sn.get('thumbnails') or {}
            thumb = (thumbs.get('high') or thumbs.get('medium')
                     or thumbs.get('default') or {}).get('url', '')
            entries.append(dict(
                title=(sn.get('title') or '').strip(),
                url=f'https://www.youtube.com/watch?v={vid}',
                provider=(sn.get('channelTitle') or 'YouTube').strip(),
                platform='youtube', category=found[vid], is_free=True,
                rating=rating, duration_text=humanize_hours(hours),
                resource_type='youtube',
                description=(sn.get('description') or '').strip()[:800],
                thumbnail_url=thumb,
            ))
    return entries


# ==== CHUNK3_COMMAND ====


def check_one_url(url, attempts=2):
    """True if link is alive.

    404/410 → dead (skip). 403/405/429 → bot-block, not a broken link → keep.
    5xx → transient hiccup → keep. Connection/timeout/SSL failures are retried
    with a short backoff, and a failed HEAD is always confirmed with a
    lightweight GET: plenty of hosts (or middleboxes) reject HEAD outright and
    those links must not be thrown away as broken.
    """
    head_status = None
    for attempt in range(attempts):
        try:
            head_status = requests.head(url, timeout=8, allow_redirects=True,
                                        headers=UA).status_code
            break
        except requests.RequestException:
            if attempt == attempts - 1:
                break
            time.sleep(0.4 * (attempt + 1))

    if head_status in (404, 410):
        return False
    if head_status is not None and head_status < 400:
        return True

    for attempt in range(attempts):
        try:
            g = requests.get(url, timeout=12, allow_redirects=True,
                             headers=UA, stream=True)
            status = g.status_code
            g.close()
        except requests.RequestException:
            if attempt == attempts - 1:
                # HEAD reached a server that never answered the GET → keep it.
                return head_status is not None
            time.sleep(0.4 * (attempt + 1))
            continue
        if status in (404, 410):
            return False
        if status in (403, 405, 429) or status >= 500:
            return True
        return status < 400
    return False


def verify_entries(entries, log, verbose=False):
    """Drop entries whose page is unreachable (parallel HEAD/GET checks).

    Concurrency is deliberately modest (10 workers): hammering hosts with 24
    simultaneous HEADs made good links time out and get dropped as "broken".
    With ``verbose`` the dropped URLs are listed instead of just counted.
    """
    t0 = time.time()
    keep, dropped = [], []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(check_one_url, e['url']): e for e in entries}
        for fut in as_completed(list(futures)):
            if fut.result():
                keep.append(futures[fut])
            else:
                dropped.append(futures[fut])
    log(f'  ~ link check: {len(keep)} alive · {len(dropped)} broken dropped '
        f'({time.time() - t0:.1f}s)')
    if verbose:
        for entry in dropped:
            log(f'      dropped: {entry["url"]}')
    return keep


class Command(BaseCommand):
    help = ('Aggregate learning resources from curated JSON, Kaggle CSVs, '
            'manual seed, and the YouTube Data API into MySQL (dedupe by link).')

    def add_arguments(self, parser):
        parser.add_argument('--only', choices=['curated', 'csv', 'manual', 'youtube',
                                               'creators'])
        parser.add_argument('--skip-verify', action='store_true',
                            help='do not HEAD-check links (faster)')
        parser.add_argument('--dry-run', action='store_true',
                            help='report what would be imported, write nothing')
        parser.add_argument('--verbose', action='store_true',
                            help='list every URL dropped by the link checker')
        # ---- hand-picked channels (--only creators) ----
        parser.add_argument('--creators', default='',
                            help='comma list of channel names to crawl; default = every '
                                 'top creator in resources/creators.py')
        parser.add_argument('--videos-per-creator', type=int, default=20,
                            help='latest uploads to import per channel (default 20)')
        parser.add_argument('--playlists-per-creator', type=int, default=4,
                            help='channel playlists to import per channel (default 4)')
        parser.add_argument('--sleep', type=float, default=0.0,
                            help='seconds to pause between channels')

    # ---- source loaders -------------------------------------------------

    def _curated_entries(self):
        entries = []
        for f in sorted(DATA_DIR.glob('curated*.json')):
            entries.extend(load_json_entries(f))
        return entries

    def _csv_entries(self):
        entries = []
        for name, loader in (('udemy_courses.csv', load_udemy_csv),
                             ('coursera_courses.csv', load_coursera_csv)):
            path = DATA_DIR / name
            if path.exists():
                entries.extend(loader(path))
                skipped = getattr(loader, 'last_skipped', 0)
                if skipped:
                    self.stdout.write(
                        f'  (csv) {name}: {skipped} off-topic row(s) skipped '
                        '(not one of our six categories).')
            else:
                self.stdout.write(self.style.WARNING(
                    f'  (csv) {name} not found in backend/data/ — skipped. '
                    'Download it from Kaggle to add thousands of courses.'))
        return entries

    def _manual_entries(self):
        entries = load_json_entries(DATA_DIR / 'manual_seed.json')
        kept = [e for e in entries
                if not str(e.get('title', '')).strip().upper().startswith('EXAMPLE')]
        if len(kept) != len(entries):
            self.stdout.write(
                f'  (manual) {len(entries) - len(kept)} placeholder EXAMPLE row(s) '
                'ignored — replace them with real Unacademy / PW courses first.')
        return kept

    def _youtube_entries(self):
        api_key = os.environ.get('YOUTUBE_API_KEY', '').strip()
        if not api_key:
            self.stdout.write(self.style.WARNING(
                '  (youtube) YOUTUBE_API_KEY empty in backend/.env — skipped.'))
            return []
        return fetch_youtube_entries(api_key, self.stdout.write)

    def _creator_entries(self):
        """Uploads + playlists of the starred channels (Top creators list)."""
        api_key = os.environ.get('YOUTUBE_API_KEY', '').strip()
        if not api_key:
            self.stdout.write(self.style.WARNING(
                '  (creators) YOUTUBE_API_KEY empty in backend/.env — skipped.'))
            return []
        opts = getattr(self, '_opts', {})
        only = [c for c in str(opts.get('creators') or '').split(',') if c.strip()]
        return crawl_top_creators(
            api_key, self.stdout.write,
            videos=opts.get('videos_per_creator', 20),
            playlists=opts.get('playlists_per_creator', 4),
            only=only, sleep=opts.get('sleep', 0.0))

# ==== CHUNK4_HANDLE ====

    # ---- pipeline -------------------------------------------------------

    def _filter_new(self, entries, source, existing_keys, seen):
        fresh, invalid, dupes = [], 0, 0
        for entry in entries:
            kwargs, reason = entry_to_resource(entry, source=source)
            if kwargs is None:
                invalid += 1
                continue
            key = normalize_url(kwargs['url'])
            if not key or key in seen or key in existing_keys:
                dupes += 1
                continue
            seen.add(key)
            if not kwargs['thumbnail_url']:
                kwargs['thumbnail_url'] = resolve_thumbnail(
                    '', kwargs['category'], kwargs['url'],
                    kwargs['title'], kwargs['provider'] or 'CourseScout',
                    url=kwargs['url'])
            fresh.append(kwargs)
        self.stdout.write(
            f'  {source}: {len(fresh)} new · {dupes} duplicates · {invalid} invalid')
        return fresh

    def handle(self, *args, **opts):
        only = opts.get('only')
        self._opts = opts
        verify = not opts['skip_verify']
        dry = opts['dry_run']

        existing_keys = {normalize_url(u) for u in
                         Resource.objects.values_list('url', flat=True)}
        seen = set()
        loaders = {
            'curated': self._curated_entries,
            'csv': self._csv_entries,
            'manual': self._manual_entries,
            'youtube': self._youtube_entries,
            # hand-picked channels — run on purpose: --only creators
            'creators': self._creator_entries,
        }
        source_names = [only] if only else ['curated', 'csv', 'manual', 'youtube']

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'CourseScout — importing resources (verify={verify}, dry-run={dry})'))
        per_source = {}
        for name in source_names:
            self.stdout.write(self.style.HTTP_INFO(f'[source: {name}]'))
            raw = loaders[name]()
            fresh = self._filter_new(raw, name, existing_keys, seen)
            if verify and fresh:
                fresh = verify_entries(fresh, self.stdout.write,
                                       verbose=opts.get('verbose', False))
            if fresh and not dry:
                objs = [Resource(**kw) for kw in fresh]
                Resource.objects.bulk_create(objs, batch_size=500, ignore_conflicts=True)
            per_source[name] = len(fresh)

        self._print_summary(per_source, dry)

    def _print_summary(self, per_source, dry):
        from django.db.models import Count

        self.stdout.write(self.style.MIGRATE_HEADING('— summary —'))
        for name, n in per_source.items():
            self.stdout.write(f'  {name:<9} {n} imported')
        if dry:
            self.stdout.write(self.style.WARNING('DRY RUN — nothing written to DB.'))
        total = Resource.objects.count()
        self.stdout.write(f'  TOTAL in DB: {total}')
        for row in (Resource.objects.values('category').order_by('category')
                    .annotate(n=Count('id'))):
            self.stdout.write(f'    {row["category"]:<22} {row["n"]}')
        if total < 300 and not dry:
            self.stdout.write(self.style.WARNING(
                '  Target is 300+. Add data/udemy_courses.csv & coursera_courses.csv '
                '(from Kaggle) and/or YOUTUBE_API_KEY in backend/.env, then re-run.'))


# ---------------------------------------------------------------------------
# Hand-picked channels (resources/creators.py) — the YouTube tab's Top creators.
#
# One channel costs ~6 API units (channel lookup, uploads, durations, playlist
# list, one item per playlist), so crawling every starred channel is well under
# the 10,000 units/day quota. Uploads already carry the real title, thumbnail
# and duration — no guesswork like the keyword search needs.
# ---------------------------------------------------------------------------

YT_API = 'https://www.googleapis.com/youtube/v3'
TITLE_NOISE = re.compile(r'^\s*(?:lesson\s*\d*\s*[:\-–|]\s*|\d+\s*[).:-]\s+)', re.I)
SKIP_PLAYLIST_PREFIXES = ('likes', 'favorites', 'playall', 'post-playback', 'popular uploads')


def yt_get(endpoint, params, timeout=25):
    """One YouTube Data API v3 GET. Every endpoint used here costs 1 unit."""
    resp = requests.get(f'{YT_API}/{endpoint}', params=params, timeout=timeout)
    if resp.status_code == 429:
        raise CommandError('YouTube API returned 429 (rate limit / quota). Wait ~60s '
                           'and re-run, or lower --videos-per-creator.')
    resp.raise_for_status()
    return resp.json()


def resolve_channel(name, key):
    """'CodeWithHarry' / '@codebasics' / 'UC…' → channel id ('' when unknown)."""
    if re.fullmatch(r'UC[\w-]{22}', name or ''):
        return name
    handle = (name or '').lstrip('@').replace(' ', '')
    lookups = [
        ('channels', {'part': 'id', 'forHandle': handle}),
        ('channels', {'part': 'id', 'forUsername': handle.replace(' ', '')}),
        ('search', {'part': 'snippet', 'type': 'channel', 'q': name, 'maxResults': 1}),
    ]
    for endpoint, params in lookups:
        try:
            items = yt_get(endpoint, {**params, 'key': key}).get('items') or []
        except (requests.RequestException, ValueError):
            continue
        if not items:
            continue
        if endpoint == 'channels':
            return items[0].get('id') or ''
        return (items[0].get('snippet') or {}).get('channelId') or ''
    return ''


def uploads_playlist_id(channel_id, key):
    data = yt_get('channels', {'part': 'contentDetails', 'id': channel_id, 'key': key})
    items = data.get('items') or []
    if not items:
        return ''
    return ((items[0].get('contentDetails') or {}).get('relatedPlaylists') or {}).get('uploads', '')


def playlist_items(playlist_id, key, limit=50):
    """Playlist items, newest first for uploads, page by page up to ``limit``."""
    out, token = [], ''
    while len(out) < limit:
        params = {'part': 'snippet,contentDetails', 'playlistId': playlist_id,
                  'maxResults': min(50, limit - len(out)), 'key': key}
        if token:
            params['pageToken'] = token
        data = yt_get('playlistItems', params)
        out.extend(data.get('items') or [])
        token = data.get('nextPageToken') or ''
        if not token:
            break
    return out


def channel_playlists(channel_id, key, limit=5):
    """The channel's own public playlists, skipping likes/favourites shelves."""
    data = yt_get('playlists', {'part': 'snippet,status', 'channelId': channel_id,
                                'maxResults': 50, 'key': key})
    out = []
    for item in data.get('items') or []:
        snippet = item.get('snippet') or {}
        title = clean_title(snippet.get('title') or '')
        if (item.get('status') or {}).get('privacyStatus') != 'public':
            continue
        if not title or title.lower().startswith(SKIP_PLAYLIST_PREFIXES):
            continue
        out.append({'id': item['id'], 'title': title,
                    'count': int(snippet.get('itemCount') or 0)})
        if len(out) >= limit:
            break
    return out


def item_video_id(item):
    return ((item.get('contentDetails') or {}).get('videoId')
            or ((item.get('snippet') or {}).get('resourceId') or {}).get('videoId') or '')


def durations_hours(video_ids, key):
    """videoId → length in hours (50 ids per request)."""
    hours = {}
    for i in range(0, len(video_ids), 50):
        data = yt_get('videos', {'part': 'contentDetails',
                                 'id': ','.join(video_ids[i:i + 50]), 'key': key})
        for item in data.get('items') or []:
            hours[item['id']] = iso_duration_hours(
                (item.get('contentDetails') or {}).get('duration'))
    return hours


def iso_duration_hours(iso):
    """'PT1H34M12S' → 1.57, 'PT45M' → 0.75, live/unknown → None."""
    m = re.match(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', iso or '')
    if not m:
        return None
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    total = h + mi / 60 + s / 3600
    return round(total, 2) if total > 0 else None


def fmt_duration(hours):
    if not hours:
        return ''
    if hours < 1:
        return f'{max(1, round(hours * 60))} minutes'
    return f'{round(hours, 1):g} total hours'


def clean_title(text):
    """'Lesson 12 - Loops' / '3. Intro' → 'Loops' / 'Intro' (single-spaced)."""
    return re.sub(r'\s+', ' ', TITLE_NOISE.sub('', text or '')).strip()


def plain(text, limit=900):
    return re.sub(r'\s+', ' ', text or '').strip()[:limit]


def level_from_title(title):
    t = (title or '').lower()
    if 'advanced' in t:
        return 'advanced'
    if 'intermediate' in t:
        return 'intermediate'
    if 'beginner' in t or 'basics' in t or 'crash course' in t or 'zero to' in t:
        return 'beginner'
    return ''

def video_entry(name, snippet, hours=None, category='', language=''):
    """playlistItem snippet → catalog entry for one upload (None when unusable)."""
    vid = (((snippet.get('resourceId') or {}).get('videoId'))
           or (snippet.get('videoId') or ''))
    title = clean_title(snippet.get('title') or '')
    if not vid or not title or title.lower() in ('private video', 'video unavailable'):
        return None
    thumb = ((snippet.get('thumbnails') or {}).get('high') or {}).get('url') \
        or f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'
    return {
        'title': title,
        'url': f'https://www.youtube.com/watch?v={vid}',
        'provider': name,
        'platform': 'youtube',
        'resource_type': 'youtube',
        # channel pin wins when the title carries no keyword ("Excel in 10 min")
        'category': category or best_slug(title) or detect_category(title),
        'is_free': True,
        'thumbnail_url': thumb,
        'description': plain(snippet.get('description') or ''),
        'duration_text': fmt_duration(hours),
        'level': level_from_title(title),
        # Hindi channels stay Hindi even when the title is in English
        'language': language or detect_language(title, name, channel=name),
    }


def playlist_entry(name, playlist, first_video_id='', category='', language=''):
    """Channel playlist → one entry linking to the playlist (stable dedupe key)."""
    title = clean_title(playlist.get('title') or '')
    if not title or not playlist.get('id'):
        return None
    count = playlist.get('count') or 0
    return {
        'title': title,
        'url': f"https://www.youtube.com/playlist?list={playlist['id']}",
        'provider': name,
        'platform': 'youtube',
        'resource_type': 'playlist',
        'category': category or best_slug(title) or detect_category(title),
        'is_free': True,
        'thumbnail_url': f'https://i.ytimg.com/vi/{first_video_id}/hqdefault.jpg'
        if first_video_id else '',
        'description': plain(f'{count} videos · {title} · complete playlist by {name}.'),
        'duration_text': f'{count} videos' if count else '',
        'level': level_from_title(title),
        'language': language or detect_language(title, name, channel=name),
    }


def crawl_top_creators(api_key, log, videos=20, playlists=4, only=None, sleep=0.0):
    """Uploads + playlists of every hand-picked channel as catalog entries."""
    entries = []
    specs = [s for s in CREATOR_SOURCES
             if not only or any(o.strip().lower() in s['name'].lower()
                                or o.strip().lstrip('@').lower() in s['handle'].lower()
                                for o in only if o.strip())]
    if not specs:
        log(f'  (creators) no channel matches {only!r} — nothing to do.')
        return entries
    for spec in specs:
        name, pinned, language = spec['name'], spec.get('category', ''), spec.get('language', '')
        channel = resolve_channel(spec.get('handle') or name, api_key)
        if not channel:
            log(f'  (creators) {name}: channel not found — skipped')
            continue
        try:
            uploads = uploads_playlist_id(channel, api_key)
            items = playlist_items(uploads, api_key, videos) if uploads else []
            ids = [i for i in (item_video_id(item) for item in items) if i]
            hours = durations_hours(ids, api_key)
            n_videos = 0
            for item in items:
                length = hours.get(item_video_id(item))
                if length is not None and length < 0.03:  # < ~2 min: Shorts / promos
                    continue
                entry = video_entry(name, item.get('snippet') or {}, length,
                                    category=pinned, language=language)
                if entry:
                    entries.append(entry)
                    n_videos += 1
            n_lists = 0
            for pl in channel_playlists(channel, api_key, playlists):
                head = playlist_items(pl['id'], api_key, 1)
                entry = playlist_entry(name, pl, item_video_id(head[0]) if head else '',
                                       category=pinned, language=language)
                if entry:
                    entries.append(entry)
                    n_lists += 1
        except requests.RequestException as exc:
            log(f'  (creators) {name}: API error {exc} — skipped')
            continue
        log(f'  (creators) {name}: {n_videos} uploads · {n_lists} playlists'
            + (f' · {language}' if language else ''))
        if sleep:
            time.sleep(sleep)
    return entries







