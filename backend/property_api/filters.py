import django_filters
from django.db.models import Q
from core_db.models import Property


class PropertyFilter(django_filters.FilterSet):
    """Property Filter"""

    search = django_filters.CharFilter(method="filter_search_set")
    address = django_filters.CharFilter(lookup_expr="icontains")
    beds = django_filters.CharFilter(method="filter_beds_and_baths")
    baths = django_filters.CharFilter(method="filter_beds_and_baths")
    price = django_filters.RangeFilter(
        field_name="price", method="filter_price_and_area_sqft"
    )
    area_sqft = django_filters.RangeFilter(
        field_name="area_sqft", method="filter_price_and_area_sqft"
    )

    class Meta:
        model = Property
        fields = ("search", "address", "beds", "baths", "price", "area_sqft")

    def filter_search_set(
        self, queryset, name, value
    ):  # pylint: disable=unused-argument
        """Filter Property where title contains the search value."""
        return queryset.filter(
            Q(title__icontains=value)
            | Q(description__icontains=value)
            | Q(address__icontains=value)
        )

    def filter_beds_and_baths(self, queryset, name, value):
        """
        Filter Property by number of beds and baths
        """
        min_value = 1
        value_str = str(value).strip()

        if value_str.lower() == "8+":
            filter_kwargs = {f"{name}__gte": 8}
            return queryset.filter(**filter_kwargs)

        try:
            num_value = int(value_str)
            num_value = max(num_value, min_value)
            filter_kwargs = {name: num_value}
            return queryset.filter(**filter_kwargs)
        except ValueError:
            return queryset

    def filter_price_and_area_sqft(self, queryset, name, value):
        """
        Filter Property by price and area
        """
        if not value:
            return queryset

        try:
            min_value = value.start
            max_value = value.stop
        except AttributeError:
            return queryset

        if min_value is None or min_value < 1:
            min_value = 1
        if max_value is None:
            filter_kwargs = {f"{name}__gte": min_value}
            return queryset.filter(**filter_kwargs)

        filter_kwargs = {
            f"{name}__gte": min_value,
            f"{name}__lte": max_value,
        }
        return queryset.filter(**filter_kwargs)
