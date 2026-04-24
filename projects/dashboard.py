"""Dashboard hisob-kitoblari uchun POST dispatcher.

Bitta `action` qatori orqali kerakli kalkulyator chaqiriladi va natija
JSON ko'rinishida qaytariladi. Yangi tahlil qo'shish — yangi `if action == ...`
bloki + persist_run dagi kind_map ga bitta qator qo'shish demak.
"""
from typing import Any

from analytics.services.core_finance import compute_classic_metrics
from analytics.services.dynamic_risk import compute_net_export_benefit
from analytics.services.forecast_export import forecast_export_volume
from analytics.services.monte_carlo import run_monte_carlo
from analytics.services.risk_matrix import compute_risk_matrix
from analytics.services.saas_metrics import compute_saas_metrics
from analytics.services.sustainability import compute_sustainability_index
from projects.dashboard_extra import EXTRA_ACTIONS, chart_payload_extra, run_extra_analysis
from projects.models import AnalysisRun, ExportTimeSeriesPoint
from projects.parse_helpers import float_list as _float_list
from projects.parse_helpers import get_float as _get_float
from projects.parse_helpers import get_int as _get_int
from uzbekistan.services.bpo_export import compute_bpo_export_profitability
from uzbekistan.services.it_park import compute_tax_shield
from uzbekistan.services.rohc import compute_rohc


def run_analysis(*, action: str, post: Any, project) -> tuple[dict[str, Any] | None, str | None]:
    """(natija, xato) juftligini qaytaradi. Faqat bittasi None bo'lmasligi kafolatlanadi."""
    try:
        # Qo'shimcha (ikkinchi guruh) tahlillarni alohida modulga ko'chirganmiz —
        # bu fayl juda shishib ketmasligi uchun
        if action in EXTRA_ACTIONS:
            return run_extra_analysis(action, post, project)

        if action == "classic":
            cfs = _float_list(post.get("annual_cashflows", ""))
            if not cfs:
                raise ValueError("Yillik pul oqimlari (kamida 1 qiymat) kiriting")

            out = compute_classic_metrics(
                initial_investment=_get_float(post, "initial_investment"),
                annual_cashflows=cfs,
                discount_rate=_get_float(post, "discount_rate", 0.12),
                salvage_value=_get_float(post, "salvage_value", 0.0),
            )
            # Chartda ko'rsatish uchun nom o'zgartirib yuboramiz
            out["chart_cashflows"] = out.pop("cashflows_used")
            return out, None

        if action == "monte_carlo":
            # seed bo'sh bo'lsa — random; kiritilgan bo'lsa — reproducible
            rs_raw = post.get("random_seed")
            seed = int(str(rs_raw).strip()) if rs_raw not in (None, "") else None

            out = run_monte_carlo(
                n_simulations=_get_int(post, "n_simulations", 10_000),
                initial_investment=_get_float(post, "initial_investment"),
                years=_get_int(post, "years", 5),
                discount_rate=_get_float(post, "discount_rate", 0.12),
                revenue_mean=_get_float(post, "revenue_mean"),
                revenue_std=_get_float(post, "revenue_std"),
                cost_mean=_get_float(post, "cost_mean"),
                cost_std=_get_float(post, "cost_std"),
                revenue_growth_mean=_get_float(post, "revenue_growth_mean", 0.05),
                cost_growth_mean=_get_float(post, "cost_growth_mean", 0.04),
                random_seed=seed,
            )
            return out, None

        if action == "saas":
            out = compute_saas_metrics(
                arpu_monthly_usd=_get_float(post, "arpu_monthly_usd"),
                gross_margin=_get_float(post, "gross_margin"),
                monthly_churn_rate=_get_float(post, "monthly_churn_rate"),
                marketing_spend_usd=_get_float(post, "marketing_spend_usd"),
                new_customers=_get_int(post, "new_customers"),
            )
            return out, None

        if action == "risk_matrix":
            out = compute_risk_matrix(
                country_risk_score=_get_float(post, "country_risk_score"),
                fx_volatility=_get_float(post, "fx_volatility"),
                cyber_cost_share=_get_float(post, "cyber_cost_share"),
                base_npv=_get_float(post, "base_npv", 1.0),
            )
            return out, None

        if action == "forecast":
            raw = (post.get("history_usd") or "").strip()
            if raw:
                hist = _float_list(raw)
            else:
                # Hech narsa kiritilmagan bo'lsa — bazadagi tarixiy ma'lumotni olamiz
                hist = [
                    float(x.export_value_usd)
                    for x in ExportTimeSeriesPoint.objects.filter(project=project).order_by("period")
                ]

            if len(hist) < 3:
                raise ValueError("Kamida 3 ta oy qiymati kiriting yoki Export tarixini to'ldiring")

            out = forecast_export_volume(
                hist,
                horizon_months=_get_int(post, "horizon_months", 12),
                prefer_arima=post.get("prefer_arima") == "on",
            )
            return out, None

        if action == "dynamic_risk":
            out = compute_net_export_benefit(
                export_revenue_usd=_get_float(post, "export_revenue_usd"),
                international_fee_rate=_get_float(post, "international_fee_rate"),
                local_costs_in_local_currency=_get_float(post, "local_costs_in_local_currency"),
                exchange_rate_local_per_usd=_get_float(post, "exchange_rate_local_per_usd"),
                delta_e=_get_float(post, "delta_e", 0.0),
            )
            return out, None

        if action == "tax_shield":
            out = compute_tax_shield(
                taxable_profit_usd=_get_float(post, "taxable_profit_usd"),
                income_tax_rate_without_incentive=_get_float(
                    post, "income_tax_rate_without_incentive", 0.15
                ),
                income_tax_rate_it_park=_get_float(post, "income_tax_rate_it_park", 0.075),
            )
            return out, None

        if action == "bpo_uz":
            out = compute_bpo_export_profitability(
                annual_export_revenue_usd=_get_float(post, "annual_export_revenue_usd"),
                annual_payroll_usd=_get_float(post, "annual_payroll_usd"),
                other_operating_costs_usd=_get_float(post, "other_operating_costs_usd", 0.0),
            )
            return out, None

        if action == "rohc":
            bench_raw = (post.get("benchmark_revenue_per_payroll") or "").strip()
            out = compute_rohc(
                annual_export_revenue_usd=_get_float(post, "annual_export_revenue_usd"),
                annual_payroll_usd=_get_float(post, "annual_payroll_usd"),
                headcount=_get_int(post, "headcount"),
                benchmark_revenue_per_payroll=float(bench_raw) if bench_raw else None,
            )
            return out, None

        if action == "sustainability":
            out = compute_sustainability_index(
                monte_carlo_success_probability=_get_float(post, "monte_carlo_success_probability"),
                composite_risk_score=_get_float(post, "composite_risk_score"),
                forecast_method=(post.get("forecast_method") or "linear_regression").strip()
                or "linear_regression",
            )
            return out, None

    except (ValueError, ZeroDivisionError) as e:
        # Foydalanuvchi xatoligi — to'liq stack trace shart emas, faqat o'qiluvchi xabar
        return None, str(e)

    return None, "Noma'lum amal"


