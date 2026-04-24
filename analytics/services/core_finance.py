"""Klassik investitsiya o'lchovlari: NPV, ROI, IRR, payback davri.

Hammasi bitta joyga to'plangan, chunki dashboard'ning qariyb hamma joyida
shu funksiyalar chaqiriladi (sensitivity, scenarios, monthly DCF va h.k.).
"""
from typing import Any

from scipy import optimize


def npv(discount_rate: float, cashflows: list[float]) -> float:
    """Diskontlangan pul oqimlarining yig'indisi.

    Konvensiya: cashflows[0] odatda manfiy (boshlang'ich investitsiya),
    qolganlari yillik (yoki davriy) net CF.
    """
    total = 0.0
    for i, cf in enumerate(cashflows):
        total += cf / (1.0 + discount_rate) ** i
    return float(total)


def irr(cashflows: list[float]) -> float | None:
    """IRR — NPV(r) = 0 bo'ladigan stavka.

    `brentq` orqali topamiz; agar oraliqda ildiz topilmasa (masalan,
    barcha CF bir ishorada bo'lsa) — None qaytaramiz, exception emas.
    Bu chaqiruvchi tomonda hayotni osonlashtiradi.
    """
    def _npv_at(r: float) -> float:
        return sum(cf / (1.0 + r) ** i for i, cf in enumerate(cashflows))

    try:
        # -99.99% dan +1000% gacha — amaliyotda ortig'i kerak emas
        return float(optimize.brentq(_npv_at, -0.9999, 10.0, maxiter=200))
    except ValueError:
        return None


def compute_classic_metrics(
    *,
    initial_investment: float,
    annual_cashflows: list[float],
    discount_rate: float,
    salvage_value: float = 0.0,
) -> dict[str, Any]:
    # initial investitsiyani har holda manfiy belgida joylashtiramiz
    inv = abs(initial_investment)
    cfs = [-inv] + list(annual_cashflows)

    # salvage qiymatini eng oxirgi yilga qo'shib qo'yamiz
    if salvage_value and annual_cashflows:
        cfs[-1] = annual_cashflows[-1] + salvage_value

    net_present_value = npv(discount_rate, cfs)

    # Oddiy ROI — vaqt qiymatini hisobga olmaydi, lekin ko'rgazma uchun foydali
    total_profit = sum(annual_cashflows) + salvage_value - inv
    roi_simple = total_profit / inv if inv else 0.0

    irr_val = irr(cfs)

    # Payback: kumulyativ CF musbatga aylangan birinchi yil + chiziqli interpolyatsiya
    payback_period: float | None = None
    cumulative = -inv
    for year_idx, cf in enumerate(annual_cashflows, start=1):
        cumulative += cf
        if cumulative >= 0 and payback_period is None:
            prev_cum = cumulative - cf
            frac = -prev_cum / cf if cf else 0.0
            # frac ba'zan suzuvchi nuqta xatolari tufayli 0..1 dan chiqib ketishi mumkin
            payback_period = (year_idx - 1) + max(0.0, min(1.0, frac))
            break

    return {
        "npv": float(net_present_value),
        "roi_simple": float(roi_simple),
        "irr": float(irr_val) if irr_val is not None else None,
        "payback_period_years": float(payback_period) if payback_period is not None else None,
        "cashflows_used": cfs,
    }
