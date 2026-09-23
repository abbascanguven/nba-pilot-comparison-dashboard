"""Pilot ve NBA karşılaştırma metrikleri.

Oranlar ve lift'ler, hazır oran kolonlarının ortalaması alınarak değil, filtrelenmiş
satırların adetleri toplanarak yeniden hesaplanır. Böylece toplamlar her filtrede doğru kalır.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

SIGNIFICANCE_LEVEL = 0.05


def _col(side: str, basis: str, kind: str) -> str:
    return f"{side}_{basis}_{kind}"


def _safe_div(a, b):
    a = np.asarray(a, dtype="float64")
    b = np.asarray(b, dtype="float64")
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(b > 0, a / b, np.nan)
    return out


def _two_proportion_p(x1, n1, x2, n2) -> np.ndarray:
    """İki oran z-testi (çift taraflı) p-değeri."""
    x1, n1, x2, n2 = (np.asarray(v, dtype="float64") for v in (x1, n1, x2, n2))
    with np.errstate(divide="ignore", invalid="ignore"):
        pooled = (x1 + x2) / (n1 + n2)
        se = np.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
        z = (x1 / n1 - x2 / n2) / se
    p = np.array([math.erfc(abs(v) / math.sqrt(2)) if np.isfinite(v) else np.nan for v in np.atleast_1d(z)])
    return p


def compare(df: pd.DataFrame, basis: str, by: list[str] | None = None) -> pd.DataFrame:
    """Pilot ve NBA metriklerini `by` kolonlarına göre (yoksa tek satır toplam) hesaplar.

    basis: "TEKIL" (tekil müşteri) ya da "TOPLAM" (toplam yanıt).
    """
    counts = {
        f"{side.lower()}_{kind.lower()}": _col(side, basis, kind)
        for side in ("PILOT", "NBA")
        for kind in ("YANITLAYAN", "OLUMLU", "SATIS")
    }
    if by:
        g = df.groupby(by, dropna=False)[list(counts.values())].sum().reset_index()
    else:
        g = df[list(counts.values())].sum().to_frame().T
    g = g.rename(columns={v: k for k, v in counts.items()})

    g["pilot_satis_oran"] = _safe_div(g["pilot_satis"], g["pilot_yanitlayan"])
    g["nba_satis_oran"] = _safe_div(g["nba_satis"], g["nba_yanitlayan"])
    g["pilot_olumlu_oran"] = _safe_div(g["pilot_olumlu"], g["pilot_yanitlayan"])
    g["nba_olumlu_oran"] = _safe_div(g["nba_olumlu"], g["nba_yanitlayan"])

    g["satis_lift"] = _safe_div(g["pilot_satis_oran"], g["nba_satis_oran"])
    g["olumlu_lift"] = _safe_div(g["pilot_olumlu_oran"], g["nba_olumlu_oran"])
    g["satis_adet_farki"] = g["pilot_satis"] - g["nba_satis"]
    g["adet_lift"] = _safe_div(g["pilot_satis"], g["nba_satis"])

    # Grup büyüklükleri farklı olduğu için adet farkı yanıltıcı olabilir.
    # Pilot kitlesi NBA oranıyla satsaydı ne olurdu? Farkı "oran bazlı ek satış" olarak gösteriyoruz.
    g["oran_bazli_ek_satis"] = g["pilot_satis"] - g["pilot_yanitlayan"] * g["nba_satis_oran"]

    g["p_degeri"] = _two_proportion_p(
        g["pilot_satis"], g["pilot_yanitlayan"], g["nba_satis"], g["nba_yanitlayan"]
    )
    g["anlamli"] = g["p_degeri"] < SIGNIFICANCE_LEVEL
    g["min_yanitlayan"] = g[["pilot_yanitlayan", "nba_yanitlayan"]].min(axis=1)
    return g


def verdict(row: pd.Series) -> str:
    """Tek satır için okunabilir sonuç etiketi."""
    if row["nba_yanitlayan"] == 0 or row["pilot_yanitlayan"] == 0:
        return "Karşılaştırma yok"
    if row["pilot_satis"] + row["nba_satis"] == 0:
        return "Satış yok"
    if not row["anlamli"]:
        return "Fark anlamlı değil"
    return "Pilot daha iyi" if row["pilot_satis_oran"] > row["nba_satis_oran"] else "NBA daha iyi"
