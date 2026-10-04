"""Hand-picked YouTube creators — the channels CourseScout crawls and ranks first.

Two things live here so the API and the importer can never drift apart:

``TOP_CREATORS``
    Channel names exactly as YouTube spells them. Videos from these channels are
    badged in the UI and float to the top of the YouTube tab
    (``GET /api/resources/?platform=youtube&ordering=top_creators``).

``CREATOR_SOURCES``
    The crawl list used by ``manage.py import_resources --only youtube``: one
    YouTube handle per channel plus the category its videos fall into when the
    title alone is not descriptive enough (e.g. "Microsoft Word Full Course" has
    no keyword to match, so office creators are pinned to data-analytics).
"""


def _creator(handle, name, category='', language='', queries=('',)):
    return {'handle': handle, 'name': name, 'category': category,
            'language': language, 'queries': list(queries)}


# Hindi-first Indian educators + the global giants + the MS Office/Excel crowd
# (Dhaval Patel's codebasics runs both an English and a Hindi channel).
CREATOR_SOURCES = [
    # — Hindi-first —
    _creator('@CodeWithHarry', 'CodeWithHarry', language='hi'),
    _creator('@ApnaCollegeOfficial', 'Apna College', language='hi'),
    _creator('@chaiaurcode', 'Chai aur Code', language='hi'),
    _creator('@CampusX', 'CampusX', language='hi'),
    _creator('@WsCubeTech', 'WsCube Tech', language='hi'),
    _creator('@ThapaTechnical', 'Thapa Technical', language='hi'),
    _creator('@codehelp', 'CodeHelp - by Babbar', language='hi'),
    _creator('@sumitkhandelwal', 'Sumit Khandelwal', 'data-analytics', 'hi'),
    # — data analytics / AI (Dhaval Patel and friends) —
    _creator('@codebasics', 'codebasics', 'data-analytics'),
    _creator('@codebasicsHindi', 'codebasics Hindi', 'data-analytics', 'hi'),
    _creator('@krishnaik06', 'Krish Naik', 'ai-machine-learning'),
    _creator('@AlexTheAnalyst', 'Alex The Analyst', 'data-analytics'),
    _creator('@3Blue1Brown', '3Blue1Brown', 'ai-machine-learning'),
    _creator('@DeepLearningAI', 'DeepLearningAI', 'ai-machine-learning'),
    # — English giants —
    _creator('@freecodecamp', 'freeCodeCamp'),
    _creator('@TraversyMedia', 'Traversy Media'),
    _creator('@NetNinja', 'Net Ninja'),
    _creator('@ProgrammingWithMosh', 'Programming with Mosh'),
    _creator('@CS50', 'CS50'),
    _creator('@MITOpenCourseWare', 'MIT OpenCourseWare', 'ai-machine-learning'),
    _creator('@GoogleCloudTech', 'Google Cloud', 'data-analytics'),
    # — MS Office / Excel / PowerPoint —
    _creator('@LeilaGharani', 'Leila Gharani', 'data-analytics'),
    _creator('@KevinStratvert', 'Kevin Stratvert', 'data-analytics'),
    _creator('@Chandoo', 'Chandoo', 'data-analytics'),
    _creator('@ExcelIsFun', 'ExcelIsFun', 'data-analytics'),
    _creator('@MyOnlineTraining', 'MyOnlineTraining', 'data-analytics'),
    _creator('@myselfRobert', 'My Online Training Partner', 'data-analytics'),
]

TOP_CREATORS = [c['name'] for c in CREATOR_SOURCES]

_TOP_LOOKUP = {name.lower() for name in TOP_CREATORS}


def is_top_creator(provider):
    """Case-insensitive membership test against ``TOP_CREATORS``."""
    return (provider or '').strip().lower() in _TOP_LOOKUP


def top_creator_q():
    """A ``Q`` object matching resources whose provider is a top creator."""
    from django.db.models import Q

    query = Q()
    for name in TOP_CREATORS:
        query |= Q(provider__iexact=name)
    return query


def order_top_creators_first(queryset, fallback=('-rating', 'created_at')):
    """Sort so that top-creator rows come first, everything else unchanged."""
    from django.db.models import Case, IntegerField, Value, When

    whens = [When(provider__iexact=name, then=Value(0)) for name in TOP_CREATORS]
    return (queryset
            .annotate(_cs_top=Case(*whens, default=Value(1), output_field=IntegerField()))
            .order_by('_cs_top', *fallback))
