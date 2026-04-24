"""Qo'shimcha kalkulyatorlar: sensitivlik, ssenariylar, oylik DCF, SaaS+, FX, va h.k.

Bularni alohida modulga ajratdim, chunki dashboard.py o'zi katta bo'lib ketgandi.
Yangi turdagi tahlil qo'shsangiz — EXTRA_ACTIONS ga kalit qo'shing va
quyidagi ikki funksiyaga (run + chart) tegishli holatni yozib qo'ying.
"""
import json
from typing import Any

from analytics.services.fx_service import fetch_rate_usd_to
from analytics.services.market_benchmark import fetch_world_bank_indicator
from analytics.services.monthly_finance import compute_monthly_dcf
from analytics.services.risk_register import score_risk_register
from analytics.services.saas_extended import (
    net_revenue_retention,
    rule_of_40,
    unit_economics,
)
from analytics.services.scenarios import compare_scenarios
from analytics.services.sensitivity import run_sensitivity_annual
from projects.parse_helpers import float_list as _float_list
from projects.parse_helpers import get_float as _get_float
from projects.parse_helpers import get_int as _get_int

EXTRA_ACTIONS = frozenset({
    "sensitivity",
    "scenarios",
    "monthly_dcf",
    "saas_extended",
    "risk_register",
    "fx_fetch",
    "market_benchmark",
})

# Default sensitivlik qadamlari (foyz)
_DEFAULT_SENSITIVITY_STEPS = [-20, -10, 0, 10, 20]


def run_extra_analysis(action: str, post: Any, project) -> tuple[dict[str, Any] | None, str | None]:
    try:
        if action == "sensitivity":
            cfs = _float_list(post.get("annual_cashflows", ""))
            if not cfs:
                raise ValueError("Pul oqimlari kerak")

            param = (post.get("sensitivity_parameter") or "discount_rate").strip()
            steps = _float_list(post.get("sensitivity_steps") or "") or _DEFAULT_SENSITIVITY_STEPS

            out = run_sensitivity_annual(
                initial_investment=_get_float(post, "initial_investment"),
                annual_cashflows=cfs,
                discount_rate=_get_float(post, "discount_rate", 0.12),
                salvage_value=_get_float(post, "salvage_value", 0.0),
                parameter=param,
                steps_pct=steps,
            )
            return out, None

        if action == "scenarios":
            cfs = _float_list(post.get("annual_cashflows", ""))
            if not cfs:
                raise ValueError("Pul oqimlari kerak")

            out = compare_scenarios(
                initial_investment=_get_float(post, "initial_investment"),
                discount_rate=_get_float(post, "discount_rate", 0.12),
                salvage_value=_get_float(post, "salvage_value", 0.0),
                base_cashflows=cfs,
                opt_revenue_mult=_get_float(post, "opt_revenue_mult", 1.15),
                opt_cost_mult=_get_float(post, "opt_cost_mult", 0.95),
                pes_revenue_mult=_get_float(post, "pes_revenue_mult", 0.85),
                pes_cost_mult=_get_float(post, "pes_cost_mult", 1.08),
            )
            return out, None

        if action == "monthly_dcf":
            mcf = _float_list(post.get("monthly_cashflows", ""))
            if not mcf:
                raise ValueError("Oylik pul oqimlari kerak")

            out = compute_monthly_dcf(
                initial_investment=_get_float(post, "initial_investment"),
                monthly_cashflows=mcf,
                annual_discount_rate=_get_float(post, "discount_rate", 0.12),
            )
            return out, None

        if action == "saas_extended":
            mode = (post.get("saas_ext_mode") or "rule40").strip()

            if mode == "rule40":
                out = rule_of_40(
                    revenue_growth_yoy=_get_float(post, "revenue_growth_yoy"),
                    profit_margin=_get_float(post, "profit_margin"),
                )
            elif mode == "nrr":
                out = net_revenue_retention(
                    starting_mrr=_get_float(post, "starting_mrr"),
                    ending_mrr=_get_float(post, "ending_mrr"),
                    churned_mrr=_get_float(post, "churned_mrr", 0),
                    expansion_mrr=_get_float(post, "expansion_mrr", 0),
                )
            elif mode == "unit":
                out = unit_economics(
                    price_per_unit_usd=_get_float(post, "price_per_unit_usd"),
                    variable_cost_per_unit_usd=_get_float(post, "variable_cost_per_unit_usd"),
                    units_per_month=_get_float(post, "units_per_month"),
                    fixed_cost_monthly_usd=_get_float(post, "fixed_cost_monthly_usd", 0),
                )
            else:
                raise ValueError("saas_ext_mode noto'g'ri")

            out["mode"] = mode  # template chart uchun rejimni bilishi kerak
            return out, None

        if action == "risk_register":
            raw = (post.get("risk_register_json") or "").strip()
            if not raw:
                raise ValueError("JSON risklar kiriting")

            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError("Ro'yxat JSON bo'lishi kerak")

            risks = [
                {
                    "name": item.get("name", ""),
                    "probability": float(item["probability"]),
                    "impact": float(item["impact"]),
                }
                for item in data
            ]
            return score_risk_register(risks), None

        if action == "fx_fetch":
            tgt = (post.get("fx_target") or "UZS").strip()
            return fetch_rate_usd_to(target_currency=tgt), None

        if action == "market_benchmark":
            iso = (post.get("wb_country") or "UZ").strip()
            return fetch_world_bank_indicator(country_iso2=iso), None

    except (ValueError, json.JSONDecodeError, ZeroDivisionError, KeyError) as e:
        return None, str(e)

    return None, "Noma'lum amal"


