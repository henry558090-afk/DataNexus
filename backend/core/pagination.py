from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """默认分页：返回 {count, next, previous, results}。"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 200
