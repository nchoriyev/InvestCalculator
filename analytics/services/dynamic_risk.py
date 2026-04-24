"""Sof eksport foydasi (NEB) — kurs o'zgarishi va xalqaro komissiya bilan."""
from typing import Any


def compute_net_export_benefit(
    *,
    export_revenue_usd: float,
    international_fee_rate: float,
    local_costs_in_local_currency: float,
    exchange_rate_local_per_usd: float,
    delta_e: float = 0.0,
) -> dict[str, Any]:
    """USDdagi tushum + komissiya - mahalliy xarajat (kursga keltirilgan).

    delta_e — mahalliy valyutaning USD ga nisbatan qancha
    kuchayganini bildiradi. Masalan, 0.05 = 5% kuchayish.
    Mahalliy valyuta kuchaysa, USDdagi xarajat ekvivalenti
    tabiiy ravishda kichrayadi (eksportchi uchun yaxshi yangilik).
    """
    if not 0 <= international_fee_rate < 1:
        raise ValueError("international_fee_rate [0, 1) bo'lishi kerak")
    if exchange_rate_local_per_usd <= 0:
        raise ValueError("exchange_rate_local_per_usd musbat bo'lishi kerak")

    # Komissiyadan keyingi sof tushum
    net_usd_inflow = export_revenue_usd * (1.0 - international_fee_rate)

    effective_rate = exchange_rate_local_per_usd * (1.0 + delta_e)
    local_cost_usd = local_costs_in_local_currency / effective_rate

    return {
        "net_export_benefit_usd": float(net_usd_inflow - local_cost_usd),
        "net_usd_inflow_after_fees": float(net_usd_inflow),
        "local_costs_usd_equivalent": float(local_cost_usd),
        "delta_e_applied": float(delta_e),
        "effective_rate_local_per_usd": float(effective_rate),
    }