# action -> AnalysisRun.Kind. Bu yerda yo'q action — tarixga yozilmaydi
# (lekin sessiyada ko'rinadi). Bu juda muhim narsalar uchun ham ataylab.
_KIND_MAP = {
    "classic": AnalysisRun.Kind.CLASSIC,
    "monte_carlo": AnalysisRun.Kind.MONTE_CARLO,
    "saas": AnalysisRun.Kind.SAAS,
    "risk_matrix": AnalysisRun.Kind.RISK_MATRIX,
    "forecast": AnalysisRun.Kind.FORECAST,
    "dynamic_risk": AnalysisRun.Kind.DYNAMIC_RISK,
    "tax_shield": AnalysisRun.Kind.TAX_SHIELD,
    "bpo_uz": AnalysisRun.Kind.BPO_UZ,
    "rohc": AnalysisRun.Kind.ROHC,
    "sustainability": AnalysisRun.Kind.SUSTAINABILITY,
    "sensitivity": AnalysisRun.Kind.SENSITIVITY,
    "scenarios": AnalysisRun.Kind.SCENARIOS,
    "monthly_dcf": AnalysisRun.Kind.MONTHLY_DCF,
    "saas_extended": AnalysisRun.Kind.SAAS_EXTENDED,
    "risk_register": AnalysisRun.Kind.RISK_REGISTER,
    "fx_fetch": AnalysisRun.Kind.FX_FETCH,
    "market_benchmark": AnalysisRun.Kind.MARKET_BENCHMARK,
}


def persist_run(project, action: str, post_data: dict, summary: dict) -> None:
    kind = _KIND_MAP.get(action)
    if not kind:
        return
    AnalysisRun.objects.create(
        project=project,
        kind=kind,
        parameters=dict(post_data),
        summary=summary,
    )


