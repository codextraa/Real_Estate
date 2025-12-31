import django_filters
from core_db_ai.models import AIReport


class AIReportFilter(django_filters.FilterSet):
    """AI Report Filter"""

    status = django_filters.ChoiceFilter(choices=AIReport.Status.choices)

    class Meta:
        model = AIReport
        fields = ["status"]
