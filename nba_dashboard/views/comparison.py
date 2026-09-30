"""Tek bir dönem için aksiyon grubu / model bazında Pilot ve NBA karşılaştırması."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from nba_dashboard import charts
from nba_dashboard.context import Context
from nba_dashboard.data import NO_MODEL_LABEL
from nba_dashboard.formatting import fmt_change, fmt_int, fmt_num, fmt_pct, fmt_points
from nba_dashboard.metrics import compare, total_of, verdict

GROUP_KEYS = ["ACTION_GROUP_CODE", "ACTION_GROUP_DESC", "MEVCUT_MODEL_KIMLIGI", "MODEL_FLAG"]

COUNT_FORMAT = "localized"
COLUMN_CONFIG = {
    "ACTION_GROUP_CODE": "Kod",
    "ACTION_GROUP_DESC": st.column_config.TextColumn("Aksiyon grubu", width="large"),
    "MEVCUT_MODEL_KIMLIGI": "Model",
    "pilot_yanitlayan": st.column_config.NumberColumn("Pilot yanıtlayan", format=COUNT_FORMAT),
    "nba_yanitlayan": st.column_config.NumberColumn("NBA yanıtlayan", format=COUNT_FORMAT),
    "pilot_olumlu": st.column_config.NumberColumn("Pilot olumlu", format=COUNT_FORMAT),
    "nba_olumlu": st.column_config.NumberColumn("NBA olumlu", format=COUNT_FORMAT),
    "pilot_satis": st.column_config.NumberColumn("Pilot satış", format=COUNT_FORMAT),
    "nba_satis": st.column_config.NumberColumn("NBA satış", format=COUNT_FORMAT),
    "pilot_satis_oran": st.column_config.NumberColumn("Pilot satış oranı", format="percent"),
    "nba_satis_oran": st.column_config.NumberColumn("NBA satış oranı", format="percent"),
    "satis_lift": st.column_config.NumberColumn("Satış lift", format="%.3f"),
    "pilot_olumlu_oran": st.column_config.NumberColumn("Pilot olumlu oranı", format="percent"),
    "nba_olumlu_oran": st.column_config.NumberColumn("NBA olumlu oranı", format="percent"),
    "olumlu_lift": st.column_config.NumberColumn("Olumlu lift", format="%.3f"),
    "satis_adet_farki": st.column_config.NumberColumn("Adet farkı", format="%+d"),
    "oran_bazli_ek_satis": st.column_config.NumberColumn("Oran bazlı ek satış", format="%+.0f"),
    "p_degeri": st.column_config.NumberColumn("p-değeri", format="%.3f"),
    "sonuc": "Sonuç",
}


def render(ctx: Context) -> None:
    df = ctx.df
    with st.sidebar:
        periods = (
            df.sort_values("LAST_OFFER_DATE", ascending=False)["DONEM"].drop_duplicates().tolist()
        )
        if not periods:
            st.warning("Seçili filtrelerle eşleşen kayıt yok.")
            st.stop()
        period = st.selectbox("Dönem", periods, help="Varsayılan: en güncel dönem")
        if ctx.removed_dates:
            st.caption(
                f"🔴 Hariç tutulan tarihlere denk gelen {len(ctx.removed_dates)} dönem listede yer almıyor."
            )
        min_resp = st.number_input(
            "Min. yanıtlayan (her iki grupta)",
            min_value=0,
            value=0,
            step=500,
            help="Pilot veya NBA tarafında bu sayıdan az yanıtlayanı olan aksiyon grupları hariç tutulur.",
        )

    df = df[df["DONEM"] == period]
    groups = compare(df, ctx.basis, by=GROUP_KEYS)
    groups = groups[groups["min_yanitlayan"] >= min_resp]
    groups["sonuc"] = groups.apply(verdict, axis=1)
    df = df[df["ACTION_GROUP_CODE"].isin(groups["ACTION_GROUP_CODE"])]

    st.title("Dönem Karşılaştırması")
    run_at = df["RUN_ALINAN_TARIH"].max()
    st.caption(
        f"{ctx.source_label} · Dönem: {period} · Veri tarihi: "
        f"{run_at:%d.%m.%Y %H:%M} · {ctx.basis_label} bazında · {len(groups)} aksiyon grubu"
    )
    if groups.empty:
        st.warning("Seçili filtrelerle eşleşen kayıt yok.")
        st.stop()

    total = compare(df, ctx.basis).iloc[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Pilot satış oranı",
        fmt_pct(total["pilot_satis_oran"]),
        delta=fmt_points(total["pilot_satis_oran"] - total["nba_satis_oran"]),
        help=f"{fmt_int(total['pilot_satis'])} satış / {fmt_int(total['pilot_yanitlayan'])} yanıtlayan",
    )
    c2.metric(
        "NBA satış oranı",
        fmt_pct(total["nba_satis_oran"]),
        help=f"{fmt_int(total['nba_satis'])} satış / {fmt_int(total['nba_yanitlayan'])} yanıtlayan",
    )
    c3.metric(
        "Satış lift",
        fmt_num(total["satis_lift"]),
        delta=fmt_change(total["satis_lift"]),
        help="Pilot satış oranı / NBA satış oranı",
    )
    c4.metric(
        "Olumlu yanıt lift",
        fmt_num(total["olumlu_lift"]),
        delta=fmt_change(total["olumlu_lift"]),
        help="Pilot olumlu oranı / NBA olumlu oranı",
    )
    c5.metric(
        "Oran bazlı ek satış",
        fmt_int(total["oran_bazli_ek_satis"], sign=True),
        help=(
            "Pilot satışı − (Pilot yanıtlayan × NBA satış oranı). Grup büyüklükleri farklı olduğu için "
            f"ham adet farkından ({fmt_int(total['satis_adet_farki'], sign=True)}) daha adil bir karşılaştırmadır."
        ),
    )

    counts = groups["sonuc"].value_counts()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("🔵 Pilot anlamlı olarak daha iyi", int(counts.get("Pilot daha iyi", 0)))
    s2.metric("🟠 NBA anlamlı olarak daha iyi", int(counts.get("NBA daha iyi", 0)))
    s3.metric("⚪ Fark anlamlı değil", int(counts.get("Fark anlamlı değil", 0)))
    s4.metric("Satış / karşılaştırma yok", int(counts.get("Satış yok", 0) + counts.get("Karşılaştırma yok", 0)))
    st.caption("Anlamlılık: satış oranları için iki oran z-testi, p < 0,05.")

    tab_lift, tab_scatter, tab_code, tab_table = st.tabs(
        ["Aksiyon grupları", "Pilot ve NBA oranları", "AG grup kodu bazında", "Detay tablo"]
    )

    with tab_lift:
        st.subheader("Satış oranı farkı (aksiyon grubu bazında)")
        st.caption("Sağa uzanan çubuk: Pilot daha yüksek satış oranına sahip. Renk, farkın anlamlı olup olmadığını gösterir.")
        st.plotly_chart(charts.lift_bars(groups), width="stretch")

    with tab_scatter:
        st.subheader("Pilot ve NBA satış oranları")
        st.caption(
            "Kesikli çizginin üstündeki noktalarda Pilot daha iyi. Nokta büyüklüğü = toplam yanıtlayan. "
            "Satışı sıfır olan gruplar log ölçekte gösterilemediği için dışarıda kalır."
        )
        st.plotly_chart(charts.rate_scatter(groups), width="stretch")

    with tab_code:
        by_code = groups.copy()
        by_code["etiket"] = by_code["ACTION_GROUP_CODE"] + " · " + by_code["ACTION_GROUP_DESC"].str.slice(0, 45)
        st.subheader("AG grup kodu bazında satış oranları")
        st.caption("Pilot ve NBA satış oranları yan yana. En çok yanıtlayanı olan kodlar üstte.")
        st.plotly_chart(charts.rate_bars(by_code, "etiket", model_col="MEVCUT_MODEL_KIMLIGI"), width="stretch")
        st.dataframe(
            by_code.sort_values("pilot_yanitlayan", ascending=False)[
                ["ACTION_GROUP_CODE", "ACTION_GROUP_DESC", "MEVCUT_MODEL_KIMLIGI", "pilot_yanitlayan", "nba_yanitlayan",
                 "pilot_satis", "nba_satis", "pilot_satis_oran", "nba_satis_oran", "satis_lift",
                 "oran_bazli_ek_satis", "p_degeri", "sonuc"]
            ],
            hide_index=True,
            width="stretch",
            column_config=COLUMN_CONFIG,
        )

    with tab_table:
        table = _filter_detail_table(groups)
        table = table.sort_values("pilot_yanitlayan", ascending=False)[
            ["ACTION_GROUP_CODE", "ACTION_GROUP_DESC", "MEVCUT_MODEL_KIMLIGI",
             "pilot_yanitlayan", "nba_yanitlayan", "pilot_olumlu", "nba_olumlu", "pilot_satis", "nba_satis",
             "pilot_satis_oran", "nba_satis_oran", "satis_lift", "pilot_olumlu_oran", "nba_olumlu_oran",
             "olumlu_lift", "satis_adet_farki", "oran_bazli_ek_satis", "p_degeri", "sonuc"]
        ]
        st.caption(
            f"{len(table)} / {len(groups)} aksiyon grubu gösteriliyor · En alttaki **dip toplam** satırı "
            "filtrelenmiş gruplardan hesaplanır: adetler toplanır, oran/lift/ek satış/p-değeri toplamdan yeniden hesaplanır."
        )
        shown = _with_total_row(table)
        st.dataframe(
            _highlight_last_row(shown) if len(shown) > len(table) else shown,
            hide_index=True,
            width="stretch",
            height=600,
            column_config=COLUMN_CONFIG,
        )
        st.download_button(
            "Excel için CSV indir",
            shown.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            file_name=f"nba_pilot_{ctx.basis.lower()}.csv",
            mime="text/csv",
            help="Tablonun filtrelenmiş hali, dip toplam satırıyla birlikte indirilir.",
        )

    if NO_MODEL_LABEL in groups["MEVCUT_MODEL_KIMLIGI"].values:
        st.caption(f"“{NO_MODEL_LABEL}”: MEVCUT_MODEL_KIMLIGI boş olan aksiyon grupları (MODEL_FLAG = 0).")


def _tr_lower(text: str) -> str:
    """Türkçe büyük/küçük harf duyarsız arama için (İ → i, I → ı)."""
    return text.replace("İ", "i").replace("I", "ı").lower()


def _filter_detail_table(groups: pd.DataFrame) -> pd.DataFrame:
    """Detay tablo sekmesinin kendi filtreleri. Yalnızca tabloyu ve CSV indirmesini etkiler."""
    c1, c2, c3 = st.columns([2, 2, 2])
    query = c1.text_input(
        "Ara (kod ya da aksiyon grubu)",
        placeholder="ör. 2015 ya da kredi kartı",
        help="Kodda ya da aksiyon grubu adında geçen metne göre süzer. Büyük/küçük harf fark etmez.",
    )
    models = c2.multiselect(
        "Model", sorted(groups["MEVCUT_MODEL_KIMLIGI"].unique()), placeholder="Tüm modeller"
    )
    verdicts = c3.multiselect("Sonuç", sorted(groups["sonuc"].unique()), placeholder="Tüm sonuçlar")

    table = groups
    if query.strip():
        q = _tr_lower(query.strip())
        haystack = (table["ACTION_GROUP_CODE"] + " " + table["ACTION_GROUP_DESC"]).map(_tr_lower)
        table = table[haystack.str.contains(q, regex=False)]
    if models:
        table = table[table["MEVCUT_MODEL_KIMLIGI"].isin(models)]
    if verdicts:
        table = table[table["sonuc"].isin(verdicts)]

    lifts = groups["satis_lift"].dropna()
    if len(lifts) > 1 and lifts.min() < lifts.max():
        lo, hi = float(np.floor(lifts.min() * 100) / 100), float(np.ceil(lifts.max() * 100) / 100)
        c4, c5 = st.columns([4, 2])
        lift_range = c4.slider(
            "Satış lift aralığı", min_value=lo, max_value=hi, value=(lo, hi), step=0.01, format="%.2f",
            help="1'in üstü Pilot, altı NBA lehine.",
        )
        keep_missing = c5.checkbox(
            "Lift'i hesaplanamayanları da göster",
            value=True,
            help="NBA satış oranı 0 olan ya da karşılaştırması olmayan gruplar (lift boş).",
        )
        in_range = table["satis_lift"].between(*lift_range)
        table = table[in_range | (table["satis_lift"].isna() & keep_missing)]
    return table


def _with_total_row(table: pd.DataFrame) -> pd.DataFrame:
    """Tablonun sonuna dip toplam satırı ekler (tablo boşsa olduğu gibi döner).

    Adet kolonları toplanır; oranlar, lift'ler, farklar ve p-değeri toplam adetlerden yeniden hesaplanır
    (kartlardaki toplamla aynı yöntem). Sıralama bozulmasın diye satır en sona eklenir.
    """
    if table.empty:
        return table
    total = total_of(table)
    row = {col: total[col] if col in total.index else None for col in table.columns}
    row["ACTION_GROUP_CODE"] = "Σ"
    row["ACTION_GROUP_DESC"] = f"DİP TOPLAM ({len(table)} grup)"
    row["MEVCUT_MODEL_KIMLIGI"] = f"{table['MEVCUT_MODEL_KIMLIGI'].nunique()} model"
    row["sonuc"] = verdict(total)
    return pd.concat([table.reset_index(drop=True), pd.DataFrame([row])], ignore_index=True)


def _highlight_last_row(df: pd.DataFrame):
    """Dip toplam satırını kalın ve hafif renkli gösterir."""
    last = len(df) - 1
    style = "font-weight: 700; background-color: rgba(42, 120, 214, 0.12)"
    return df.style.apply(lambda r: [style if r.name == last else ""] * len(r), axis=1)
