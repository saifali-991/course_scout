from rest_framework.pagination import PageNumberPagination


class ResourcesPagination(PageNumberPagination):
    """?page=2&page_size=9 — page_size capped so the UI can request 9/12/24.

    9 is the Discover default: three full rows of the 3-up card grid.
    """

    page_size = 9
    page_size_query_param = 'page_size'
    max_page_size = 48
