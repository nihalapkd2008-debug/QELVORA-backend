from django.db.models import Count, Q, Sum
from rest_framework.pagination import (
    LimitOffsetPagination,
    PageNumberPagination,
)
from rest_framework.response import Response


class AdminProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        statistics = self.page.paginator.object_list.aggregate(
            total_stock=Sum("stock"),
            out_of_stock=Count(
                "id",
                filter=Q(stock=0),
            ),
        )

        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "total_stock": statistics["total_stock"] or 0,
            "out_of_stock": statistics["out_of_stock"],
            "results": data,
        })


class AdminProductLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    limit_query_param = "limit"
    offset_query_param = "offset"
    max_limit = 50