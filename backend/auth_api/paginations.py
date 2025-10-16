from backend.paginations import CustomPagination


class UserPagination(CustomPagination):
    """Custom pagination class for users."""

    page_size = 2
