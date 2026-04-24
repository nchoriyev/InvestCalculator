"""Barqarorlik indeksi (0..100) — bitta raqamga sig'dirilgan umumiy baholash.

Asosiy g'oya: Monte-Carlo muvaffaqiyat ehtimoli yuqori va kompozit risk
past bo'lsa, indeks shuncha katta. ARIMA ishlatilgan bo'lsa, model
ishonchliligi biroz yaxshiroq deb qabul qilamiz va kichik bonus beramiz.
"""
from typing import Any

_ARIMA_BONUS = 5.0


def compute_sustainability_index(
    *,
    monte_carlo_success_probability: float,
    composite_risk_score: float,
    forecast_method: str,
) -> dict[str, Any]:
    if not 0 <= monte_carlo_success_probability <= 1:
        raise ValueError("monte_carlo_success_probability 0..1")
    if not 0 <= composite_risk_score <= 1:
        raise ValueError("composite_risk_score 0..1")

    base = 100.0 * monte_carlo_success_probability * (1.0 - composite_risk_score)
    bonus = _ARIMA_BONUS if forecast_method == "arima" else 0.0
    index = min(100.0, max(0.0, base + bonus))

    return {
        "sustainability_index": float(index),
        "components": {
            "success_weight": float(monte_carlo_success_probability),
            "risk_discount": float(1.0 - composite_risk_score),
            "forecast_bonus": bonus,
        },
    }
