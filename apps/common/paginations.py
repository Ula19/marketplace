from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 3  # Количество объектов на странице
    page_size_query_param = 'page_size'  # Параметр запроса для изменения размера страницы
    max_page_size = 100  # Максимально допустимый размер страницы

    def get_paginated_response(self, data):
        return Response({
            'total_count': self.page.paginator.count,
            'page_number': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
