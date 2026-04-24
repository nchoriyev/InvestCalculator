"""Har bir kalkulyator natijasi uchun o'zbek tilida xulosa va tavsiyalar.

Asosiy qaror "ko'rsatkich qancha yaxshi yoki yomon" degan savolga
oddiy chegaralar (threshold) bilan javob beradi. Chegaralar — sanoat
amaliyotidan olingan empirik qiymatlar; loyihangizga qarab moslashtirsa
bo'ladi. Hech qanday ML yoki murakkab logika ishlatilmaydi — shaffof
qoladi va PDF/CSV ga eksport qilish ham oson.
"""
from typing import Any


def _level(good: bool, warn: bool) -> str:
    """UI da rang tanlash uchun: yashil / sariq / kulrang."""
    if good:
        return "good"
    if warn:
        return "warn"
    return "neutral"


def _bld(action_title: str, summary: str, tips: list[str], level: str) -> dict[str, Any]:
    """Xulosa dict ini yig'ish — har joyda bir xil shakl bo'lsin uchun."""
    return {
        "level": level,
        "title": action_title,
        "summary": summary,
        "tips": tips[:5],  # 5 dan ortig'i ko'rsatilmaydi (UI joyi cheklangan)
    }


# ----- Klassik tahlil ------------------------------------------------------

def _conclude_classic(result: dict[str, Any]) -> dict[str, Any]:
    npv = float(result.get("npv", 0))
    roi = float(result.get("roi_simple", 0))
    irr = result.get("irr")
    payback = result.get("payback_period_years")

    good = npv > 0
    if good:
        summary = (
            "NPV ijobiy — loyiha diskontlangan pul oqimlari investitsiyani qoplaydi "
            "va qo'shimcha qiymat yaratadi."
        )
    else:
        summary = (
            "NPV salbiy — joriy parametrlar bilan loyiha diskontlangan bazada "
            "qiymat yo'qotishi mumkin."
        )

    tips: list[str] = []
    if irr is not None:
        irr_v = float(irr)
        if irr_v > 0.15:
            tips.append("IRR yuqori — kapital uchun talab qilinadigan daromad stavkasidan yuqori rentabellik ko'rsatiladi.")
        elif irr_v < 0:
            tips.append("IRR manfiy yoki juda past — pul oqimlarini qayta tekshiring (narxlash, xarajatlar).")
    if payback is not None:
        pb_v = float(payback)
        if pb_v <= 4:
            tips.append("Payback qisqa — investitsiya tezroq qaytariladi; likvidlik jihatdan qulay.")
        elif pb_v > 8:
            tips.append("Payback uzoq — risk va imkoniyat xarajatlarini qayta baholang.")
    if roi > 0.2:
        tips.append("Oddiy ROI yuqori — lekin NPV/IRR bilan birga solishtiring (vaqt qiymati).")

    if not tips:
        # Hech qanday alohida signal bo'lmasa, umumiy maslahat
        tips.append("Sensitivlik: diskont stavkasi va yillik pul oqimlarini ±10% o'zgartirib qayta hisoblang.")

    return _bld("Klassik tahlil xulosasi", summary, tips, _level(good, npv < 0 and not good))


# ----- Monte Carlo --------------------------------------------------------

def _conclude_monte_carlo(result: dict[str, Any]) -> dict[str, Any]:
    p = float(result.get("success_probability", 0))
    mean = float(result.get("npv_mean", 0))
    cvar = float(result.get("cvar_95_loss", 0))

    good = p >= 0.55 and mean > 0
    warn = p < 0.45 or mean < 0

    direction = "ijobiy" if mean > 0 else "xavfli"
    summary = (
        f"Muvaffaqiyat ehtimoli {p:.1%} va NPV o'rtacha {mean:,.0f} USD — "
        f"stoxastik jihatdan loyiha {direction} yo'nalishda."
    )

    tips: list[str] = []
    if p >= 0.65:
        tips.append("Yuqori ehtimollik — loyiha barqaror ko'rinadi; asosiy risk omillarini (valyuta, mijoz) barqarorlashtirishni davom eting.")
    else:
        tips.append("Ehtimollik o'rtacha/past — daromad va xarajat dispersiyasini kamaytirish (shartnomalar, KPI) ma'qul.")

    if cvar < 0:
        tips.append(
            f"Pastki 5% ssenariylarda o'rtacha NPV taxminan {cvar:,.0f} USD — "
            f"pastki xavf (tail risk) uchun zaxira kapital rejalashtiring."
        )
    tips.append("Simulyatsiyada trend va dispersiyani yangilab, real bozor ma'lumotlari bilan kalibrlang.")

    return _bld("Monte Carlo xulosasi", summary, tips, _level(good, warn))


