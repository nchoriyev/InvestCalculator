from django.db import models


class InvestmentProject(models.Model):
    """Raqamli xizmatlar eksporti bo'yicha bitta investitsiya loyihasi.

    Foydalanuvchi loyihasiz ham ishlay oladi — birinchi POSTda "default"
    nomli loyiha avtomatik yaratiladi (views_helpers.get_active_project).
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=280)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class ProjectFinancialSnapshot(models.Model):
    """Foydalanuvchi kiritgan parametrlar va shu paytdagi natijalar (snapshot).

    Hozircha avtomatik to'ldirilmaydi, lekin kelajakda "snapshot saqlash"
    tugmasi qo'yilsa shu yerga yozamiz.
    """

    project = models.ForeignKey(
        InvestmentProject,
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    label = models.CharField(max_length=120, blank=True)
    inputs = models.JSONField(default=dict)
    last_results = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ExportTimeSeriesPoint(models.Model):
    """Bashorat va trend tahlili uchun tarixiy oylik eksport qiymatlari."""

    project = models.ForeignKey(
        InvestmentProject,
        on_delete=models.CASCADE,
        related_name="export_series",
    )
    period = models.DateField()
    export_value_usd = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        ordering = ["period"]
        constraints = [
            # Bitta loyiha uchun bir oyga ikki marta yozib qo'ymaslik
            models.UniqueConstraint(
                fields=["project", "period"],
                name="uniq_project_export_period",
            )
        ]


class AnalysisRun(models.Model):
    """Har safar foydalanuvchi biror kalkulyatorni ishga tushirganda yozuv yaratiladi.

    Bu CSV eksport va "tahlillar tarixi" panelining manbai. Sessiya tozalansa
    ham ma'lumotlar yo'qolmaydi (sessiyadagi `dashboard_results` esa volatile).
    """

    class Kind(models.TextChoices):
        CLASSIC = "classic", "NPV/ROI/IRR"
        MONTE_CARLO = "monte_carlo", "Monte Carlo"
        SAAS = "saas", "SaaS metrikalari"
        RISK_MATRIX = "risk_matrix", "Risk matritsasi"
        FORECAST = "forecast", "Bashorat"
        DYNAMIC_RISK = "dynamic_risk", "Dinamik eksport foydasi"
        TAX_SHIELD = "tax_shield", "IT Park soliq imtiyozi"
        ROHC = "rohc", "ROHC"
        BPO_UZ = "bpo_uz", "O'zbekiston BPO eksport"
        SUSTAINABILITY = "sustainability", "Barqarorlik indeksi"
        SENSITIVITY = "sensitivity", "Sensitivlik"
        SCENARIOS = "scenarios", "Ssenariylar solishtirish"
        MONTHLY_DCF = "monthly_dcf", "Oylik DCF"
        SAAS_EXTENDED = "saas_extended", "Rule40 / NRR / Unit"
        RISK_REGISTER = "risk_register", "Risk reyestri"
        FX_FETCH = "fx_fetch", "Valyuta kursi"
        MARKET_BENCHMARK = "market_benchmark", "Bozor benchmark"

    project = models.ForeignKey(
        InvestmentProject,
        on_delete=models.CASCADE,
        related_name="analysis_runs",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    parameters = models.JSONField(default=dict)
    summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
