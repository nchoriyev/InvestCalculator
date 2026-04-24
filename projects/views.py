"""Asosiy sahifa view'i.

Hamma kalkulyator bittagina sahifaga sig'gan: foydalanuvchi formani to'ldiradi,
tegishli `action` bilan POST yuboradi, biz hisoblaymiz va natijani sessiyaga
saqlab, redirect orqali shu sahifaning hash bo'limiga qaytaramiz (PRG pattern).
"""
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from projects.banner_data import get_banner_data
from projects.conclusions import enrich_results, strip_for_chart_json
from projects.dashboard import chart_payload, persist_run, run_analysis
from projects.models import AnalysisRun
from projects.views_helpers import get_active_project


# Form default'larini template'ga uzatishda ishlatiladigan kalit nomlari
# (template tomonida {{ fc.something }}, {{ fm.something }} ko'rinishida).
# Tartib muhim emas, lekin yangi kalkulyator qo'shilganda shu yerga ham
# bitta qator qo'shish kerak.
_FORM_KEYS = {
    "fc": "classic",
    "fm": "monte_carlo",
    "fs": "saas",
    "fr": "risk_matrix",
    "ff": "forecast",
    "fd": "dynamic_risk",
    "ft": "tax_shield",
    "fb": "bpo_uz",
    "fro": "rohc",
    "fsu": "sustainability",
    "fse": "sensitivity",
    "fsc": "scenarios",
    "fmo": "monthly_dcf",
    "fsext": "saas_extended",
    "frr": "risk_register",
    "ffx": "fx_fetch",
    "fmb": "market_benchmark",
}


def _form_defaults_dict(fd: dict) -> dict:
    """Sessiyadagi form_defaults dan template uchun qisqa nom -> dict mapping."""
    out = {}
    for tpl_key, action in _FORM_KEYS.items():
        v = fd.get(action)
        out[tpl_key] = v if isinstance(v, dict) else {}
    return out


def home(request):
    project = get_active_project(request)
    results = request.session.get("dashboard_results", {})
    form_defaults = request.session.get("form_defaults", {})

    if request.method == "POST":
        action = (request.POST.get("action") or "").strip()
        if not action:
            messages.error(request, "Amal tanlanmagan.")
            return redirect(reverse("home"))

        res, err = run_analysis(action=action, post=request.POST, project=project)

        if err:
            messages.error(request, err)
        elif res is not None:
            # Form defaults va natijalarni sessiyaga yozamiz —
            # foydalanuvchi sahifani yangilaganda ham qiymatlar joyida tursin
            posted = request.POST.dict()
            form_defaults[action] = posted
            results[action] = {
                "result": res,
                "chart": chart_payload(action, res),
                # PDF da kirish parametrlarini ko'rsatish uchun saqlaymiz
                "params": {k: v for k, v in posted.items() if k not in ("csrfmiddlewaretoken", "action")},
            }
            request.session["dashboard_results"] = results
            request.session["form_defaults"] = form_defaults
            request.session.modified = True

            persist_run(project, action, dict(request.POST), res)
            messages.success(request, "Hisob-kitob yangilandi.")

        # PRG (Post/Redirect/Get) — F5 bosilganda ikkinchi marta yuborilmasin
        return redirect(f"{reverse('home')}#{action}")

    results_display = enrich_results(results)
    history = AnalysisRun.objects.filter(project=project).order_by("-created_at")[:30]

    context = {
        "project": project,
        "banner": get_banner_data(),
        "history": history,
        "results": results_display,
        "results_for_charts": strip_for_chart_json(results_display),
        "form_defaults": form_defaults,
    }
    context.update(_form_defaults_dict(form_defaults or {}))

    return render(request, "home.html", context)


@require_POST
def reset_session(request):
    """Joriy sessiyadagi barcha hisob-kitob natijalarini va form qiymatlarini tozalaydi.

    DB dagi tarix (AnalysisRun) tegmaydi — faqat aktiv brauzer sessiyasi.
    """
    request.session.pop("dashboard_results", None)
    request.session.pop("form_defaults", None)
    request.session.modified = True
    messages.success(request, "Sessiya tozalandi — barcha natijalar va kiritilgan qiymatlar olib tashlandi.")
    return HttpResponseRedirect(reverse("home"))
