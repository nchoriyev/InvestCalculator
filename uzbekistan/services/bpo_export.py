"""O'zbekiston BPO loyihalari uchun eksport rentabelligi tahlili.

Asosiy savol: ish haqi va boshqa xarajatlardan keyin qancha foyda qoladi va
IT Park imtiyozi bu foydani qancha oshiradi?
"""
from typing import Any

from uzbekistan.services.it_park import compute_tax_shield


def compute_bpo_export_profitability(
    *,
    annual_export_revenue_usd: float,
    annual_payroll_usd: float,
    other_operating_costs_usd: float = 0.0,
    income_tax_rate_without_incentive: float = 0.15,
    income_tax_rate_it_park: float = 0.075,
) -> dict[str, Any]:
    ebit = annual_export_revenue_usd - annual_payroll_usd - other_operating_costs_usd

    # EBIT manfiy bo'lsa, soliq hisobi alohida masala (zararni tashlash va h.k.).
    # Hozir esa shunchaki nol soliq bilan qaytaramiz va foydalanuvchini ogohlantiramiz.
    if ebit < 0:
        return {
            "ebit_usd": float(ebit),
            "note": "EBIT manfiy — soliq hisobi soddalashtirilgan",
            "tax_shield": compute_tax_shield(taxable_profit_usd=0.0),
        }

    tax_block = compute_tax_shield(
        taxable_profit_usd=ebit,
        income_tax_rate_without_incentive=income_tax_rate_without_incentive,
        income_tax_rate_it_park=income_tax_rate_it_park,
    )

    # Ikkala holat uchun eksport tushumiga nisbatan sof rentabellik
    rev = annual_export_revenue_usd or 0.0
    if rev:
        roi_with_it = tax_block["net_profit_after_tax_with_it_park_usd"] / rev
        roi_without = tax_block["net_profit_after_tax_without_usd"] / rev
    else:
        roi_with_it = 0.0
        roi_without = 0.0

    return {
        "annual_export_revenue_usd": float(annual_export_revenue_usd),
        "annual_payroll_usd": float(annual_payroll_usd),
        "other_operating_costs_usd": float(other_operating_costs_usd),
        "ebit_usd": float(ebit),
        "export_margin_before_tax_usd": float(ebit),
        "tax_shield_analysis": tax_block,
        "roi_on_export_revenue_with_it_park": float(roi_with_it),
        "roi_on_export_revenue_without_incentive": float(roi_without),
    }
