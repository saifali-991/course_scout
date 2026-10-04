"""Keep the catalog to the two languages the site offers: English & Hindi.

    python manage.py apply_languages            # report only (default)
    python manage.py apply_languages --apply    # fix + hide the rest

Everything the site displays comes from ``resources/langs.py``: two codes, with
Hindi recognised either from Devanagari script, from YouTube's own
``localizationLanguages`` metadata, or from channels that publish in Hindi
(CodeWithHarry, Apna College, …) even when the video title is in English.

This command re-detects the language for every row (cheap, no network) and —
with ``--apply`` — deactivates anything that is neither of the two, so a stray
Spanish or German course disappears from search and counts instead of showing
up with a language the user never asked for.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count

from resources.langs import SUPPORTED_CODES, detect_language
from resources.models import Resource


class Command(BaseCommand):
    help = 'Tag every course en/hi and hide resources in any other language.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='write the new language and deactivate off-language rows')

    def handle(self, *args, **opts):
        apply = opts['apply']
        rows = Resource.objects.values_list('id', 'title', 'provider', 'language',
                                            'is_active')
        changed, hidden, counts = 0, 0, {}
        updates, hide_ids = [], []
        for pk, title, provider, current, active in rows.iterator(chunk_size=2000):
            lang = detect_language(title, provider, channel=provider)
            counts[lang] = counts.get(lang, 0) + 1
            if lang != current:
                changed += 1
                if apply:
                    updates.append(Resource(id=pk, language=lang))
            if lang not in SUPPORTED_CODES and active:
                hidden += 1
                if apply:
                    hide_ids.append(pk)

        self.stdout.write(self.style.MIGRATE_HEADING('— languages —'))
        for code in sorted(counts, key=lambda c: (-counts[c], c)):
            label = code if code in SUPPORTED_CODES else f'{code} (unsupported -> hidden)'
            self.stdout.write(f'  {label:<28} {counts[code]}')
        self.stdout.write(f'  language re-tagged: {changed} · to hide: {hidden}')

        if not apply:
            self.stdout.write(self.style.WARNING('DRY RUN — re-run with --apply to write.'))
            return
        if updates:
            Resource.objects.bulk_update(updates, ['language'], batch_size=500)
        if hide_ids:
            Resource.objects.filter(id__in=hide_ids).update(is_active=False)
        remaining = (Resource.objects.filter(is_active=True)
                     .values('language').annotate(n=Count('id')).order_by('-n'))
        self.stdout.write(self.style.SUCCESS(
            f'  updated {len(updates)} row(s), hid {len(hide_ids)} row(s).'))
        for row in remaining:
            self.stdout.write(f'  live: {row["language"] or "(unset)":<6} {row["n"]}')
