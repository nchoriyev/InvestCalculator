"""SaaS metrikalari: LTV, CAC, LTV:CAC.

Formulalar soddalashtirilgan ko'rinishda — chuqurroq modellashtirish uchun
oylik kohortalar va expansion/contraction MRR alohida hisoblanishi kerak
(buning uchun saas_extended.py ga qarang).
"""
from typing import Any


def compute_saas_metrics(
    *,
    arpu_monthly_usd: float,
    gross_margin: float,
    monthly_churn_rate: float,
    marketing_spend_usd: float,
    new_customers: int,
    avg_customer_lifetime_months: float | None = None,
) -> dict[str, Any]:
    # Kirishlarni darhol tekshiramiz — pastdagi formulalar 0 ga bo'lishdan azob chekmasin
    if monthly_churn_rate <= 0 or monthly_churn_rate >= 1:
        raise ValueError("monthly_churn_rate (0, 1) oralig'ida bo'lishi kerak")
    if new_customers <= 0:
        raise ValueError("new_customers musbat bo'lishi kerak")
    if not 0 <= gross_margin <= 1:
        raise ValueError("gross_margin 0..1 oralig'ida")

    # Mijozning kutilayotgan umri: agar berilmagan bo'lsa, churn ning teskarisi
    if avg_customer_lifetime_months is None:
        lifetime_m = 1.0 / monthly_churn_rate
    else:
        lifetime_m = avg_customer_lifetime_months

    ltv = arpu_monthly_usd * gross_margin * lifetime_m
    cac = marketing_spend_usd / new_customers

    # Marketing budget 0 bo'lishi mumkin (organik o'sish) — bunda nisbatni hisoblamaymiz
    ltv_cac = ltv / cac if cac > 0 else None

    return {
        "ltv_usd": float(ltv),
        "cac_usd": float(cac),
        "monthly_churn_rate": monthly_churn_rate,
        "implied_lifetime_months": float(lifetime_m),
        "ltv_cac_ratio": float(ltv_cac) if ltv_cac is not None else None,
    }
