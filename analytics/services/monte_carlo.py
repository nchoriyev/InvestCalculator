"""Monte-Carlo: NPV taqsimoti va muvaffaqiyat ehtimoli.

Daromad/xarajat normal taqsimotdan, har yili kichik trend bilan o'sadi.
Buni "soddalashtirilgan" model deb atash mumkin — agar real loyiha uchun
ishlatilsa, distributionni log-normal yoki triangularga o'zgartirish mantiqliroq
bo'lishi mumkin (lekin demo uchun hozirgi varianti yetarli).
"""
from __future__ import annotations

from typing import Any

import numpy as np


def run_monte_carlo(
    *,
    n_simulations: int = 10_000,
    initial_investment: float,
    years: int = 5,
    discount_rate: float = 0.12,
    revenue_mean: float,
    revenue_std: float,
    cost_mean: float,
    cost_std: float,
    revenue_growth_mean: float = 0.05,
    cost_growth_mean: float = 0.04,
    random_seed: int | None = None,
) -> dict[str, Any]:
    if n_simulations < 100:
        # 100 dan kam simulyatsiyada histogramma deyarli ma'no bermaydi
        raise ValueError("n_simulations kamida 100 bo'lishi kerak")

    rng = np.random.default_rng(random_seed)

    # Har bir simulyatsiya uchun NPV ni vektor sifatida yig'amiz —
    # bu loop ichida har gal yangi massiv yaratishdan tezroq.
    npvs = np.zeros(n_simulations)

    for year in range(1, years + 1):
        trend_r = (1.0 + revenue_growth_mean) ** (year - 1)
        trend_c = (1.0 + cost_growth_mean) ** (year - 1)

        rev = rng.normal(revenue_mean * trend_r, revenue_std, n_simulations)
        cst = rng.normal(cost_mean * trend_c, cost_std, n_simulations)

        cf_year = rev - cst
        npvs += cf_year / (1.0 + discount_rate) ** year

    npvs -= initial_investment

    # Histogramma uchun bin'lar — 48 ta yetarli, ko'p bo'lsa shovqinli ko'rinadi
    counts, bin_edges = np.histogram(npvs, bins=48)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    p5 = float(np.percentile(npvs, 5))
    # CVaR — pastki 5% ssenariylar bo'yicha o'rtacha (tail risk)
    tail = npvs[npvs <= p5]
    cvar_95 = float(np.mean(tail)) if tail.size else p5

    return {
        "n_simulations": n_simulations,
        "success_probability": float(np.mean(npvs > 0)),
        "npv_mean": float(np.mean(npvs)),
        "npv_std": float(np.std(npvs)),
        "npv_p5": p5,
        "npv_p50": float(np.percentile(npvs, 50)),
        "npv_p95": float(np.percentile(npvs, 95)),
        "cvar_95_loss": cvar_95,
        "histogram": {
            "labels": [float(x) for x in bin_centers],
            "counts": [float(x) for x in counts],
        },
    }
