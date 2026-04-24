"""Risk matritsasi: mamlakat, valyuta va kiber xavf koeffitsiyentlarini birlashtiradi.

Vaznlar: country_risk 40%, fx_volatility 35%, cyber 25% — bu raqamlar
xalqaro IT-eksport bo'yicha empirik tahlilga asoslangan,
lekin xohlasangiz `weights` argumentidan boshqa kombinatsiya berishingiz mumkin.
"""
from typing import Any

# Default vaznlar — ekspert baholash bilan tanlangan
_DEFAULT_WEIGHTS = (0.40, 0.35, 0.25)


def compute_risk_matrix(
    *,
    country_risk_score: float,
    fx_volatility: float,
    cyber_cost_share: float,
    base_npv: float = 1.0,
    weights: tuple[float, float, float] | None = None,
) -> dict[str, Any]:
    # Hammasi 0..1 oralig'ida bo'lishi shart
    inputs = {
        "country_risk_score": country_risk_score,
        "fx_volatility": fx_volatility,
        "cyber_cost_share": cyber_cost_share,
    }
    for name, v in inputs.items():
        if not 0 <= v <= 1:
            raise ValueError(f"{name} 0..1 oralig'ida bo'lishi kerak")

    w1, w2, w3 = weights or _DEFAULT_WEIGHTS
    # Vaznlar yig'indisini 1 ga normallashtirib qo'yamiz —
    # foydalanuvchi (0.5, 0.5, 0.5) kabi narsa bersa ham mantiq buzilmasin
    wsum = w1 + w2 + w3
    w1, w2, w3 = w1 / wsum, w2 / wsum, w3 / wsum

    composite = (
        w1 * country_risk_score
        + w2 * fx_volatility
        + w3 * cyber_cost_share
    )
    adjusted_npv = base_npv * (1.0 - composite)

    heatmap = [
        {"factor": "country_risk", "value": country_risk_score, "weight": w1},
        {"factor": "fx_volatility", "value": fx_volatility, "weight": w2},
        {"factor": "cybersecurity_cost", "value": cyber_cost_share, "weight": w3},
    ]

    return {
        "composite_risk_score": float(composite),
        "adjusted_npv_multiplier": float(1.0 - composite),
        "adjusted_npv": float(adjusted_npv),
        "heatmap_rows": heatmap,
    }
