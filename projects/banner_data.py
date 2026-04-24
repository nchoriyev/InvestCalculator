"""Saytning yuqori paneli: sana/vaqt (Toshkent), ob-havo va valyuta kurslari.

Tashqi APIlar tushib qolsa, banner ham o'lib qolmasligi kerak —
shuning uchun har bir chaqiriq alohida try/except bilan o'ralgan.
"""
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import requests

from analytics.services.fx_service import fetch_rate_usd_to

_TZ = ZoneInfo("Asia/Tashkent")
# Hafta kunlarining qisqa o'zbekcha shakli (Du, Se, ..., Ya)
_WEEKDAYS_UZ = ("Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya")


def _weather_tashkent() -> dict[str, Any]:
    """open-meteo dan joriy harorat. API kalitsiz, sodda."""
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 41.3111,
                "longitude": 69.2797,
                "current": "temperature_2m,weather_code",
                "timezone": "Asia/Tashkent",
            },
            timeout=5,
        )
        r.raise_for_status()
        cur = (r.json() or {}).get("current") or {}

        return {
            "ok": True,
            "temp_c": cur.get("temperature_2m"),
            "code": cur.get("weather_code"),
            "city": "Toshkent",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_banner_data() -> dict[str, Any]:
    now = datetime.now(_TZ)

    uzs = fetch_rate_usd_to("UZS")
    eur = fetch_rate_usd_to("EUR")
    weather = _weather_tashkent()

    if weather.get("ok") and weather.get("temp_c") is not None:
        temp_txt = f"{float(weather['temp_c']):.0f}°C"
    else:
        temp_txt = "—"

    fx_lines: list[str] = []
    if uzs.get("ok") and uzs.get("rate"):
        fx_lines.append(f"1 USD = {float(uzs['rate']):,.2f} UZS")
    if eur.get("ok") and eur.get("rate"):
        fx_lines.append(f"1 USD = {float(eur['rate']):.4f} EUR")

    # Agar ikkala manba ham tushib qolgan bo'lsa, foydalanuvchiga sabab ko'rsatamiz
    fx_error = None
    if not (uzs.get("ok") or eur.get("ok")):
        fx_error = uzs.get("error") or eur.get("error")

    return {
        "date_str": now.strftime("%d.%m.%Y"),
        "time_str": now.strftime("%H:%M"),
        "weekday": _WEEKDAYS_UZ[now.weekday()],
        "weather": weather,
        "weather_text": temp_txt,
        "fx_lines": fx_lines,
        "fx_error": fx_error,
    }
