"""URL marshrutlari.

Loyiha bitta sahifali (single-page-ish) — barcha kalkulyatorlar `/` da
joylashgan, qolganlari faqat eksport endpointlari.
"""
from django.contrib import admin
from django.urls import path

from projects.views import home, reset_session
from projects.views_export import (
    export_analysis_csv,
    export_section_pdf,
    export_session_json,
    report_pdf,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("reset/", reset_session, name="reset_session"),

    # Eksport endpointlari
    path("export/csv/", export_analysis_csv, name="export_csv"),
    path("export/json/", export_session_json, name="export_json"),
    path("export/pdf/", report_pdf, name="export_pdf"),
    path("export/pdf/section/<slug:section>/", export_section_pdf, name="export_section_pdf"),
]
