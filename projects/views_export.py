"""Eksport view'lari: CSV, JSON va PDF (umumiy + bo'limma-bo'lim).

PDF generatsiyasi `xhtml2pdf` orqali. Kutubxona xotiraga bir marta yuklanadi
(modul darajasidagi import sinov), keyingi so'rovlar tezroq bajariladi.
"""
import csv
import json
from io import BytesIO

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone as dj_tz

from projects.models import AnalysisRun
from projects.pdf_helpers import (
    SECTION_TITLES,
    iter_report_sections,
    param_rows,
    result_rows,
    section_title,
)
from projects.views_helpers import get_active_project

# Bo'limma-bo'lim PDF uchun ruxsat etilgan kalitlar — `pdf_helpers`dagi
# sarlavhalar ro'yxati bilan bir manbadan oladi (ikki joyda yangilash shart emas).
SECTION_PDF_KEYS = frozenset(SECTION_TITLES.keys())


# xhtml2pdf ni modul darajasida bir marta tekshiramiz: importning o'zi
# ~150-300 ms olishi mumkin, har so'rovda qayta-qayta qilishning hojati yo'q.
try:
    from xhtml2pdf import pisa as _pisa  # noqa: F401
    _PDF_AVAILABLE = True
except ImportError:  # pragma: no cover
    _pisa = None  # type: ignore[assignment]
    _PDF_AVAILABLE = False


def _safe_json(obj) -> str:
    """JSON ga aylantirib bo'lmaydigan turlarni stringga o'tkazib qaytaradi."""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    except TypeError:
        return str(obj)


def export_analysis_csv(request):
    project = get_active_project(request)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="investcalc_analysis.csv"'

    w = csv.writer(response)
    w.writerow(["vaqt", "tur", "parametrlar", "xulosa_json"])

    runs = AnalysisRun.objects.filter(project=project).order_by("-created_at")[:800]
    for run in runs:
        w.writerow([
            run.created_at.isoformat(),
            run.kind,
            json.dumps(run.parameters, ensure_ascii=False)[:2000],
            json.dumps(run.summary, ensure_ascii=False)[:4000],
        ])

    snap = request.session.get("dashboard_results", {})
    if snap:
        w.writerow([])
        w.writerow(["sessiya_natijalari", json.dumps(snap, default=str)[:8000]])

    return response


def export_session_json(request):
    project = get_active_project(request)

    payload = {
        "project": project.name,
        "slug": project.slug,
        "dashboard_results": request.session.get("dashboard_results", {}),
        "form_defaults": request.session.get("form_defaults", {}),
    }

    response = HttpResponse(
        json.dumps(payload, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
    )
    response["Content-Disposition"] = 'attachment; filename="investcalc_session.json"'
    return response


def _render_pdf(html: str, filename: str) -> HttpResponse:
    """HTML -> PDF (xhtml2pdf orqali). Kutubxona yo'q bo'lsa — 503."""
    if not _PDF_AVAILABLE or _pisa is None:
        return HttpResponse(
            "PDF eksporti uchun kutubxona o'rnatilmagan. Buyruq: pip install xhtml2pdf",
            status=503,
            content_type="text/plain; charset=utf-8",
        )

    out = BytesIO()
    # encoding=utf-8 — kirillcha/o'zbek harflar uchun
    _pisa.CreatePDF(html, dest=out, encoding="utf-8")
    out.seek(0)

    response = HttpResponse(out.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    # Brauzer eski PDF ni keshlamasligi uchun
    response["Cache-Control"] = "no-store, max-age=0"
    return response


def report_pdf(request):
    """Sessiyadagi barcha natijalarni bitta chiroyli PDF ga jamlaydi."""
    from projects.conclusions import enrich_results  # circular import oldini olish

    project = get_active_project(request)
    raw = request.session.get("dashboard_results", {}) or {}

    if not raw:
        return HttpResponse(
            "Sessiyada hech qanday hisob-kitob yo'q. PDF olishdan oldin "
            "kamida bitta bo'limda «Hisoblash» tugmasini bosing.",
            status=400,
            content_type="text/plain; charset=utf-8",
        )

    results = enrich_results(raw)
    sections = list(iter_report_sections(results))

    html = render_to_string(
        "report_pdf.html",
        {
            "project": project,
            "sections": sections,
            "generated_at": dj_tz.localtime(dj_tz.now()).strftime("%d.%m.%Y, %H:%M"),
            "section_count": len(sections),
        },
        request=request,
    )
    return _render_pdf(html, f"investcalc_{project.slug or 'hisobot'}.pdf")


def export_section_pdf(request, section: str):
    from projects.conclusions import enrich_results

    key = (section or "").strip().lower()
    if key not in SECTION_PDF_KEYS:
        return HttpResponse(
            "Bo'lim topilmadi.",
            status=404,
            content_type="text/plain; charset=utf-8",
        )

    project = get_active_project(request)
    raw = request.session.get("dashboard_results", {}) or {}
    if key not in raw:
        return HttpResponse(
            "Bu bo'lim uchun sessiyada natija yo'q. Avval «Hisoblash»ni bosing.",
            status=400,
            content_type="text/plain; charset=utf-8",
        )

    enriched = enrich_results({key: raw[key]})
    entry = enriched.get(key) or {}

    html = render_to_string(
        "report_section_pdf.html",
        {
            "project": project,
            "title": section_title(key),
            "params": param_rows(entry.get("params")),
            "results": result_rows(entry.get("result")),
            "conclusion": entry.get("conclusion"),
            "result_str": _safe_json(entry.get("result")),
            "generated_at": dj_tz.localtime(dj_tz.now()).strftime("%d.%m.%Y, %H:%M"),
        },
        request=request,
    )
    return _render_pdf(html, f"investcalc_{key}.pdf")
