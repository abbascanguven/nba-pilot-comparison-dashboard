"""Türkçe sayı biçimlendirme yardımcıları (binlik ayırıcı nokta, ondalık virgül)."""

from __future__ import annotations

import pandas as pd


def _tr(s: str) -> str:
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def fmt_int(v: float, sign: bool = False) -> str:
    return "–" if pd.isna(v) else _tr(f"{v:{'+' if sign else ''},.0f}")


def fmt_pct(v: float, digits: int = 3) -> str:
    return "–" if pd.isna(v) else "%" + _tr(f"{v * 100:.{digits}f}")


def fmt_num(v: float, digits: int = 3, sign: bool = False) -> str:
    return "–" if pd.isna(v) else _tr(f"{v:{'+' if sign else ''}.{digits}f}")


def fmt_points(v: float, digits: int = 3) -> str:
    """Oran farkı, yüzde puan olarak."""
    return "–" if pd.isna(v) else _tr(f"{v * 100:+.{digits}f}") + " puan"


def fmt_change(v: float, digits: int = 1) -> str:
    """Lift değerinin 1'e göre yüzde farkı."""
    return "–" if pd.isna(v) else _tr(f"{(v - 1) * 100:+.{digits}f}") + "%"
