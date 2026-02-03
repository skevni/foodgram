from rest_framework.pagination import PageNumberPagination

from .constants import PAGINATION_PAGE_SIZE, USER_PAGINATION_PAGE_SIZE


class UsersPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = USER_PAGINATION_PAGE_SIZE


class Pagination(PageNumberPagination):
    page_size = PAGINATION_PAGE_SIZE
    max_page_size = PAGINATION_PAGE_SIZE
    page_size_query_param = 'limit'