def chart_payload(action: str, result: dict[str, Any]) -> dict[str, Any]:
    """Chart.js sozlamalariga moslashtirilgan dict.

    Hech qanday chart kerak emas bo'lsa — {"type": "none"} qaytariladi
    (template qarab "rasm o'rniga jadval" rejimiga o'tadi).
    """
    if action in EXTRA_ACTIONS:
        c = chart_payload_extra(action, result)
        if c.get("type") != "none":
            return c

    if action == "classic":
        cfs = result.get("chart_cashflows", [])
        return {
            "type": "bar",
            "labels": [f"t{i}" for i in range(len(cfs))],
            "datasets": [{"label": "Pul oqimi", "data": cfs}],
        }

    if action == "monte_carlo":
        h = result.get("histogram", {})
        return {
            "type": "bar",
            "labels": [f"{x:.0f}" for x in h.get("labels", [])],
            "datasets": [{"label": "NPV taqsimoti", "data": h.get("counts", [])}],
        }

    if action == "saas":
        return {
            "type": "doughnut",
            "labels": ["LTV", "CAC"],
            "datasets": [{
                "data": [result.get("ltv_usd", 0), result.get("cac_usd", 0)],
                "backgroundColor": ["#22c55e", "#f97316"],
            }],
        }

    if action == "risk_matrix":
        rows = result.get("heatmap_rows", [])
        return {
            "type": "bar",
            "labels": [r["factor"] for r in rows],
            "datasets": [{
                "label": "Risk (0–1)",
                "data": [r["value"] for r in rows],
                "backgroundColor": ["#ef4444", "#eab308", "#6366f1"],
            }],
        }

    if action == "forecast":
        fc = result.get("forecast_next_months_usd") or []
        return {
            "type": "line",
            "labels": [f"Oy {i + 1}" for i in range(len(fc))],
            "datasets": [{
                "label": "Bashorat (USD)",
                "data": fc,
                "borderColor": "#38bdf8",
                "fill": True,
            }],
        }

    if action == "dynamic_risk":
        return {
            "type": "bar",
            "labels": ["Tushum (komissiyadan keyin)", "Mahalliy xarajat (USD)", "Sof foyda"],
            "datasets": [{
                "data": [
                    result.get("net_usd_inflow_after_fees", 0),
                    result.get("local_costs_usd_equivalent", 0),
                    result.get("net_export_benefit_usd", 0),
                ],
                "backgroundColor": ["#22c55e", "#f87171", "#a78bfa"],
            }],
        }

    if action == "tax_shield":
        return {
            "type": "bar",
            "labels": ["Soliq (imtiyozsiz)", "Soliq (IT Park)", "Tax shield"],
            "datasets": [{
                "data": [
                    result.get("tax_without_incentive_usd", 0),
                    result.get("tax_with_it_park_usd", 0),
                    result.get("tax_shield_usd", 0),
                ],
                "backgroundColor": ["#64748b", "#22c55e", "#fbbf24"],
            }],
        }

    if action == "bpo_uz":
        tb = result.get("tax_shield_analysis")
        if not tb:
            return {"type": "none"}  # EBIT manfiy bo'lib chartga yarashmadi
        return {
            "type": "bar",
            "labels": ["Sof foyda (imtiyozsiz)", "Sof foyda (IT Park)"],
            "datasets": [{
                "data": [
                    tb.get("net_profit_after_tax_without_usd", 0),
                    tb.get("net_profit_after_tax_with_it_park_usd", 0),
                ],
                "backgroundColor": ["#94a3b8", "#22d3ee"],
            }],
        }

    if action == "rohc":
        rel = result.get("relative_to_benchmark")
        return {
            "type": "bar",
            "labels": ["ROHC (eksport/payroll)", "Benchmark nisbati (agar berilgan)"],
            "datasets": [{
                "label": "Qiymat",
                "data": [
                    float(result.get("rohc_ratio", 0)),
                    float(rel) if rel is not None else 0.0,
                ],
                "backgroundColor": ["#2dd4bf", "#a855f7"],
            }],
        }

    if action == "sustainability":
        idx = float(result.get("sustainability_index", 0))
        return {
            "type": "doughnut",
            "labels": ["Indeks", "Qolgan"],
            "datasets": [{
                "data": [idx, max(0, 100 - idx)],
                "backgroundColor": ["#34d399", "#1e293b"],
            }],
        }

    return {"type": "none"}
