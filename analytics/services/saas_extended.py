"""SaaS metrikalarining kengaytirilgan to'plami: Rule of 40, NRR, unit economics."""
from typing import Any


def _to_percent(x: float) -> float:
    """0.25 va 25 — ikkalasini ham foiz sifatida talqin qilish.

    Foydalanuvchilar formani har xil to'ldirishadi: kimdir 0.25 yozadi,
    kimdir 25. Soddagina chegara: 1.5 dan kichik bo'lsa "fraksiya" deb hisoblaymiz.
    """
    return x * 100 if x <= 1.5 else x


def rule_of_40(*, revenue_growth_yoy: float, profit_margin: float) -> dict[str, Any]:
    g = _to_percent(revenue_growth_yoy)
    m = _to_percent(profit_margin)
    score = g + m

    if score >= 40:
        label = "yaxshi"
    elif score >= 25:
        label = "o'rta"
    else:
        label = "past"

    return {
        "revenue_growth_percent": float(g),
        "profit_margin_percent": float(m),
        "rule_of_40_score": float(score),
        "interpretation": label,
    }


def net_revenue_retention(
    *,
    starting_mrr: float,
    ending_mrr: float,
    churned_mrr: float,
    expansion_mrr: float,
) -> dict[str, Any]:
    if starting_mrr <= 0:
        raise ValueError("starting_mrr musbat bo'lishi kerak")

    nrr = (ending_mrr - churned_mrr + expansion_mrr) / starting_mrr

    if nrr >= 1.2:
        label = "a'lo"
    elif nrr >= 1.0:
        label = "yaxshi"
    else:
        label = "past"

    return {
        "nrr_ratio": float(nrr),
        "nrr_percent": float((nrr - 1) * 100),
        "interpretation": label,
    }


def unit_economics(
    *,
    price_per_unit_usd: float,
    variable_cost_per_unit_usd: float,
    units_per_month: float,
    fixed_cost_monthly_usd: float = 0.0,
) -> dict[str, Any]:
    cm = price_per_unit_usd - variable_cost_per_unit_usd
    cm_ratio = cm / price_per_unit_usd if price_per_unit_usd else 0.0

    monthly_contribution = cm * units_per_month
    monthly_net = monthly_contribution - fixed_cost_monthly_usd

    return {
        "contribution_margin_per_unit": float(cm),
        "contribution_margin_ratio": float(cm_ratio),
        "monthly_contribution_usd": float(monthly_contribution),
        "monthly_net_after_fixed_usd": float(monthly_net),
    }
