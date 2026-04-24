"""Faol loyihani sessiyadan olish va CSV import."""
import csv
from datetime import datetime
from io import StringIO
from typing import TYPE_CHECKING

from django.utils.dateparse import parse_date

from projects.models import ExportTimeSeriesPoint, InvestmentProject

if TYPE_CHECKING:
    from django.http import HttpRequest


def get_active_project(request: "HttpRequest") -> InvestmentProject:
    """Sessiyadagi project_id bo'yicha loyihani topadi.

    Topilmasa — "default" slugli loyihani yaratib (yoki olib) qaytaradi.
    Shu bilan birinchi kirgan foydalanuvchini "ro'yxatdan o'tkazish" shart emas.
    """
    pid = request.session.get("project_id")
    if pid:
        try:
            return InvestmentProject.objects.get(pk=int(pid))
        except (InvestmentProject.DoesNotExist, ValueError, TypeError):
            # session id eskirgan / o'chirilgan loyiha — pastga tushib default ni olamiz
            pass

    project, _ = InvestmentProject.objects.get_or_create(
        slug="default",
        defaults={"name": "Asosiy loyiha"},
    )
    request.session["project_id"] = project.pk
    return project


# CSV ichida sana qaysi formatda kelishi mumkinligini bilmaymiz —
# eng keng tarqalgan uchtasini birma-bir sinab ko'ramiz.
_DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y")


def import_timeseries_csv(project: InvestmentProject, file_obj) -> tuple[int, str | None]:
    """CSV: birinchi ustun — sana, ikkinchisi — qiymat (USD)."""
    try:
        raw = file_obj.read()
        text = raw.decode("utf-8-sig") if isinstance(raw, bytes) else str(raw)

        reader = csv.reader(StringIO(text))
        n = 0

        for row in reader:
            if len(row) < 2:
                continue

            raw_d = row[0].strip()
            d = parse_date(raw_d)

            if d is None:
                # Django parse_date ISO formatda kutadi — qolganlarini qo'lda urinib ko'ramiz
                for fmt in _DATE_FORMATS:
                    try:
                        d = datetime.strptime(raw_d, fmt).date()
                        break
                    except ValueError:
                        continue

            if d is None:
                continue  # tushunolmagan qatorni shunchaki tashlab ketamiz

            # Qiymat ichida ham vergul, ham bo'sh joy bo'lishi mumkin (1 234,56)
            try:
                val = float(str(row[1]).replace(",", ".").replace(" ", ""))
            except ValueError:
                continue

            ExportTimeSeriesPoint.objects.update_or_create(
                project=project,
                period=d,
                defaults={"export_value_usd": val},
            )
            n += 1

        return n, None
    except Exception as e:  # pragma: no cover
        return 0, str(e)
