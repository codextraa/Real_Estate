from backend.paginations import CustomPagination


class PropertyPagination(CustomPagination):
    """Custom pagination class for Property."""

    page_size = 12