# ----- SaaS LTV/CAC --------------------------------------------------------

def _conclude_saas(result: dict[str, Any]) -> dict[str, Any]:
    ratio = result.get("ltv_cac_ratio")
    ltv = float(result.get("ltv_usd", 0))
    cac = float(result.get("cac_usd", 0))

    if ratio is None:
        # CAC nolga juda yaqin yoki marketing budjeti yo'q
        return _bld(
            "SaaS metrikalari xulosasi",
            "LTV:CAC hisoblanmadi — CAC nolga yaqin bo'lishi mumkin.",
            ["Marketing xarajatlarini kiritib qaytadan urinib ko'ring."],
            "neutral",
        )

    r = float(ratio)
    good = r >= 3
    warn = r < 1.5

    if r >= 3:
        verdict = "SaaS uchun yaxshi zonada (odatda 3+ ma'qul)."
    else:
        verdict = "Nisbatni oshirish uchun churn va marketing samaradorligiga e'tibor bering."
    summary = f"LTV {ltv:,.0f} USD, CAC {cac:,.0f} USD, nisbat {r:.2f}. {verdict}"

    tips: list[str] = []
    if r < 1:
        tips.append("LTV < CAC — mijoz yutuq narxi marketingdan past; kanallar va konversiyani optimallashtiring.")
    elif r < 3:
        tips.append("Nisbatni 3+ ga chiqarish: churnni kamaytirish (onboarding, mahsulot), ARPU oshirish.")
    else:
        tips.append("Nisbat yaxshi — hajmni xavfsiz kengaytirish va CAC nazoratini saqlash.")
    tips.append("Churn va gross margin haqiqiy bo'yicha qayta kiritib, LTV ni yangilang.")

    return _bld("SaaS metrikalari xulosasi", summary, tips, _level(good, warn))


# ----- Risk matritsasi ----------------------------------------------------

def _conclude_risk_matrix(result: dict[str, Any]) -> dict[str, Any]:
    comp = float(result.get("composite_risk_score", 0))
    adj = float(result.get("adjusted_npv", 0))

    good = comp < 0.35
    warn = comp > 0.55

    tail = "Risklar nisbatan boshqariladigan darajada." if good else "Risklar yuqori — tuzatilgan natija sezilarli pasayishi mumkin."
    summary = f"Jami risk bahosi {comp:.2f} (0–1). Tuzatilgan NPV ko'rsatkichi {adj:.4f}. {tail}"

    tips = [
        "Mamlakat riskini diversifikatsiya va shartnomalar bilan kamaytiring.",
        "FX: hedging yoki natural hedging (tushum/xarajat valyutasi).",
        "Kiberxavfsizlik: SOC2/ISO yo'nalishida byudjetni rejalashtiring.",
    ]
    return _bld("Risk matritsasi xulosasi", summary, tips, _level(good, warn))


# ----- Bashorat -----------------------------------------------------------

def _conclude_forecast(result: dict[str, Any]) -> dict[str, Any]:
    method = result.get("method_used", "")
    fc = result.get("forecast_next_months_usd") or []

    good = len(fc) >= 2 and float(fc[-1]) >= float(fc[0])
    summary = f"Bashorat usuli: {method}. Keyingi {len(fc)} oy uchun eksport hajmi prognozi hisoblandi."

    tips: list[str] = []
    if fc:
        trend = float(fc[-1]) - float(fc[0])
        summary += f" Oxirgi oyga nisbatan boshlang'ichdan farq: {trend:+,.0f} USD (taxminiy)."
        if trend > 0:
            tips.append("O'sish trendi — kapital va xodimlar rejasini prognoz bilan uyg'unlashtiring.")
        else:
            tips.append("Pasayish yoki tekislik — marketing va mijoz bazasini mustahkamlash.")
    tips.append("ARIMA ishlatilgan bo'lsa, ma'lumot uzunligini oshirib modelni qayta baholang.")

    return _bld("Bashorat xulosasi", summary, tips, _level(good, not good))


