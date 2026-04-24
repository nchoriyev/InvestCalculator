"""IT Park rezidentligi: imtiyozli soliq stavkasi va undan kelib chiqadigan tax shield.

Standart stavka ~15% deb olingan, IT Park rezidentlari uchun esa odatda
yarmiga yaqin (7.5%). Stavkalar vaqt o'tishi bilan o'zgarib turishi mumkin —
yangi qonun chiqsa, default qiymatlarni shu yerda yangilab qo'yish kifoya.
"""
from typing import Any


def compute_tax_shield(
    *,
    taxable_profit_usd: float,
    income_tax_rate_without_incentive: float = 0.15,
    income_tax_rate_it_park: float = 0.075,
) -> dict[str, Any]:
    if taxable_profit_usd < 0:
        # Foyda manfiy bo'lsa, soliq hisobi murakkablashadi (zarar tashlash, va h.k.) —
        # demo doirasida hozircha bunga yo'l qo'ymaymiz.
        raise ValueError("taxable_profit_usd manfiy bo'lmasligi kerak (demo)")

    tax_without = taxable_profit_usd * income_tax_rate_without_incentive
    tax_with = taxable_profit_usd * income_tax_rate_it_park
    shield = tax_without - tax_with

    return {
        "tax_without_incentive_usd": float(tax_without),
        "tax_with_it_park_usd": float(tax_with),
        "tax_shield_usd": float(shield),
        "net_profit_after_tax_without_usd": float(taxable_profit_usd - tax_without),
        "net_profit_after_tax_with_it_park_usd": float(taxable_profit_usd - tax_with),
        "rates": {
            "without_incentive": income_tax_rate_without_incentive,
            "it_park": income_tax_rate_it_park,
        },
    }
