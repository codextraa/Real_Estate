from backend.paginations import CustomePagination

class PropertyPagination(CustomePagination):
    """Custom pagination class for Property."""

    page_size = 12

