"""python manage.py attach_thumbnails — give every resource a real image.

The Kaggle CSV import has no image column, so those rows only carry an
auto-generated SVG gradient data-URI. This command swaps those (and any empty
value) for a topic-matched stock photo URL from ``resources.thumbnails`` so the
database itself is self-describing: admin, exports and API dumps all show a
picture. Picks are deterministic per resource id, so nothing reshuffles.

YouTube rows get the video's own frame from ``i.ytimg.com`` (public, no API key)
instead of generic artwork.

The API/serializer already falls back to the same images at read time, so this
command is a data-tidying step, not a prerequisite.

Usage:
  python manage.py attach_thumbnails                # report only (dry run)
  python manage.py attach_thumbnails --apply        # write the URLs
  python manage.py attach_thumbnails --apply --category python
  python manage.py attach_thumbnails --apply --refill   # also replace real photos
"""

from django.core.management.base import BaseCommand

from resources.categories import CATEGORY_SLUGS
from resources.models import Resource
from resources.thumbnails import (
    CATEGORY_PHOTOS, is_placeholder, is_stock_art, resolve_thumbnail,
)

BATCH = 500


class Command(BaseCommand):
    help = 'Store a topic-matched photo URL for resources without a real image.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Write the changes (default is a dry-run report).')
        parser.add_argument('--refill', action='store_true',
                            help='Also replace existing http(s) thumbnails.')
        parser.add_argument('--category', choices=CATEGORY_SLUGS,
                            help='Only touch one category.')

    def handle(self, *args, **opts):
        apply_changes = opts['apply']
        refill = opts['refill']
        category = opts.get('category')

        qs = Resource.objects.all()
        if category:
            qs = qs.filter(category=category)

        total = qs.count()
        self.updated = 0
        self.photos = 0
        kept = 0
        batch = []

        for res in qs.only('id', 'title', 'url', 'category', 'thumbnail_url',
                           'provider', 'is_active').iterator(chunk_size=BATCH):
            target = resolve_thumbnail(res.thumbnail_url, res.category, res.pk,
                                       res.title, res.provider or 'CourseScout',
                                       url=res.url)
            stored = res.thumbnail_url or ''
            if target == stored:
                kept += 1
                continue
            # Keep an image the source provided, unless --refill was requested;
            # placeholders and our own stock art are always fair game to replace.
            if not (is_placeholder(stored) or is_stock_art(stored)) and not refill:
                kept += 1
                continue
            res.thumbnail_url = target
            batch.append(res)
            if len(batch) >= BATCH:
                self._flush(batch, apply_changes)
                batch = []

        self._flush(batch, apply_changes)

        missing = [slug for slug in CATEGORY_SLUGS if slug not in CATEGORY_PHOTOS]
        self.stdout.write(
            f'total={total} kept={kept} updated={self.updated} '
            f'svg_fallback={self.updated - self.photos}')
        if missing:
            self.stdout.write(self.style.WARNING(
                f'categories without a photo pool (SVG fallback used): {missing}'))
        self.stdout.write(self.style.SUCCESS('done — changes written')
                          if apply_changes else
                          self.style.WARNING('dry run — nothing written (use --apply)'))

    # -- helpers ---------------------------------------------------------

    def _flush(self, rows, apply_changes):
        if not rows:
            return
        self.updated += len(rows)
        self.photos += sum(1 for r in rows if r.thumbnail_url.startswith('http'))
        if apply_changes:
            Resource.objects.bulk_update(rows, ['thumbnail_url'])
