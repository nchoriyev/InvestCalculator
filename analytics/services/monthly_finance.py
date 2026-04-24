"""Oylik DCF: yillik diskont stavkasini oylik ekvivalentga aylantirib hisoblash.

Yillik modeldan farqi — mavsumiylik va birinchi oylar likvidligini aniqroq
ko'rsatadi. Lekin natija unchalik katta farq qilmasa, yillik modelni ham
birga qaytaramiz (annual_equivalent_simplified_npv).
"""
from typing import Any

from analytics.services.core_finance import compute_classic_metrics, irr


def annual_to_monthly_rate(annual_discount: float) -> float:
    # Geometric o'rtacha: (1+r_y) = (1+r_m)^12
    return (1.0 + annual_discount) ** (1.0 / 12.0) - 1.0


def compute_monthly_dcf(
    *,
    initial_investment: float,
    monthly_cashflows: list[float],
    annual_discount_rate: float,
) -> dict[str, Any]:
    """initial_investment t=0 da chiqim sifatida (musbat raqam beriladi).

    monthly_cashflows: 1-oydan boshlab oylik net CF (ijobiy = tushum,
    salbiy = sof xarajat). Hech qanday yillik o'rtachalashtirish ishlatilmaydi.
    """
    if not monthly_cashflows:
        raise ValueError("Oylik pul oqimlari kerak")

    inv = abs(initial_investment)
    r_m = annual_to_monthly_rate(annual_discount_rate)

    # Diskontlangan PV
    pv = 0.0
    for t, cf in enumerate(monthly_cashflows, start=1):
        pv += cf / (1.0 + r_m) ** t
    npv_m = pv - inv

    # Oylik IRR ni topib, yillikka aylantiramiz
    cfs_for_irr = [-inv] + list(monthly_cashflows)
    irr_m = irr(cfs_for_irr)
    irr_annual = (1.0 + irr_m) ** 12 - 1.0 if irr_m is not None else None

    # Payback (oylarda)
    payback_months: float | None = None
    cumulative = -inv
    for i, cf in enumerate(monthly_cashflows, start=1):
        cumulative += cf
        if cumulative >= 0 and payback_months is None:
            prev_cum = cumulative - cf
            frac = -prev_cum / cf if cf else 0.0
            payback_months = (i - 1) + max(0.0, min(1.0, frac))
            break

    # Sodda yillik ekvivalent — solishtirish uchun (oylar yillarga taqsimlanadi)
    n_years = max(1, (len(monthly_cashflows) + 11) // 12)
    approx_annual_cf = sum(monthly_cashflows) / n_years if n_years else 0.0
    annual_equiv_npv = compute_classic_metrics(
        initial_investment=initial_investment,
        annual_cashflows=[approx_annual_cf] * n_years,
        discount_rate=annual_discount_rate,
        salvage_value=0.0,
    )["npv"]

    return {
        "npv_monthly_model_usd": float(npv_m),
        "monthly_discount_rate": float(r_m),
        "annual_discount_rate_used": float(annual_discount_rate),
        "irr_monthly": float(irr_m) if irr_m is not None else None,
        "irr_annualized_from_monthly": float(irr_annual) if irr_annual is not None else None,
        "payback_period_months": float(payback_months) if payback_months is not None else None,
        "months_modeled": len(monthly_cashflows),
        "chart_monthly_cfs": [-inv] + list(monthly_cashflows),
        "annual_equivalent_simplified_npv": float(annual_equiv_npv),
    }