# ----- Sof eksport foydasi ------------------------------------------------

def _conclude_dynamic_risk(result: dict[str, Any]) -> dict[str, Any]:
    net = float(result.get("net_export_benefit_usd", 0))
    good = net > 0

    if good:
        summary = f"Sof eksport foydasi (USD): {net:,.2f}. Komissiya va kurs o'zgarishlari hisobga olindi."
    else:
        summary = "Sof foyda salbiy — kurs, komissiya yoki mahalliy xarajatlarni optimallashtirish kerak."

    tips = [
        "Δe ni stress-test qiling: ±5% va ±10% uchun foydani qayta hisoblang.",
        "Xalqaro komissiyani kamaytirish: to'lov kanali va shartnomalar.",
    ]
    return _bld("Sof eksport foydasi xulosasi", summary, tips, _level(good, not good))


# ----- IT Park soliq imtiyozi ----------------------------------------------

def _conclude_tax_shield(result: dict[str, Any]) -> dict[str, Any]:
    shield = float(result.get("tax_shield_usd", 0))
    good = shield > 0
    summary = f"IT Park imtiyozi taxminan {shield:,.2f} USD soliq yukini kamaytirish effektini beradi (tax shield)."
    tips = [
        "Rezidentlik va hisob siyosatini IT Park talablariga mos tuting.",
        "Imtiyozsiz stavka va IT Park stavkasini yangi qonunchilikka qarab yangilang.",
    ]
    return _bld("Soliq (IT Park) xulosasi", summary, tips, "good" if good else "neutral")


# ----- BPO O'zbekiston ----------------------------------------------------

def _conclude_bpo_uz(result: dict[str, Any]) -> dict[str, Any]:
    # EBIT manfiy bo'lsa, run paytida `note` qo'shilgan bo'ladi
    if result.get("note"):
        return _bld(
            "BPO tahlili xulosasi",
            "EBIT manfiy — eksport tushumi ish haqi va xarajatlarni qoplamayapti; "
            "hajm yoki narxlash strategiyasini ko'rib chiqing.",
            [
                "Xodim samaradorligi va chet el narxlariga mos tariflar.",
                "Operatsion xarajatlarni qisqartirish va eksport shartnomalarini mustahkamlash.",
            ],
            "warn",
        )

    roi_it = float(result.get("roi_on_export_revenue_with_it_park") or 0)
    roi_no = float(result.get("roi_on_export_revenue_without_incentive") or 0)
    good = roi_it > roi_no and roi_it > 0

    summary = (
        f"IT Park bilan eksport tushumiga nisbatan sof rentabellik {roi_it:.2%}, "
        f"imtiyozsiz {roi_no:.2%}. Farq: imtiyoz loyihaning sof rentabelligini oshiradi."
    )
    tips = [
        "Eksport hajmini oshirish va ish haqi fondini boshqarish — ROIni yaxshilashning asosiy yo'li.",
        "Boshqa operatsion xarajatlarni monitoring qilib, EBIT marjasini saqlang.",
    ]
    return _bld("BPO (O'zbekiston) xulosasi", summary, tips, _level(good, roi_it < 0.05))


# ----- ROHC ---------------------------------------------------------------

def _conclude_rohc(result: dict[str, Any]) -> dict[str, Any]:
    rohc = float(result.get("rohc_ratio", 0))
    rel = result.get("relative_to_benchmark")

    good = rohc >= 1.2
    warn = rohc < 1.0

    summary = (
        f"ROHC (eksport/payroll) {rohc:.2f}. "
        f"Xodim boshiga eksport tushumi {float(result.get('export_revenue_per_employee_usd', 0)):,.0f} USD."
    )

    tips: list[str] = []
    if rel is not None:
        rel_v = float(rel)
        summary += f" Benchmark nisbati: {rel_v:.2f}."
        if rel_v >= 1:
            tips.append("Benchmarkdan yuqori yoki teng — inson kapitali samaradorligi yaxshi.")
        else:
            tips.append("Benchmarkdan past — jarayonlarni avtomatlashtirish va chet el bozorida narxlashni ko'rib chiqing.")
    else:
        tips.append("Benchmark kiriting — Hindiston/Polsha kabi BPO ko'rsatkichlari bilan solishtirish osonlashadi.")
    tips.append("Ish haqi fondi va eksport hajmini muvozanatlang: ortiqcha xodimlar ROHCni pasaytiradi.")

    return _bld("ROHC xulosasi", summary, tips, _level(good, warn))


