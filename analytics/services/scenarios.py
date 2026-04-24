"""Uch ssenariy — bazaviy / optimistik / pessimistik — NPV bo'yicha solishtirish.

Soddalashtirilgan logika: tushum ko'paytuvchisi musbat CF larga, xarajat
ko'paytuvchisi salbiy CF larga qo'llaniladi. Bu modellashtirish "kichik
hajmdagi loyiha"lar uchun yaxshi ishlaydi; juda murakkab struktura uchun
har bir yilning daromad/xarajatini alohida kiritish ma'qulroq.
"""
from typing import Any

from analytics.services.core_finance import compute_classic_metrics


def _scale_cfs(cfs: list[float], rev_mult: float, cost_mult: float) -> list[float]:
    """Musbat CF tushum, salbiy CF xarajat deb taxmin qilamiz."""
    out: list[float] = []
    for cf in cfs:
        if cf >= 0:
            out.append(cf * rev_mult)
        else:
            out.append(cf * cost_mult)
    return out


def compare_scenarios(
    *,
    initial_investment: float,
    discount_rate: float,
    salvage_value: float,
    base_cashflows: list[float],
    opt_revenue_mult: float = 1.15,
    opt_cost_mult: float = 0.95,
    pes_revenue_mult: float = 0.85,
    pes_cost_mult: float = 1.08,
) -> dict[str, Any]:
    if not base_cashflows:
        raise ValueError("Bazaviy pul oqimi kerak")

    common = dict(
        initial_investment=initial_investment,
        discount_rate=discount_rate,
        salvage_value=salvage_value,
    )

    base = compute_classic_metrics(annual_cashflows=base_cashflows, **common)
    opt = compute_classic_metrics(
        annual_cashflows=_scale_cfs(base_cashflows, opt_revenue_mult, opt_cost_mult),
        **common,
    )
    pes = compute_classic_metrics(
        annual_cashflows=_scale_cfs(base_cashflows, pes_revenue_mult, pes_cost_mult),
        **common,
    )

    return {
        "base": {"npv": base["npv"], "irr": base["irr"], "label": "Bazaviy"},
        "optimistic": {"npv": opt["npv"], "irr": opt["irr"], "label": "Optimistik"},
        "pessimistic": {"npv": pes["npv"], "irr": pes["irr"], "label": "Pessimistik"},
        "multipliers": {
            "optimistic": {"revenue": opt_revenue_mult, "cost": opt_cost_mult},
            "pessimistic": {"revenue": pes_revenue_mult, "cost": pes_cost_mult},
        },
    }
