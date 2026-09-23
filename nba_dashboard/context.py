"""Sayfalar arasında paylaşılan filtre sonucu."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Context:
    df: pd.DataFrame  # ortak filtreler uygulanmış detay satırları
    basis: str  # "TEKIL" / "TOPLAM"
    basis_label: str  # "Tekil" / "Toplam"
    period_days: int  # hesaplama penceresi (gün)
    source_label: str