# ----- Barqarorlik --------------------------------------------------------

def _conclude_sustainability(result: dict[str, Any]) -> dict[str, Any]:
    idx = float(result.get("sustainability_index", 0))
    good = idx >= 65
    warn = idx < 40

    summary = f"Barqarorlik indeksi {idx:.1f} / 100 — Monte Carlo muvaffaqiyati, risk va bashorat ishonchliligidan foydalanadi."

    if good:
        tip = "Indeks yuqori — loyiha strategik jihatdan barqarorroq ko'rinadi; monitoringni davom ettiring."
    elif warn:
        tip = "Indeks past — riskni kamaytirish yoki bashorat ishonchliligini oshirish (ma'lumot, ARIMA) kerak."
    else:
        tip = "O'rta zona — alohida risk omillarini (valyuta, mamlakat) chuqurroq tahlil qiling."

    return _bld("Barqarorlik indeksi xulosasi", summary, [tip], _level(good, warn))


# ----- Sensitivity / Scenarios / Monthly DCF / SaaS+ ----------------------

def _conclude_sensitivity(result: dict[str, Any]) -> dict[str, Any]:
    base = float(result.get("base_npv", 0))
    param = result.get("parameter", "")
    summary = f"NPV {param} bo'yicha ±foizlar bilan o'zgaradi; bazaviy NPV {base:,.2f} USD."
    tips = [
        "Eng katta NPV siljishini beruvchi omilni rejalashtirishda ustuvor tuting.",
        "Diskont va tushum taxminlarini mustaqil manbalardan tasdiqlang.",
    ]
    return _bld("Sensitivlik xulosasi", summary, tips, "neutral")


def _conclude_scenarios(result: dict[str, Any]) -> dict[str, Any]:
    b = float(result["base"]["npv"])
    o = float(result["optimistic"]["npv"])
    p = float(result["pessimistic"]["npv"])

    spread = max(o, b, p) - min(o, b, p)
    summary = f"Uch ssenariy: NPV bazaviy {b:,.0f}, optimistik {o:,.0f}, pessimistik {p:,.0f} USD (spread ~{spread:,.0f})."
    tips = [
        "Pessimistik ssenariyda ham NPV ijobiy bo'lsa — loyiha xavf-sezgirligi pastroq.",
        "Tushum va xarajat koeffitsientlarini real bozor bilan kalibrlang.",
    ]
    return _bld("Ssenariylar xulosasi", summary, tips, _level(o > b > p, p < 0))


def _conclude_monthly_dcf(result: dict[str, Any]) -> dict[str, Any]:
    npv = float(result.get("npv_monthly_model_usd", 0))
    pm = result.get("payback_period_months")

    summary = f"Oylik model NPV {npv:,.2f} USD."
    if pm is not None:
        summary += f" Payback ~{float(pm):.1f} oy."

    tips = ["Oylik model yillik model bilan solishtiring — farq katta bo'lsa, mavsumiylikni hisobga oling."]
    return _bld("Oylik DCF xulosasi", summary, tips, _level(npv > 0, npv < 0))


def _conclude_saas_extended(result: dict[str, Any]) -> dict[str, Any] | None:
    mode = result.get("mode", "")

    if mode == "rule40":
        s = float(result.get("rule_of_40_score", 0))
        summary = f"Rule of 40 balli {s:.1f} — {result.get('interpretation', '')}."
        return _bld(
            "Rule of 40 xulosasi",
            summary,
            ["O'sish va marjani bir vaqtda kuzating; SaaS IPO/bozor kutilmalari bilan solishtiring."],
            _level(s >= 40, s < 25),
        )

    if mode == "nrr":
        nrr = float(result.get("nrr_ratio", 1))
        summary = f"NRR {nrr:.2f} — {result.get('interpretation', '')}."
        return _bld(
            "NRR xulosasi",
            summary,
            ["Expansion va churnni alohida hisoblang; NRR >1 barqaror o'sish uchun muhim."],
            _level(nrr >= 1.1, nrr < 1),
        )

    if mode == "unit":
        net = float(result.get("monthly_net_after_fixed_usd", 0))
        return _bld(
            "Unit economics xulosasi",
            "Birlik iqtisodiyoti: kontributsiya va fixed dan keyingi oylik natija hisoblandi.",
            ["Birlik hajmini oshirishdan oldin chegaraviy foydani tekshiring."],
            _level(net > 0, net < 0),
        )

    return None


