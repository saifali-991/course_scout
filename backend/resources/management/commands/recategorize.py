"""Re-run the category classifier over rows that are already in MySQL.

The first Kaggle import happened before the classifier learned to tell
AI/ML apart from generic Python (and before out-of-scope subjects were
dropped), so some stored rows sit in a wrong category. This command fixes
them in place — no CSV re-download, no link re-checking.

Examples
--------
    python manage.py recategorize                    # report only
    python manage.py recategorize --apply            # write the fixes
    python manage.py recategorize --apply --drop-offtopic
                                                     # + delete music/fitness rows
    python manage.py recategorize --apply --source all
"""

from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from resources.categories import CATEGORY_SLUGS
from resources.classify import classify_from_description, subject_offtopic_from_description
from resources.models import Resource


class Command(BaseCommand):
    help = ('Re-apply resources/classify.py to stored rows and repair their '
            'categories (report-only unless --apply is passed).')

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='write the new categories (default: report only)')
        parser.add_argument('--source', default='csv',
                            help="rows to inspect: 'csv' (default), 'all', or any "
                                 'other stored source label')
        parser.add_argument('--drop-offtopic', action='store_true',
                            help='delete rows whose subject is out of scope for the '
                                 'six categories (e.g. Musical Instruments)')
        parser.add_argument('--batch-size', type=int, default=500)

    def handle(self, *args, **options):
        source = (options['source'] or '').strip().lower()
        qs = Resource.objects.all()
        if source and source != 'all':
            qs = qs.filter(source=source)
        rows = list(qs.only('id', 'title', 'description', 'category'))

        if not rows:
            self.stdout.write(self.style.WARNING(
                f'  no resources found for source={source!r} — nothing to do.'))
            return

        before = Counter(r.category for r in rows)
        changed, unmatched, doomed = [], 0, []

        for row in rows:
            if options['drop_offtopic'] and subject_offtopic_from_description(row.description):
                doomed.append(row.id)
                continue
            slug = classify_from_description(row.description, row.title)
            if not slug:
                unmatched += 1
                continue
            if slug in CATEGORY_SLUGS and slug != row.category:
                row.category = slug
                changed.append(row)

        doomed_ids = set(doomed)
        after = Counter(r.category for r in rows if r.id not in doomed_ids)

        self.stdout.write(f'  inspected {len(rows)} row(s) [source={source}]')
        self.stdout.write(f'  category changes: {len(changed)}')
        if unmatched:
            self.stdout.write(self.style.WARNING(
                f'  {unmatched} row(s) could not be mapped to a category '
                '(kept as-is; use --drop-offtopic to delete out-of-scope ones)'))
        if options['drop_offtopic']:
            self.stdout.write(f'  out-of-scope rows to delete: {len(doomed)}')

        if not options['apply']:
            self.stdout.write(self.style.WARNING(
                '  report only — re-run with --apply to write these changes.'))
        else:
            with transaction.atomic():
                if changed:
                    Resource.objects.bulk_update(
                        changed, ['category'], batch_size=options['batch_size'])
                if doomed:
                    Resource.objects.filter(id__in=doomed).delete()
            self.stdout.write(self.style.SUCCESS(
                f'  applied: {len(changed)} updated, {len(doomed)} deleted'))

        self.stdout.write('  category distribution:')
        for slug in CATEGORY_SLUGS:
            old, new = before.get(slug, 0), after.get(slug, 0)
            arrow = '' if old == new else f'  ({old} -> {new})'
            self.stdout.write(f'    {slug:<22} {new}{arrow}')
        self.stdout.write(f'    {"TOTAL":<22} {sum(after.values())}')
