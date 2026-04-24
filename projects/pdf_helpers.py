"""PDF eksport uchun yordamchi funksiyalar.

Asosiy maqsad — natija dict'idagi texnik kalitlarni (`npv_mean`,
`roi_simple`...) o'zbekcha o'qilishi qulay yorliqlar va to'g'ri
formatlangan qiymatlarga aylantirish. Shu bilan PDF "ham odamga ham
buxgalterga" tushunarli bo'ladi: qator-qator jadvalda ko'rsatamiz,
JSON tashlamasi qolmaydi.

Yangi maydonlar paydo bo'lsa — `_LABELS` ga qo'shing; topilmagan kalit
texnik nomi bilan ko'rinadi (xato bermaydi).
"""
from typing import Any, Iterable


# --- Sarlavhalar (action -> chiroyli sarlavha) ----------------------------

SECTION_TITLES: dict[str, str] = {
    "classic": "Klassik investitsiya tahlili",
    "monte_carlo": "Monte Carlo simulyatsiyasi",
    "saas": "SaaS metrikalari (LTV / CAC)",
    "risk_matrix": "Risk matritsasi",
    "forecast": "Eksport bashorati",
    "dynamic_risk": "Sof eksport foydasi",
    "tax_shield": "IT Park — soliq imtiyozi (tax shield)",
    "bpo_uz": "BPO — O'zbekiston tahlili",
    "rohc": "ROHC — inson kapitali rentabelligi",
    "sustainability": "Barqarorlik indeksi",
    "sensitivity": "Sensitivlik tahlili",
    "scenarios": "Uch ssenariy (optimistik / bazaviy / pessimistik)",
    "monthly_dcf": "Oylik DCF",
    "saas_extended": "Rule of 40 / NRR / Unit economics",
    "risk_register": "Risk reyestri",
    "fx_fetch": "Valyuta kursi (tashqi API)",
    "market_benchmark": "Jahon Banki benchmark",
}


# --- Maydon formatlari ----------------------------------------------------
# (chiroyli yorliq, format kodi). Format kodlari:
#   "usd"       -> $1 234.56
#   "usd0"      -> $1 235  (yaxlitlangan)
#   "pct"       -> 12.34 %
#   "pct1"      -> 12.3 %
#   "ratio"     -> 1.23
#   "num"       -> 1 234.5678
#   "int"       -> 1 234
#   "year"      -> 2.5 yil
#   "month"     -> 12.0 oy
#   "text"      -> str(x)
_LABELS: dict[str, tuple[str, str]] = {
    # Klassik
    "npv": ("NPV (sof joriy qiymat)", "usd"),
    "roi_simple": ("ROI (oddiy)", "pct"),
    "irr": ("IRR (ichki rentabellik)", "pct"),
    "payback_period_years": ("Payback (yil)", "year"),

    # Monte Carlo
    "success_probability": ("Muvaffaqiyat ehtimoli", "pct"),
    "npv_mean": ("NPV — o'rtacha", "usd"),
    "npv_std": ("NPV — standart og'ish", "usd"),
    "cvar_95_loss": ("CVaR 95% (pastki 5% o'rtachasi)", "usd"),
    "n_simulations": ("Simulyatsiyalar soni", "int"),

    # SaaS
    "ltv_usd": ("LTV (mijoz hayotiy qiymati)", "usd"),
    "cac_usd": ("CAC (mijoz olish narxi)", "usd"),
    "ltv_cac_ratio": ("LTV : CAC nisbati", "ratio"),
    "monthly_churn_rate": ("Oylik churn", "pct"),
    "gross_margin": ("Brutto marja", "pct"),

    # Risk matritsa
    "composite_risk_score": ("Yig'ma risk balli (0–1)", "ratio"),
    "adjusted_npv": ("Tuzatilgan NPV (koeffitsient)", "ratio"),
    "country_risk": ("Mamlakat riski", "ratio"),
    "fx_risk": ("FX riski", "ratio"),
    "cyber_risk": ("Kiber riski", "ratio"),

    # Bashorat
    "method_used": ("Qo'llanilgan usul", "text"),
    "forecast_next_months_usd": ("Bashorat (USD, oylar)", "list_usd"),

    # Sof eksport
    "net_export_benefit_usd": ("Sof eksport foydasi (USD)", "usd"),
    "international_fee_usd": ("Xalqaro komissiya (USD)", "usd"),
    "local_costs_usd": ("Mahalliy xarajat (USD ekvivalenti)", "usd"),
    "effective_rate": ("Samarali kurs (so'm/USD)", "num"),

    # Tax shield
    "tax_shield_usd": ("Tax shield (USD)", "usd"),
    "tax_without_incentive_usd": ("Soliq — imtiyozsiz", "usd"),
    "tax_with_it_park_usd": ("Soliq — IT Park", "usd"),

    # BPO
    "ebit_usd": ("EBIT (operatsion foyda)", "usd"),
    "roi_on_export_revenue_with_it_park": ("ROI (IT Park bilan)", "pct"),
    "roi_on_export_revenue_without_incentive": ("ROI (imtiyozsiz)", "pct"),
    "note": ("Eslatma", "text"),

    # ROHC
    "rohc_ratio": ("ROHC nisbati", "ratio"),
    "export_revenue_per_employee_usd": ("Xodim boshiga eksport (USD)", "usd"),
    "relative_to_benchmark": ("Benchmarkga nisbatan", "ratio"),

    # Barqarorlik
    "sustainability_index": ("Barqarorlik indeksi (0–100)", "num"),

    # Sensitivlik / Ssenariy
    "base_npv": ("Bazaviy NPV", "usd"),
    "parameter": ("O'zgartirilgan parametr", "text"),

    # Oylik DCF
    "npv_monthly_model_usd": ("Oylik model NPV", "usd"),
    "payback_period_months": ("Payback (oy)", "month"),

    # SaaS extended
    "mode": ("Rejim", "text"),
    "rule_of_40_score": ("Rule of 40 balli", "num"),
    "interpretation": ("Talqin", "text"),
    "nrr_ratio": ("NRR nisbati", "ratio"),
    "monthly_net_after_fixed_usd": ("Sof oylik (fixed dan keyin)", "usd"),

    # Risk reyestri
    "aggregate_score": ("Yig'ma risk (p×i)", "ratio"),
    "risk_count": ("Omillar soni", "int"),

    # FX
    "ok": ("Holat", "ok"),
    "rate": ("1 USD =", "num"),
    "target": ("Maqsad valyuta", "text"),
    "source": ("Manba", "text"),
    "error": ("Xatolik", "text"),

    # Jahon Banki
    "latest_growth_pct": ("So'nggi yil GDP o'sishi", "pct1"),
    "country": ("Mamlakat (ISO)", "text"),
}


