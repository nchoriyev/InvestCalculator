"""Sensitivlik tahlili — bitta parametrni ±foiz bilan o'zgartirib NPV ga ta'sirini kuzatish."""
from typing import Any

from analytics.services.core_finance import compute_classic_metrics

# Qaysi parametrlar bo'yicha sensitivlikni qo'llab-quvvatlaymiz
_SUPPORTED = {"discount_rate", "first_cf", "all_cf"}


def run_sensitivity_annual(
    *,
    initial_investment: float,
    annual_cashflows: list[float],
    discount_rate: float,
    salvage_value: float,
    parameter: str,
    steps_pct: list[float],
) -> dict[str, Any]:
    """parameter — yuqoridagi to'plamdan biri.

    steps_pct — masalan [-20, -10, 0, 10, 20]. 0 nuqtasi bazaviy
    NPV ga teng bo'ladi (foydali sanity-check).
    """
    if parameter not in _SUPPORTED:
        raise ValueError("parameter noto'g'ri")

    base = compute_classic_metrics(
        initial_investment=initial_investment,
        annual_cashflows=list(annual_cashflows),
        discount_rate=discount_rate,
        salvage_value=salvage_value,
    )
    base_npv = base["npv"]

    rows = []
    for pct in steps_pct:
        m = 1.0 + pct / 100.0

        dr = discount_rate * m if parameter == "discount_rate" else discount_rate
        cfs = list(annual_cashflows)

        if parameter == "first_cf" and cfs:
            cfs[0] = cfs[0] * m
        elif parameter == "all_cf":
            cfs = [c * m for c in cfs]

        # all_cf rejimida salvage qiymatini nolga tushiramiz, aks holda
        # ikki marotaba o'lchovga uchrashi mumkin (chunki oxirgi yil CF si
        # ham allaqachon ko'paytirilgan)
        sv = 0.0 if parameter == "all_cf" else salvage_value

        out = compute_classic_metrics(
            initial_investment=initial_investment,
            annual_cashflows=cfs,
            discount_rate=dr,
            salvage_value=sv,
        )
        rows.append({
            "step_pct": pct,
            "npv": out["npv"],
            "delta_vs_base": out["npv"] - base_npv,
        })

    return {
        "parameter": parameter,
        "base_npv": base_npv,
        "steps": rows,
        "base_irr": base.get("irr"),
    }
