"""Forma qiymatlarini xavfsiz parse qilish.

Foydalanuvchi vergul yoki nuqta bilan, bo'sh joy yoki probelsiz —
har xil yozadi. Bu yerdagi yordamchilar bularni bir holatga keltiradi.
"""
import re
from typing import Any

# Bo'sh joy, vergul yoki nuqta-vergul — uchalasini ham ajratuvchi sifatida qabul qilamiz
_SPLIT_RE = re.compile(r"[\s,;]+")


def float_list(raw: str) -> list[float]:
    parts = _SPLIT_RE.split(raw.strip())
    return [float(p) for p in parts if p]


def get_float(post: Any, key: str, default: float | None = None) -> float:
    v = post.get(key)
    if v is None or str(v).strip() == "":
        if default is not None:
            return float(default)
        raise ValueError(f"{key} kiritilishi shart")
    # vergulni nuqtaga aylantiramiz — o'zbekcha klaviaturada ko'pincha vergul
    return float(str(v).replace(",", "."))


def get_int(post: Any, key: str, default: int | None = None) -> int:
    v = post.get(key)
    if v is None or str(v).strip() == "":
        if default is not None:
            return int(default)
        raise ValueError(f"{key} kiritilishi shart")
    # foydalanuvchi "10000.0" deb yozsa ham qabul qilaylik
    return int(float(str(v)))
