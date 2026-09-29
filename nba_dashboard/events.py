"""Config klasöründeki tarih listelerini okur.

- config/onemli_tarihler.toml          → grafiklerde 📌 ile işaretlenen önemli tarihler
- config/is_birimi_aksiyonlari.toml    → grafiklerde ⚠️ ile işaretlenen iş birimi aksiyonları (gün ya da aralık)
- config/haric_tutulan_tarihler.toml   → kırmızıyla işaretlenen, istenirse hesaplamadan çıkarılan tarihler
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pandas as pd

from nba_dashboard.data import PROJECT_ROOT

EVENTS_PATH = PROJECT_ROOT / "config" / "onemli_tarihler.toml"
ACTIONS_PATH = PROJECT_ROOT / "config" / "is_birimi_aksiyonlari.toml"
EXCLUSIONS_PATH = PROJECT_ROOT / "config" / "haric_tutulan_tarihler.toml"

DATE_FORMAT = "%d.%m.%Y"


def _read_entries(path: Path, key: str) -> tuple[list[dict], list[str]]:
    if not path.exists():
        return [], []
    try:
        with path.open("rb") as f:
            return tomllib.load(f).get(key, []), []
    except tomllib.TOMLDecodeError as exc:
        return [], [f"{path.name} okunamadı: {exc}"]


def _parse_day(value) -> pd.Timestamp:
    return pd.to_datetime(str(value or ""), format=DATE_FORMAT, errors="coerce")


def _load_day_entries(path: Path, key: str) -> tuple[pd.DataFrame, list[str]]:
    """Tek günlük kayıtları (gun, baslik, aciklama, birim) okur."""
    columns = ["tarih", "baslik", "aciklama", "birim"]
    entries, errors = _read_entries(path, key)

    rows = []
    for i, entry in enumerate(entries, start=1):
        day = _parse_day(entry.get("gun"))
        title = str(entry.get("baslik", "")).strip()
        if pd.isna(day) or not title:
            errors.append(f"{path.name}, {i}. kayıt atlandı: 'gun' (GG.AA.YYYY) ve 'baslik' zorunlu.")
            continue
        rows.append(
            {
                "tarih": day,
                "baslik": title,
                "aciklama": str(entry.get("aciklama", "")).strip(),
                "birim": str(entry.get("birim", "")).strip(),
            }
        )
    df = pd.DataFrame(rows, columns=columns).sort_values("tarih") if rows else pd.DataFrame(columns=columns)
    return df, errors


def load_events() -> tuple[pd.DataFrame, list[str]]:
    """Önemli tarihler: (tarih, baslik, aciklama, birim) tablosu ve hata mesajları."""
    return _load_day_entries(EVENTS_PATH, "tarih")


def _load_range_entries(path: Path, key: str) -> tuple[pd.DataFrame, list[str]]:
    """Tek gün (`gun`) ya da aralık (`baslangic` + `bitis`, iki gün de dahil) kayıtlarını okur."""
    columns = ["baslangic", "bitis", "baslik", "aciklama", "birim"]
    entries, errors = _read_entries(path, key)

    rows = []
    for i, entry in enumerate(entries, start=1):
        title = str(entry.get("baslik", "")).strip()
        if "gun" in entry:
            start = end = _parse_day(entry.get("gun"))
        else:
            start, end = _parse_day(entry.get("baslangic")), _parse_day(entry.get("bitis"))
        if pd.isna(start) or pd.isna(end) or not title:
            errors.append(
                f"{path.name}, {i}. kayıt atlandı: 'gun' ya da 'baslangic' + 'bitis' "
                "(GG.AA.YYYY) ve 'baslik' zorunlu."
            )
            continue
        if end < start:
            errors.append(f"{path.name}, {i}. kayıt atlandı: 'bitis', 'baslangic' tarihinden önce.")
            continue
        rows.append(
            {
                "baslangic": start,
                "bitis": end,
                "baslik": title,
                "aciklama": str(entry.get("aciklama", "")).strip(),
                "birim": str(entry.get("birim", "")).strip(),
            }
        )
    df = pd.DataFrame(rows, columns=columns).sort_values("baslangic") if rows else pd.DataFrame(columns=columns)
    return df, errors


def load_actions() -> tuple[pd.DataFrame, list[str]]:
    """İş birimi aksiyonları (tek gün ya da aralık): (baslangic, bitis, baslik, aciklama, birim) tablosu."""
    return _load_range_entries(ACTIONS_PATH, "aksiyon")


def load_exclusions() -> tuple[pd.DataFrame, list[str]]:
    """Hariç tutulan tarihler (tek gün ya da aralık): (baslangic, bitis, baslik, aciklama, birim) tablosu."""
    return _load_range_entries(EXCLUSIONS_PATH, "haric")


def overlaps_exclusion(df: pd.DataFrame, exclusions: pd.DataFrame) -> pd.Series:
    """Hesaplama penceresi (FIRST_OFFER_DATE → LAST_OFFER_DATE) hariç tutulan bir tarihe değen satırlar.

    1 günlük periyotta bu, LAST_OFFER_DATE'in hariç tarihlerden biri olması demektir. 7 günlük periyotta
    ise o günü içeren tüm pencereler (hariç günden sonraki 7 günün noktaları) etkilenir, çünkü pencere
    toplamı Oracle'da hazır gelir ve içinden tek bir gün çıkarılamaz.
    """
    first = df["FIRST_OFFER_DATE"].fillna(df["LAST_OFFER_DATE"])
    last = df["LAST_OFFER_DATE"]
    mask = pd.Series(False, index=df.index)
    for row in exclusions.itertuples():
        mask |= (first <= row.bitis) & (last >= row.baslangic)
    return mask