def _conclude_risk_register(result: dict[str, Any]) -> dict[str, Any]:
    agg = float(result.get("aggregate_score", 0))
    summary = f"Risk reyestri: yig'ma ball (p×i) {agg:.3f}, {result.get('risk_count', 0)} ta omil."
    tips = [
        "Eng yuqori p×i bo'yicha kamaytirish rejalari (tuzatish, sug'urta, shartnoma).",
        "Yangi risk qo'shilganda reyestrni yangilab qayta baholang.",
    ]
    return _bld("Risk reyestri xulosasi", summary, tips, _level(agg < 1.5, agg > 3))


def _conclude_fx_fetch(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("ok"):
        summary = f"1 USD = {result.get('rate')} {result.get('target')} (manba: {result.get('source', 'API')})."
        return _bld(
            "Valyuta kursi",
            summary,
            ["Kursni eksport shartnomalaridagi kurs bilan solishtiring; stress uchun ±5% qo'llang."],
            "good",
        )
    return _bld(
        "Valyuta kursi",
        result.get("error", "Kurs olinmadi — qo'lda kiriting."),
        ["Internet ulanishini tekshiring yoki MB kursidan foydalaning."],
        "warn",
    )


def _conclude_market_benchmark(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("ok"):
        summary = "Jahon Banki ochiq ma'lumotlari bo'yicha mamlakat iqtisodiy o'sish seriyasi yuklandi."
        latest = result.get("latest_growth_pct")
        if latest is not None:
            summary += f" So'nggi yil: {latest}%."
        return _bld(
            "Bozor benchmark",
            summary,
            ["IT eksporti uchun real sektor o'sishi bilan to'g'ridan bog'liq emas — qo'shimcha sifatiy tahlil qiling."],
            "neutral",
        )
    return _bld(
        "Bozor benchmark",
        result.get("error", "Ma'lumot olinmadi."),
        ["Keyinroq qayta urinib ko'ring yoki qo'lda kiritilgan trenddan foydalaning."],
        "warn",
    )


# action -> tegishli xulosa funksiyasi. Bitta dispatch o'rniga lambda emas,
# alohida funksiyalar — chunki har biri tipik holatlarda 10-30 qatordan iborat.
_DISPATCH = {
    "classic": _conclude_classic,
    "monte_carlo": _conclude_monte_carlo,
    "saas": _conclude_saas,
    "risk_matrix": _conclude_risk_matrix,
    "forecast": _conclude_forecast,
    "dynamic_risk": _conclude_dynamic_risk,
    "tax_shield": _conclude_tax_shield,
    "bpo_uz": _conclude_bpo_uz,
    "rohc": _conclude_rohc,
    "sustainability": _conclude_sustainability,
    "sensitivity": _conclude_sensitivity,
    "scenarios": _conclude_scenarios,
    "monthly_dcf": _conclude_monthly_dcf,
    "saas_extended": _conclude_saas_extended,
    "risk_register": _conclude_risk_register,
    "fx_fetch": _conclude_fx_fetch,
    "market_benchmark": _conclude_market_benchmark,
}


def build_conclusion(action: str, result: dict[str, Any] | None) -> dict[str, Any] | None:
    if not result:
        return None
    fn = _DISPATCH.get(action)
    return fn(result) if fn else None


def enrich_results(results: dict[str, Any]) -> dict[str, Any]:
    """Har bir natijaga "conclusion" qo'shadi — template'da bevosita ko'rsatish uchun."""
    out: dict[str, Any] = {}
    for key, entry in results.items():
        if not isinstance(entry, dict):
            continue
        inner = dict(entry)
        inner["conclusion"] = build_conclusion(key, inner.get("result"))
        out[key] = inner
    return out


def strip_for_chart_json(results: dict[str, Any]) -> dict[str, Any]:
    """Chart.js ga uzatish uchun faqat (result + chart) qoldiramiz, xulosani olib tashlaymiz.

    Buni JSON sifatida HTMLga embed qilamiz, demak hajmini kichraytirish foydali.
    """
    return {
        key: {k: v for k, v in entry.items() if k in ("result", "chart")}
        for key, entry in results.items()
        if isinstance(entry, dict)
    }
