"""USD asosidagi valyuta kursi — bir nechta tashqi API orqali."""
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]


# Bepul / API-keysiz manbalar. exchangerate.host ba'zan tushib qoladi —
# shu sababli ikkinchi backup sifatida open.er-api ham qo'shilgan.
_PROVIDERS = (
    "https://api.exchangerate.host/latest?base=USD&symbols={cur}",
    "https://open.er-api.com/v6/latest/USD",
)


def fetch_rate_usd_to(target_currency: str = "UZS", timeout: float = 8.0) -> dict[str, Any]:
    target_currency = target_currency.upper().strip()

    if requests is None:
        return {
            "ok": False,
            "error": "requests kutubxonasi o'rnatilmagan",
            "rate": None,
        }

    last_err = ""
    for tmpl in _PROVIDERS:
        url = tmpl.format(cur=target_currency)
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            data = r.json()

            # exchangerate.host javob formati
            if "rates" in data and target_currency in data["rates"]:
                return {
                    "ok": True,
                    "base": "USD",
                    "target": target_currency,
                    "rate": float(data["rates"][target_currency]),
                    "source": url.split("/")[2],
                    "raw_date": data.get("date") or data.get("time_last_update_utc"),
                }

            # open.er-api javob formati biroz boshqacha
            if data.get("result") == "success" and "rates" in data:
                rates = data["rates"]
                if target_currency in rates:
                    return {
                        "ok": True,
                        "base": "USD",
                        "target": target_currency,
                        "rate": float(rates[target_currency]),
                        "source": "open.er-api.com",
                        "raw_date": None,
                    }
        except Exception as e:  # pragma: no cover
            # Birinchi manba ishlamasa, keyingisiga o'tamiz
            last_err = str(e)
            continue

    return {
        "ok": False,
        "error": last_err or "Kurs olinmadi",
        "rate": None,
        "target": target_currency,
    }