# Kirish parametrlari (POST) uchun yorliqlar
_PARAM_LABELS: dict[str, str] = {
    "initial_investment": "Boshlang'ich investitsiya (USD)",
    "discount_rate": "Diskont stavkasi",
    "salvage_value": "Qoldiq qiymati",
    "annual_cashflows": "Yillik pul oqimlari",
    "monthly_cashflows": "Oylik pul oqimlari",
    "n_simulations": "Simulyatsiyalar soni",
    "years": "Yillar soni",
    "revenue_mean": "Daromad — o'rtacha (μ)",
    "revenue_std": "Daromad — og'ish (σ)",
    "cost_mean": "Xarajat — o'rtacha (μ)",
    "cost_std": "Xarajat — og'ish (σ)",
    "revenue_growth_mean": "Daromad o'sishi (μ)",
    "cost_growth_mean": "Xarajat o'sishi (μ)",
    "random_seed": "Random seed",
    "arpu_monthly_usd": "ARPU (oylik, USD)",
    "gross_margin": "Brutto marja",
    "monthly_churn_rate": "Oylik churn",
    "marketing_spend_usd": "Marketing budjeti (USD)",
    "new_customers": "Yangi mijozlar soni",
    "country_risk_score": "Mamlakat riski (0–1)",
    "fx_volatility": "FX tebranishi (0–1)",
    "cyber_cost_share": "Kiber ulush (0–1)",
    "base_npv": "Bazaviy NPV",
    "history_usd": "Tarixiy oylar (USD)",
    "horizon_months": "Bashorat gorizonti (oy)",
    "prefer_arima": "ARIMA urinish",
    "export_revenue_usd": "Eksport tushumi (USD)",
    "international_fee_rate": "Xalqaro komissiya (0–1)",
    "local_costs_in_local_currency": "Mahalliy xarajat (so'm)",
    "exchange_rate_local_per_usd": "Kurs (so'm/USD)",
    "delta_e": "Δe (kurs o'zgarishi)",
    "taxable_profit_usd": "Soliqqa tortiladigan foyda (USD)",
    "income_tax_rate_without_incentive": "Stavka — imtiyozsiz",
    "income_tax_rate_it_park": "Stavka — IT Park",
    "annual_export_revenue_usd": "Yillik eksport (USD)",
    "annual_payroll_usd": "Yillik ish haqi (USD)",
    "other_operating_costs_usd": "Boshqa operatsion xarajatlar",
    "headcount": "Xodimlar soni",
    "benchmark_revenue_per_payroll": "Benchmark (eksport/payroll)",
    "monte_carlo_success_probability": "MC muvaffaqiyat ehtimoli",
    "composite_risk_score": "Jami risk (0–1)",
    "forecast_method": "Bashorat usuli",
    "sensitivity_parameter": "Parametr",
    "sensitivity_steps": "Qadamlar (%)",
    "opt_revenue_mult": "Optimistik tushum koef.",
    "opt_cost_mult": "Optimistik xarajat koef.",
    "pes_revenue_mult": "Pessimistik tushum koef.",
    "pes_cost_mult": "Pessimistik xarajat koef.",
    "saas_ext_mode": "SaaS+ rejim",
    "revenue_growth_yoy": "Yillik tushum o'sishi",
    "profit_margin": "Foyda marjasi",
    "starting_mrr": "Boshlang'ich MRR",
    "ending_mrr": "Yakuniy MRR",
    "churned_mrr": "Churn MRR",
    "expansion_mrr": "Expansion MRR",
    "price_per_unit_usd": "Birlik narxi",
    "variable_cost_per_unit_usd": "O'zgaruvchan xarajat",
    "units_per_month": "Birlik / oy",
    "fixed_cost_monthly_usd": "Doimiy xarajat / oy",
    "risk_register_json": "Risk reyestri (JSON)",
    "fx_target": "Valyuta (ISO)",
    "wb_country": "Mamlakat (ISO2)",
}

