"""ROHC — Return On Human Capital.

Inson kapitalining samaradorligi: eksport tushumining ish haqi fondiga nisbati.
BPO sanoatida bu Hindiston/Polsha kabi mamlakatlarda 1.5–2.5 oralig'ida bo'ladi.
"""
from typing import Any


def compute_rohc(
    *,
    annual_export_revenue_usd: float,
    annual_payroll_usd: float,
    headcount: int,
    benchmark_revenue_per_payroll: float | None = None,
) -> dict[str, Any]:
    if annual_payroll_usd <= 0:
        raise ValueError("annual_payroll_usd musbat bo'lishi kerak")
    if headcount <= 0:
        raise ValueError("headcount musbat bo'lishi kerak")

    rohc = annual_export_revenue_usd / annual_payroll_usd
    revenue_per_employee = annual_export_revenue_usd / headcount

    # Benchmark berilgan bo'lsa, nisbiy ko'rsatkichni ham qaytaramiz
    relative = None
    if benchmark_revenue_per_payroll is not None and benchmark_revenue_per_payroll > 0:
        relative = rohc / benchmark_revenue_per_payroll

    return {
        "rohc_ratio": float(rohc),
        "export_revenue_per_employee_usd": float(revenue_per_employee),
        "benchmark_payroll_efficiency": (
            float(benchmark_revenue_per_payroll)
            if benchmark_revenue_per_payroll is not None
            else None
        ),
        "relative_to_benchmark": float(relative) if relative is not None else None,
    }
