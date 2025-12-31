from core_db_ai.models import AIReport
from .serializers import AIReportSerializer, AIReportListSerializer
from rest_framework.viewsets import ModelViewSet
from backend_ai.renderers import ViewRenderer
from .paginations import AIReportPagination
from .filters import AIReportFilter
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated


class AIReportViewSet(ModelViewSet):
    queryset = AIReport.objects.all()
    serializer_class = AIReportSerializer
    renderer_classes = [ViewRenderer]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AIReportFilter
    pagination_class = AIReportPagination
    http_method_names = ["get", "post", "delete"]

    def get_serializer_class(self):
        """Assign serializer based on action."""
        if self.action in ("list", "my_reports"):
            return AIReportListSerializer
        return super().get_serializer_class()
