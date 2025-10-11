import django_filters
from django.db.models import Q
from core_db.models import Property


class PropertyFilter(django_filters.FilterSet):
    """Property Filter"""

    search = django_filters.CharFilter(method="filter_search_set")
    beds = django_filters.NumberFilter()
    baths = django_filters.NumberFilter()
    price = django_filters.RangeFilter()
    area_sqft = django_filters.RangeFilter()

    class Meta:
        model = Property
        fields = ("search", "beds", "baths", "price", "area_sqft")

    def filter_search_set(
        self, queryset, name, value
    ):  # pylint: disable=unused-argument
        """Filter Property where title contains the search value."""
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(address__icontains=value)
        )
