from django.contrib import admin

from projects.models import (
    AnalysisRun,
    ExportTimeSeriesPoint,
    InvestmentProject,
    ProjectFinancialSnapshot,
)


@admin.register(InvestmentProject)
class InvestmentProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(ProjectFinancialSnapshot)
class ProjectFinancialSnapshotAdmin(admin.ModelAdmin):
    list_display = ("project", "label", "created_at")
    list_filter = ("project",)


@admin.register(ExportTimeSeriesPoint)
class ExportTimeSeriesPointAdmin(admin.ModelAdmin):
    list_display = ("project", "period", "export_value_usd")
    list_filter = ("project",)
    date_hierarchy = "period"


@admin.register(AnalysisRun)
class AnalysisRunAdmin(admin.ModelAdmin):
    list_display = ("project", "kind", "created_at")
    list_filter = ("kind", "project")
    date_hierarchy = "created_at"
