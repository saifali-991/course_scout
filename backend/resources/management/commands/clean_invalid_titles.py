"""python manage.py clean_invalid_titles — drop rows whose title is not English/Hindi.

The YouTube keyword crawler used to run without a region or a language, so MySQL
picked up tutorials titled in Japanese, Chinese, Korean, Thai, Arabic and
Russian. This command reads the **writing system** of every title with the stdlib
``unicodedata`` module (no network, no fuzzy guessing, no extra package) and
targets only the rows that cannot be English or Hindi:

    kept    Latin letters        →  English   "Django REST Framework tutorial"
    kept    Devanagari letters   →  Hindi     "हिनदी में पायथन सीखें"
    kept    both, plus digits, spaces, punctuation, emoji, '–', '©' …
    delete  any other script     →  CJK, Hiragana, Katakana, Hangul, Thai, Arabic,
                                    Cyrillic, Greek, Hebrew, Bengali, Tamil,
                                    Telugu, Malayalam, Gujarati, Gurmukhi, …

So Hindi titles are safe, mixed "English + देवनागरी" titles are safe, and a row is
only deleted because of what its title is *written in* — never because a
probability library felt like it.

Latin-script foreign titles ("Curso de Python", "Türkçe eğitim") are a different
problem and are *not* matched by the script rule; add ``--include-latin-foreign``
to drop those as well through the marker list ``resources/langs.py`` already
uses (the same logic ``apply_languages`` applies).

Usage:
    python manage.py clean_invalid_titles                          # report only
    python manage.py clean_invalid_titles --apply                  # delete
    python manage.py clean_invalid_titles --apply --include-latin-foreign
    python manage.py clean_invalid_titles --limit 0                # no samples

This is **not** a table wipe: everything with an English/Hindi title — curated
JSON, the Kaggle CSVs, the hand-picked channels — stays untouched.
"""
import sys
from collections import Counter

from django.core.management.base import BaseCommand

from resources.langs import SUPPORTED_CODES, detect_language, foreign_scripts
from resources.models import Resource

BATCH = 500


def _force_utf8():
    """Windows pipes default to cp1252 — printing '日本語' would crash the command."""
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError, OSError):  # pragma: no cover
        pass


class Command(BaseCommand):
    help = ('Delete resources whose title is written in a script that is neither '
            'Latin (English) nor Devanagari (Hindi).')

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='delete the matched rows (default only reports them)')
        parser.add_argument('--include-latin-foreign', action='store_true',
                            help='also delete Latin-script titles that resources/langs.py '
                                 'recognises as another language (Curso…, Türkçe…, …)')
        parser.add_argument('--limit', type=int, default=15,
                            help='how many sample titles to print (default 15, 0 = none)')

    # ---- matching ---------------------------------------------------------

    def _matches(self, title, provider, include_latin_foreign):
        """(reason, detail) for a title that must go, or ('', '') when it stays."""
        scripts = foreign_scripts(title)
        if scripts:
            return 'script', ', '.join(scripts)
        if include_latin_foreign:
            code = detect_language(title, provider, channel=provider)
            if code not in SUPPORTED_CODES:
                return 'marker', code
        return '', ''

    # ---- command ----------------------------------------------------------

    def handle(self, *args, **opts):
        _force_utf8()
        apply_, limit = opts['apply'], opts['limit']
        latin_foreign = opts['include_latin_foreign']

        total_before = Resource.objects.count()
        matched, by_reason, by_detail = [], Counter(), Counter()
        for pk, title, provider in Resource.objects.values_list(
                'id', 'title', 'provider').iterator(chunk_size=2000):
            reason, detail = self._matches(title, provider, latin_foreign)
            if not reason:
                continue
            matched.append(pk)
            by_reason[reason] += 1
            by_detail[f'{reason}:{detail}'] += 1

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'— title audit ({total_before} rows scanned) —'))
        if not matched:
            self.stdout.write(self.style.SUCCESS(
                '  nothing to remove — every title is English (Latin script) or '
                'Hindi (Devanagari).'))
            return

        for detail in sorted(by_detail, key=lambda d: (-by_detail[d], d))[:12]:
            self.stdout.write(f'  {detail:<36} {by_detail[detail]}')
        if len(by_detail) > 12:
            self.stdout.write(f'  … and {len(by_detail) - 12} more script buckets')

        if limit:
            self.stdout.write(self.style.MIGRATE_HEADING('— samples to delete —'))
            for title, provider, platform in Resource.objects.filter(
                    id__in=matched[:limit]).values_list('title', 'provider', 'platform'):
                self.stdout.write(f'  [{platform:<9}] {title[:74]}  ·  {provider[:26]}')

        if not apply_:
            self.stdout.write(self.style.WARNING(
                f'  {len(matched)} of {total_before} row(s) would be deleted — '
                f'DRY RUN, re-run with --apply to write.'))
            return

        deleted, ids = 0, sorted(matched)
        for start in range(0, len(ids), BATCH):
            _, per_model = Resource.objects.filter(
                id__in=ids[start:start + BATCH]).delete()
            deleted += per_model.get('resources.Resource', 0)

        remaining = Resource.objects.count()
        live = Resource.objects.filter(is_active=True).count()
        left = sum(1 for t in Resource.objects.values_list('title', flat=True)
                   .iterator(chunk_size=2000) if foreign_scripts(t))
        self.stdout.write(self.style.SUCCESS(
            f'  deleted {deleted} row(s) · {remaining} left ({live} live, '
            f'{remaining - live} hidden)'))
        detail = f'{by_reason["script"]} matched by writing system'
        if by_reason['marker']:
            detail += f' · {by_reason["marker"]} by foreign-language marker'
        self.stdout.write(f'  removed: {detail}')
        write = self.style.SUCCESS if not left else self.style.WARNING
        self.stdout.write(write(
            f'  re-check: {left} remaining title(s) in a non English/Hindi script'))
