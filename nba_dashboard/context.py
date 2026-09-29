"""Sayfalar arasında paylaşılan filtre sonucu."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class Context:
    df: pd.DataFrame  # ortak filtreler uygulanmış detay satırları
    basis: str  # "TEKIL" / "TOPLAM"
    basis_label: str  # "Tekil" / "Toplam"
    period_days: int  # hesaplama penceresi (gün)
    source_label: str
    exclusions: pd.DataFrame = field(default_factory=pd.DataFrame)  # kırmızı işaretlenecek tarihler
    exclude_active: bool = False  # "Hariç tutulan tarihleri çıkar" açık mı
    removed_dates: tuple[pd.Timestamp, ...] = ()  # hariç tutulduğu için veriden çıkarılan LAST_OFFER_DATE'ler
