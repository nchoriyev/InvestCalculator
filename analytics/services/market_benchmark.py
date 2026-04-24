"""Jahon Banki ochiq API — mamlakatlar bo'yicha makro ko'rsatkichlar.

Default indikator — real GDP o'sishi (NY.GDP.MKTP.KD.ZG). Boshqa kodlarni
https://data.worldbank.org/indicator dan qarab ishlatish mumkin.
"""
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

_DEFAULT_INDICATOR = "NY.GDP.MKTP.KD.ZG"  # real GDP growth (annual %)


def fetch_world_bank_indicator(
    country_iso2: str = "UZ",
    indicator: str = _DEFAULT_INDICATOR,
    per_page: int = 5,
    timeout: float = 10.0,
) -> dict[str, Any]:
    if requests is None:
        return {"ok": False, "error": "requests yo'q", "values": []}

    url = (
        f"https://api.worldbank.org/v2/country/{country_iso2}"
        f"/indicator/{indicator}?format=json&per_page={per_page}"
    )

    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        data = r.json()

        # Jahon Banki APIsi har doim 2 elementli ro'yxat qaytaradi:
        # [metadata, rows]. Birinchisi bizga juda kerak emas.
        if not data or len(data) < 2:
            return {"ok": False, "error": "Bo'sh javob", "values": []}

        rows = data[1] or []
        series = [
            {"year": row.get("date"), "value": row.get("value")}
            for row in rows
        ]

        # API odatda yangidan eskigacha tartiblab beradi —
        # shuning uchun [0] eng so'nggi yil hisoblanadi.
        latest = None
        if series and series[0].get("value") is not None:
            latest = series[0]["value"]

        return {
            "ok": True,
            "indicator": indicator,
            "country": country_iso2,
            "description": "GDP real growth (annual %)",
            "series": series,
            "latest_growth_pct": latest,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "values": []}