# Texnik kalitlar — PDF kirish jadvalida ko'rsatilmaydi
_PARAM_HIDDEN = {"action", "csrfmiddlewaretoken"}


# --- Format funksiyalari --------------------------------------------------

def _fmt_number(x, decimals: int = 2) -> str:
    """Probel bilan ajratilgan minglik (1 234 567,89) — Yevropa odati."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    s = f"{v:,.{decimals}f}"
    # Vergulni probel bilan, nuqtani vergul bilan almashtirib chiqamiz
    return s.replace(",", " ").replace(".", ",")


def _fmt_value(value: Any, fmt: str) -> str:
    if value is None:
        return "—"

    if fmt == "usd":
        return f"${_fmt_number(value, 2)}"
    if fmt == "usd0":
        return f"${_fmt_number(value, 0)}"
    if fmt == "pct":
        try:
            return f"{float(value) * 100:.2f} %".replace(".", ",")
        except (TypeError, ValueError):
            return str(value)
    if fmt == "pct1":
        try:
            return f"{float(value):.1f} %".replace(".", ",")
        except (TypeError, ValueError):
            return str(value)
    if fmt == "ratio":
        return _fmt_number(value, 4)
    if fmt == "num":
        return _fmt_number(value, 2)
    if fmt == "int":
        try:
            return _fmt_number(int(float(value)), 0)
        except (TypeError, ValueError):
            return str(value)
    if fmt == "year":
        return f"{_fmt_number(value, 2)} yil"
    if fmt == "month":
        return f"{_fmt_number(value, 1)} oy"
    if fmt == "ok":
        return "Muvaffaqiyatli" if value else "Xatolik"
    if fmt == "list_usd":
        if not isinstance(value, (list, tuple)):
            return str(value)
        head = ", ".join(_fmt_number(x, 0) for x in value[:6])
        if len(value) > 6:
            head += f", … ({len(value)} ta jami)"
        return head
    return str(value)


def result_rows(result: dict[str, Any] | None) -> list[dict[str, str]]:
    """Natija dict'idan PDF jadvali uchun [{label, value}, ...] qaytaradi.

    `_LABELS` da bo'lmagan maydonlar oddiy str() bilan ko'rsatiladi —
    ma'lumot yo'qolmaydi, lekin maxsus formatlanmaydi.
    """
    if not isinstance(result, dict):
        return []
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    # Avval ma'lum kalitlar (insonga tushunarli tartibda)
    for key, (label, fmt) in _LABELS.items():
        if key in result:
            rows.append({"label": label, "value": _fmt_value(result[key], fmt)})
            seen.add(key)

    # Qolganlari (texnik nomlar bilan)
    for key, value in result.items():
        if key in seen:
            continue
        if isinstance(value, (list, tuple, dict)):
            # Murakkab strukturalarni qisqartirilgan ko'rinishda
            preview = str(value)
            if len(preview) > 120:
                preview = preview[:117] + "…"
            rows.append({"label": key, "value": preview})
        else:
            rows.append({"label": key, "value": _fmt_value(value, "text")})
    return rows


def param_rows(params: dict[str, Any] | None) -> list[dict[str, str]]:
    """Foydalanuvchi kiritgan POST qiymatlardan jadval qatorlari."""
    if not isinstance(params, dict):
        return []
    rows: list[dict[str, str]] = []
    for key, value in params.items():
        if key in _PARAM_HIDDEN:
            continue
        label = _PARAM_LABELS.get(key, key)
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        text = str(value).strip()
        if len(text) > 200:
            text = text[:197] + "…"
        rows.append({"label": label, "value": text or "—"})
    return rows


def section_title(action: str) -> str:
    return SECTION_TITLES.get(action, action)


def iter_report_sections(results: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """`enrich_results` natijasidan PDF uchun bo'limlar generatori."""
    for key, entry in results.items():
        if not isinstance(entry, dict):
            continue
        yield {
            "key": key,
            "title": section_title(key),
            "params": param_rows(entry.get("params")),
            "results": result_rows(entry.get("result")),
            "conclusion": entry.get("conclusion"),
        }
