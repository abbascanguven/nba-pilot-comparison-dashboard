"""Veri yükleme: Oracle tablosundan (veya geliştirme için örnek dosyadan) tek seferde okur."""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Satır tipi: 1 = aksiyon grubu detayı, 2 = MODEL_FLAG=1 toplamı, 3 = genel toplam.
# Toplamları filtrelere göre kendimiz hesapladığımız için sadece detay satırları kullanılır.
DETAIL_ROW = 1

COUNT_COLUMNS = [
    f"{side}_{basis}_{kind}"
    for side in ("PILOT", "NBA")
    for basis in ("TEKIL", "TOPLAM")
    for kind in ("YANITLAYAN", "OLUMLU", "SATIS")
]
DATE_COLUMNS = ["RUN_ALINAN_TARIH", "FIRST_OFFER_DATE", "LAST_OFFER_DATE"]
NO_MODEL_LABEL = "(Model yok)"


def _normalize_column(name: str) -> str:
    """'Hesaplama Gün sayısı' -> 'HESAPLAMA_GUN_SAYISI'."""
    name = name.replace("ı", "i").replace("İ", "I")
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"\W+", "_", name.strip()).strip("_").upper()


def _read_oracle() -> pd.DataFrame:
    import oracledb

    table = os.environ["ORACLE_TABLE"]
    if not re.fullmatch(r"[A-Za-z0-9_$#.]+", table):
        raise ValueError(f"Geçersiz tablo adı: {table!r}")

    with oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
    ) as conn, conn.cursor() as cur:
        cur.arraysize = 5000
        cur.execute(f"SELECT * FROM {table}")
        columns = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columns)


def _read_file(path: Path) -> pd.DataFrame:
    sep = "," if path.suffix.lower() == ".csv" else "\t"
    return pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=_normalize_column)

    if "SIRALAMA_DEGERI" in df.columns:
        df = df[pd.to_numeric(df["SIRALAMA_DEGERI"], errors="coerce") == DETAIL_ROW]
    df = df[df["ACTION_GROUP_CODE"].astype(str).str.strip() != ""].copy()

    for col in COUNT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")
    for col in ("MODEL_FLAG", "HESAPLAMA_GUN_SAYISI", "INJECTION_POINT_ID"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in DATE_COLUMNS:
        if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    # Aynı pencere birden fazla kez çalıştırıldıysa sadece en son çalıştırma kullanılır.
    window_keys = ["INJECTION_POINT_ID", "FIRST_OFFER_DATE", "LAST_OFFER_DATE", "HESAPLAMA_GUN_SAYISI"]
    latest_run = df.groupby(window_keys, dropna=False)["RUN_ALINAN_TARIH"].transform("max")
    df = df[(df["RUN_ALINAN_TARIH"] == latest_run) | latest_run.isna()].copy()

    df["ACTION_GROUP_CODE"] = df["ACTION_GROUP_CODE"].astype(str).str.strip()
    df["ACTION_GROUP_DESC"] = df["ACTION_GROUP_DESC"].astype(str).str.strip()
    model = df["MEVCUT_MODEL_KIMLIGI"].fillna("").astype(str).str.strip()
    df["MEVCUT_MODEL_KIMLIGI"] = model.mask(model == "", NO_MODEL_LABEL)

    df["DONEM"] = (
        df["FIRST_OFFER_DATE"].dt.strftime("%d.%m.%Y")
        + " – "
        + df["LAST_OFFER_DATE"].dt.strftime("%d.%m.%Y")
        + " ("
        + df["HESAPLAMA_GUN_SAYISI"].astype(str)
        + " gün)"
    )
    return df.reset_index(drop=True)


def load_data() -> tuple[pd.DataFrame, str]:
    """Veriyi yükler ve (tablo, kaynak açıklaması) döner.

    DATA_SOURCE=oracle ise Oracle'dan, aksi halde SAMPLE_DATA_PATH dosyasından okur.
    """
    source = os.getenv("DATA_SOURCE", "file").lower()
    if source == "oracle":
        raw = _read_oracle()
        label = f"Oracle · {os.environ['ORACLE_TABLE']}"
    else:
        path = PROJECT_ROOT / os.getenv("SAMPLE_DATA_PATH", "data/sample_data.tsv")
        raw = _read_file(path)
        label = f"Örnek dosya · {path.name}"
    return _clean(raw), label