def chart_payload_extra(action: str, result: dict[str, Any]) -> dict[str, Any]:
    if action == "sensitivity":
        steps = result.get("steps", [])
        return {
            "type": "line",
            "labels": [str(s["step_pct"]) for s in steps],
            "datasets": [{
                "label": "NPV",
                "data": [s["npv"] for s in steps],
                "borderColor": "#0284c7",
                "fill": False,
            }],
        }

    if action == "scenarios":
        return {
            "type": "bar",
            "labels": [
                result["base"]["label"],
                result["optimistic"]["label"],
                result["pessimistic"]["label"],
            ],
            "datasets": [{
                "label": "NPV",
                "data": [
                    result["base"]["npv"],
                    result["optimistic"]["npv"],
                    result["pessimistic"]["npv"],
                ],
                "backgroundColor": ["#64748b", "#22c55e", "#f97316"],
            }],
        }

    if action == "monthly_dcf":
        cfs = result.get("chart_monthly_cfs", [])
        return {
            "type": "bar",
            "labels": [str(i) for i in range(len(cfs))],
            "datasets": [{"label": "Oylik model", "data": cfs}],
        }

    if action == "saas_extended":
        mode = result.get("mode")
        if mode == "rule40":
            return {
                "type": "bar",
                "labels": ["O'sish %", "Marja %", "Rule of 40"],
                "datasets": [{
                    "data": [
                        result.get("revenue_growth_percent", 0),
                        result.get("profit_margin_percent", 0),
                        result.get("rule_of_40_score", 0),
                    ],
                    "backgroundColor": ["#38bdf8", "#a78bfa", "#22c55e"],
                }],
            }
        if mode == "nrr":
            nrr = float(result.get("nrr_ratio", 1))
            # 2 dan oshib ketsa ham doughnutni 2 da ushlab turamiz —
            # vizual jihatdan tushunarliroq
            capped = min(nrr, 2)
            return {
                "type": "doughnut",
                "labels": ["NRR (nisbati)", "Qolgan"],
                "datasets": [{
                    "data": [capped, max(0, 2 - capped)],
                    "backgroundColor": ["#22c55e", "#e2e8f0"],
                }],
            }
        if mode == "unit":
            return {
                "type": "bar",
                "labels": ["Kontributsiya/oy", "Sof (fixed dan keyin)"],
                "datasets": [{
                    "data": [
                        result.get("monthly_contribution_usd", 0),
                        result.get("monthly_net_after_fixed_usd", 0),
                    ],
                    "backgroundColor": ["#0ea5e9", "#8b5cf6"],
                }],
            }

    if action == "risk_register":
        rs = result.get("risks", [])
        return {
            "type": "bar",
            "labels": [r["name"][:20] for r in rs],  # uzun nomlarni qisqartiramiz
            "datasets": [{
                "label": "p×i",
                "data": [r["score"] for r in rs],
                "backgroundColor": "#ef4444",
            }],
        }

    if action == "fx_fetch" and result.get("ok"):
        return {
            "type": "bar",
            "labels": [f"1 USD = {result.get('target')}"],
            "datasets": [{
                "label": "Kurs",
                "data": [result.get("rate", 0)],
                "backgroundColor": "#0284c7",
            }],
        }

    if action == "market_benchmark" and result.get("ok"):
        # API yangidan eskigacha beradi — chartda chapdan o'ngga eskidan yangiga
        # bo'lishi yaxshiroq, lekin hozir tartibni o'zgartirmasdan ham yetadi.
        series = result.get("series") or []
        usable = [(x["year"], x["value"]) for x in series if x.get("value") is not None][:8]
        if not usable:
            return {"type": "none"}
        labs = [str(y) for y, _ in usable]
        vals = [v for _, v in usable]
        return {
            "type": "line",
            "labels": labs,
            "datasets": [{"label": "GDP o'sishi %", "data": vals}],
        }

    return {"type": "none"}
