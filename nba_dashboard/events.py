"""config/onemli_tarihler.toml dosyasındaki önemli tarihleri okur."""

from __future__ import annotations

import tomllib

import pandas as pd

from nba_dashboard.data import PROJECT_ROOT

EVENTS_PATH = PROJECT_ROOT / "config" / "onemli_tarihler.toml"


def load_events() -> tuple[pd.DataFrame, list[str]]:
    """(tarih, baslik, aciklama) tablosu ve okunamayan kayıtlar için hata mesajları döner."""
    empty = pd.DataFrame(columns=["tarih", "baslik", "aciklama"])
    if not EVENTS_PATH.exists():
        return empty, []
    try:
        with EVENTS_PATH.open("rb") as f:
            entries = tomllib.load(f).get("tarih", [])
    except tomllib.TOMLDecodeError as exc:
        return empty, [f"{EVENTS_PATH.name} okunamadı: {exc}"]

    rows, errors = [], []
    for i, entry in enumerate(entries, start=1):
        day = pd.to_datetime(str(entry.get("gun", "")), format="%d.%m.%Y", errors="coerce")
        title = str(entry.get("baslik", "")).strip()
        if pd.isna(day) or not title:
            errors.append(f"{EVENTS_PATH.name}, {i}. kayıt atlandı: 'gun' (GG.AA.YYYY) ve 'baslik' zorunlu.")
            continue
        rows.append({"tarih": day, "baslik": title, "aciklama": str(entry.get("aciklama", "")).strip()})
    return (pd.DataFrame(rows).sort_values("tarih") if rows else empty), errors
