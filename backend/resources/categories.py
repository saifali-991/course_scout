"""Category metadata — drives /api/categories/ and the Categories page.

Slugs double as the `Resource.category` DB values, so the counts on the
Categories page and the "All topics" dropdown always match the data.
"""

CATEGORIES = [
    {
        'slug': 'python',
        'name': 'Python',
        'description': 'Learn Python from scratch — scripts, automation, and real projects.',
        'search_hint': 'Python',
        'icon': 'python',
        'color': '#1d6ff2',
    },
    {
        'slug': 'web-development',
        'name': 'Web Development',
        'description': 'Frontend, backend, and full-stack development with modern tools.',
        'search_hint': 'Web Development',
        'icon': 'code',
        'color': '#f97316',
    },
    {
        'slug': 'data-analytics',
        'name': 'Data Analytics',
        'description': 'Excel, SQL, and BI tools to turn raw data into decisions.',
        'search_hint': 'Data Analytics',
        'icon': 'data',
        'color': '#ef4460',
    },
    {
        'slug': 'ai-machine-learning',
        'name': 'AI & Machine Learning',
        'description': 'ML, deep learning, and generative AI from leading universities.',
        'search_hint': 'Machine Learning',
        'icon': 'bot',
        'color': '#3b82f6',
    },
    {
        'slug': 'ui-ux-design',
        'name': 'UI/UX Design',
        'description': 'Design thinking, Figma, and user research for beautiful products.',
        'search_hint': 'UI/UX',
        'icon': 'pen',
        'color': '#0891b2',
    },
    {
        'slug': 'digital-marketing',
        'name': 'Digital Marketing',
        'description': 'SEO, social media, and performance marketing that converts.',
        'search_hint': 'Digital Marketing',
        'icon': 'megaphone',
        'color': '#6366f1',
    },
]

CATEGORY_SLUGS = [c['slug'] for c in CATEGORIES]
CATEGORY_CHOICES = [(c['slug'], c['name']) for c in CATEGORIES]

_CATEGORY_BY_SLUG = {c['slug']: c for c in CATEGORIES}


def get_category(slug):
    return _CATEGORY_BY_SLUG.get(slug)
