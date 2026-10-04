from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .categories import CATEGORIES, get_category
from .creators import is_top_creator, order_top_creators_first, top_creator_q
from .langs import SUPPORTED_LANGUAGES
from .models import Resource
from .pagination import ResourcesPagination
from .serializers import ResourceSerializer


class ResourceListView(generics.ListAPIView):
    """GET /api/resources/

    Query params:
      search        free-text across title / provider / description
      category      slug (see /api/categories/)
      platform      Resource.Platform value
      resource_type youtube | course | certificate | ...
      language      en | hi  (the catalog keeps English + Hindi courses only)
      provider      exact channel/provider name, e.g. CodeWithHarry
      top_creators  true — only channels flagged is_top by /api/creators/
      level         beginner | intermediate | advanced | all
      is_free       true | false   (Free/Paid toggle)
      ids           comma-separated ids (Saved page)
      ordering      -rating | rating | newest | title | top_creators
      page,page_size pagination (default 9 — three rows of the 3-up card grid, max 48)
    """

    serializer_class = ResourceSerializer
    pagination_class = ResourcesPagination

    ORDERING_MAP = {
        '-rating': ('-rating', '-created_at', 'id'),
        'rating': ('rating', 'id'),
        'newest': ('-created_at', 'id'),
        'title': ('title', 'id'),
        '-title': ('-title', 'id'),
    }

    def get_queryset(self):
        qs = Resource.objects.filter(is_active=True)
        p = self.request.query_params

        search = (p.get('search') or '').strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(provider__icontains=search)
                | Q(description__icontains=search)
            )

        category = (p.get('category') or '').strip()
        if category:
            qs = qs.filter(category=category)

        platform = (p.get('platform') or '').strip()
        if platform:
            qs = qs.filter(platform=platform)

        resource_type = (p.get('resource_type') or '').strip()
        if resource_type:
            qs = qs.filter(resource_type=resource_type)

        language = (p.get('language') or '').strip().lower()
        if language in [lang['code'] for lang in SUPPORTED_LANGUAGES]:
            qs = qs.filter(language=language)

        provider = (p.get('provider') or '').strip()
        if provider:
            qs = qs.filter(provider__iexact=provider)

        if (p.get('top_creators') or '').strip().lower() in ('true', '1', 'yes'):
            qs = qs.filter(top_creator_q())

        level = (p.get('level') or '').strip()
        if level:
            qs = qs.filter(level=level)

        is_free = (p.get('is_free') or '').strip().lower()
        if is_free in ('true', 'false'):
            qs = qs.filter(is_free=(is_free == 'true'))

        ids_param = (p.get('ids') or '').strip()
        if ids_param:
            id_list = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
            qs = qs.filter(id__in=id_list)

        ordering_param = (p.get('ordering') or '').strip()
        if ordering_param == 'top_creators':
            return order_top_creators_first(qs)
        ordering = self.ORDERING_MAP.get(ordering_param, self.ORDERING_MAP['-rating'])
        return qs.order_by(*ordering)


class ResourceDetailView(generics.RetrieveAPIView):
    queryset = Resource.objects.filter(is_active=True)
    serializer_class = ResourceSerializer


class CategoryListView(APIView):
    """GET /api/categories/ — metadata + live course counts per category."""

    def get(self, request):
        rows = (
            Resource.objects.filter(is_active=True)
            .values('category')
            .annotate(n=Count('id'))
        )
        counts = {r['category']: r['n'] for r in rows}
        data = [{**cat, 'course_count': counts.get(cat['slug'], 0)} for cat in CATEGORIES]
        return Response(data)


class StatsView(APIView):
    """GET /api/stats/ — hero badge numbers."""

    def get(self, request):
        base = Resource.objects.filter(is_active=True)
        agg = base.aggregate(
            total=Count('id'),
            free=Count('id', filter=Q(is_free=True)),
            paid=Count('id', filter=Q(is_free=False)),
        )
        platforms = base.values('platform').distinct().count()
        return Response({**agg, 'platforms': platforms})


class RecommendationListView(generics.ListAPIView):
    """GET /api/recommendations/?interests=python,ai-machine-learning

    Personal picks: top-rated resources in the user's interest categories.
    Logged-in users fall back to their UserProfile.interests automatically.
    """

    serializer_class = ResourceSerializer
    pagination_class = ResourcesPagination

    def get_queryset(self):
        interests_param = (self.request.query_params.get('interests') or '').strip()
        if interests_param:
            interests = [i.strip() for i in interests_param.split(',') if i.strip()]
        else:
            interests = []

        if not interests and self.request.user.is_authenticated:
            profile = getattr(self.request.user, 'profile', None)
            interests = [i for i in (profile.interests or []) if get_category(i)]

        valid = [i for i in interests if get_category(i)]
        qs = Resource.objects.filter(is_active=True)
        if valid:
            qs = qs.filter(category__in=valid)
        return qs.order_by('-rating', '-created_at', 'id')


class CreatorListView(APIView):
    """GET /api/creators/?platform=youtube — the channels to filter the grid by.

    Returns ``[{name, count, is_top, languages}, …]``: hand-picked top creators
    first, then everything else by number of live courses. That order is exactly
    what the YouTube tab's creator dropdown renders. ``&category=`` narrows the
    counts to one topic so the dropdown can match the visible grid.
    """

    def get(self, request):
        qs = Resource.objects.filter(is_active=True).exclude(provider='')
        platform = (request.query_params.get('platform') or '').strip()
        if platform:
            qs = qs.filter(platform=platform)
        category = (request.query_params.get('category') or '').strip()
        if category:
            qs = qs.filter(category=category)

        rows = qs.values('provider', 'language').annotate(n=Count('id')).order_by()
        by_name = {}
        for row in rows:
            entry = by_name.setdefault(row['provider'], {
                'name': row['provider'], 'count': 0, 'languages': [],
            })
            entry['count'] += row['n']
            if row['language'] not in entry['languages']:
                entry['languages'].append(row['language'])

        data = [{**item, 'is_top': is_top_creator(item['name'])}
                for item in by_name.values()]
        data.sort(key=lambda item: (not item['is_top'], -item['count'], item['name'].lower()))
        return Response(data)


class LanguageListView(APIView):
    """GET /api/languages/ — the languages the catalog keeps, with live counts.

    Anything that was not English or Hindi is deactivated by
    ``manage.py apply_languages``, so these two are also the whole catalog.
    """

    def get(self, request):
        rows = (Resource.objects.filter(is_active=True)
                .values('language').annotate(n=Count('id')))
        counts = {r['language']: r['n'] for r in rows}
        return Response([
            {**lang, 'course_count': counts.get(lang['code'], 0)}
            for lang in SUPPORTED_LANGUAGES
        ])

