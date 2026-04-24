"""Eksport hajmi bashorati — chiziqli regressiya yoki ARIMA orqali.

Yetarli ma'lumot bo'lsa (>= 8 nuqta) ARIMA, aks holda oddiy chiziqli trend.
Statsmodels o'rnatilmagan bo'lsa, ham xato bermasdan chiziqliga o'tib ketadi —
shu bilan deployment muhitiga talablar yumshoqroq bo'ladi.
"""
from __future__ import annotations

from typing import Any

import numpy as np

# Statsmodels og'ir kutubxona — har doim ham bo'lavermaydi
try:
    from statsmodels.tsa.arima.model import ARIMA
except Exception:  # pragma: no cover
    ARIMA = None


def forecast_export_volume(
    history_usd: list[float],
    *,
    horizon_months: int = 12,
    prefer_arima: bool = True,
    arima_order: tuple[int, int, int] = (1, 1, 1),
) -> dict[str, Any]:
    """history_usd — oylar bo'yicha eksport tushumi (USD).

    Kamida 6 nuqta tavsiya etiladi, lekin 3 ham ishlaydi.
    """
    if len(history_usd) < 3:
        raise ValueError("history_usd kamida 3 ta kuzatuv bo'lishi kerak")

    y = np.array(history_usd, dtype=float)
    n = len(y)
    t = np.arange(n, dtype=float)

    # Chiziqli regressiya (y = a + b*t) — har doim hisoblaymiz, fallback uchun
    A = np.vstack([np.ones(n), t]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    a, b = float(coef[0]), float(coef[1])

    linear_forecast = [a + b * (n - 1 + h) for h in range(1, horizon_months + 1)]

    # ARIMA — agar shartlar mos kelsa
    arima_forecast: list[float] | None = None
    arima_error: str | None = None

    if prefer_arima and ARIMA is not None and n >= 8:
        try:
            fit = ARIMA(y, order=arima_order).fit()
            fc = fit.forecast(steps=horizon_months)
            arima_forecast = [float(x) for x in fc]
        except Exception as e:  # pragma: no cover
            # Konvergensiya muvaffaqiyatsiz bo'lishi mumkin —
            # bunday holatda chiziqli trend yetarli
            arima_error = str(e)

    chosen = "arima" if arima_forecast else "linear_regression"
    series_out = arima_forecast or linear_forecast

    return {
        "method_used": chosen,
        "linear_trend": {"intercept": a, "slope": b},
        "forecast_next_months_usd": series_out,
        "linear_forecast_next_months_usd": linear_forecast,
        "arima_forecast_next_months_usd": arima_forecast,
        "arima_error": arima_error,
        "horizon_months": horizon_months,
    }
