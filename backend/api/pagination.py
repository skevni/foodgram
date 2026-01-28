from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class UsersPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = settings.USER_PAGINATION_PAGE_SIZE


class Pagination(PageNumberPagination):
    page_size = settings.PAGINATION_PAGE_SIZE
    max_page_size = settings.PAGINATION_PAGE_SIZE
    page_size_query_param = 'limit'
