"""Geliştirme için SENTETİK günlük veri üretir (gerçek veri değildir).

data/sample_data.tsv içindeki aksiyon gruplarının hacim ve oranlarını baz alarak,
her gün için 1 günlük ve 7 günlük pencereli satırlar oluşturur.

    python scripts/make_demo_data.py [--days 30] [--end 22.09.2026]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nba_dashboard.data import _clean, _read_file  # noqa: E402

WINDOWS = (1, 7)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--end", default="22.09.2026")
    parser.add_argument("--out", default="data/demo_timeseries.tsv")
    args = parser.parse_args()

    base = _clean(_read_file(ROOT / "data/sample_data.tsv"))
    base = base[base["LAST_OFFER_DATE"] == base["LAST_OFFER_DATE"].max()]
    base = base[base["HESAPLAMA_GUN_SAYISI"] == base["HESAPLAMA_GUN_SAYISI"].max()]
    base_days = int(base["HESAPLAMA_GUN_SAYISI"].iloc[0])

    rng = np.random.default_rng(42)
    end = datetime.strptime(args.end, "%d.%m.%Y")
    n_days = args.days + max(WINDOWS) - 1
    dates = [end - timedelta(days=n_days - 1 - i) for i in range(n_days)]
    weekday_factor = np.array([0.7 if d.weekday() >= 5 else 1.0 for d in dates])
    # Pilot'un NBA'ya göre üstünlüğü zamanla hafifçe artsın (demo için görünür bir eğilim).
    pilot_trend = np.linspace(0.97, 1.08, n_days)

    rows = []
    for _, g in base.iterrows():
        daily = {}
        for side in ("PILOT", "NBA"):
            resp_mean = g[f"{side}_TEKIL_YANITLAYAN"] / base_days
            resp = rng.poisson(np.maximum(resp_mean * weekday_factor, 0))
            n = max(g[f"{side}_TEKIL_YANITLAYAN"], 1)
            pos_rate = g[f"{side}_TEKIL_OLUMLU"] / n
            sale_rate = g[f"{side}_TEKIL_SATIS"] / n
            if side == "PILOT":
                sale_rate = np.clip(sale_rate * pilot_trend, 0, 1)
            daily[side] = {
                "YANITLAYAN": resp,
                "OLUMLU": rng.binomial(resp, min(pos_rate, 1)),
                "SATIS": rng.binomial(resp, sale_rate),
            }
            # Toplam = tekil + küçük tekrar oranı
            for kind in ("YANITLAYAN", "OLUMLU", "SATIS"):
                daily[side][f"TOPLAM_{kind}"] = daily[side][kind] + rng.binomial(daily[side][kind], 0.01)

        for w in WINDOWS:
            for i in range(max(WINDOWS) - 1, n_days):
                sl = slice(i - w + 1, i + 1)
                row = {
                    "INJECTION_POINT_ID": g["INJECTION_POINT_ID"],
                    "ACTION_GROUP_CODE": g["ACTION_GROUP_CODE"],
                    "ACTION_GROUP_DESC": g["ACTION_GROUP_DESC"],
                    "MEVCUT_MODEL_KIMLIGI": "" if g["MODEL_FLAG"] != 1 else g["MEVCUT_MODEL_KIMLIGI"],
                }
                for side in ("PILOT", "NBA"):
                    for kind in ("YANITLAYAN", "OLUMLU", "SATIS"):
                        row[f"{side}_TEKIL_{kind}"] = int(daily[side][kind][sl].sum())
                        row[f"{side}_TOPLAM_{kind}"] = int(daily[side][f"TOPLAM_{kind}"][sl].sum())
                row.update(
                    MODEL_FLAG=int(g["MODEL_FLAG"]),
                    SIRALAMA_DEGERI=1,
                    RUN_ALINAN_TARIH=(dates[i] + timedelta(days=1, hours=6)).strftime("%d.%m.%Y %H:%M"),
                    FIRST_OFFER_DATE=dates[i - w + 1].strftime("%d.%m.%Y"),
                    LAST_OFFER_DATE=dates[i].strftime("%d.%m.%Y"),
                    HESAPLAMA_GUN_SAYISI=w,
                )
                rows.append(row)

    out = ROOT / args.out
    pd.DataFrame(rows).to_csv(out, sep="\t", index=False)
    print(f"{len(rows)} satır yazıldı: {out}")


if __name__ == "__main__":
    main()
