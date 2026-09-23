"""Ana sayfa: Pilot ve NBA satış oranları ile satış adetlerinin günlük seyri."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from nba_dashboard import charts
from nba_dashboard.context import Context
from nba_dashboard.events import load_events
from nba_dashboard.formatting import fmt_int, fmt_num, fmt_pct, fmt_points
from nba_dashboard.metrics import compare


def render(ctx: Context) -> None:
    df = ctx.df.dropna(subset=["LAST_OFFER_DATE"])
    if df.empty:
        st.title("Günlük Trend")
        st.warning("Seçili filtrelerle eşleşen kayıt yok.")
        st.stop()

    first_day = df["LAST_OFFER_DATE"].min().date()
    last_day = df["LAST_OFFER_DATE"].max().date()
    with st.sidebar:
        date_range = st.date_input(
            "Tarih aralığı",
            value=(first_day, last_day),
            min_value=first_day,
            max_value=last_day,
            format="DD.MM.YYYY",
        )
    # Kullanıcı aralığın ilk gününü seçip ikincisini henüz seçmediyse tek değer gelir.
    start, end = (date_range + (last_day,))[:2] if isinstance(date_range, tuple) else (date_range, last_day)

    # Referans günü tarih aralığının dışında da seçilebilsin diye tüm günler hesaplanır.
    daily_all = compare(df, ctx.basis, by=["LAST_OFFER_DATE"]).sort_values("LAST_OFFER_DATE")
    daily = daily_all[daily_all["LAST_OFFER_DATE"].between(pd.Timestamp(start), pd.Timestamp(end))]
    if daily.empty:
        st.title("Günlük Trend")
        st.warning("Seçili tarih aralığında kayıt yok.")
        st.stop()

    last = daily.iloc[-1]
    ref_candidates = daily_all[daily_all["LAST_OFFER_DATE"] < last["LAST_OFFER_DATE"]]
    with st.sidebar:
        ref_mode = st.radio(
            "Karşılaştırma referansı",
            ["Bir önceki gün", "Seçilen gün"],
            horizontal=True,
            help="Son gün özetindeki değişimler hangi güne göre hesaplansın?",
        )
        ref = None
        if ref_candidates.empty:
            st.caption("Son günden önce kayıt olmadığı için karşılaştırma yapılamıyor.")
        elif ref_mode == "Bir önceki gün":
            ref = ref_candidates.iloc[-1]
        else:
            ref_dates = ref_candidates["LAST_OFFER_DATE"].sort_values(ascending=False).tolist()
            ref_date = st.selectbox(
                "Referans günü",
                ref_dates,
                format_func=lambda d: f"{d:%d.%m.%Y}",
                help=f"Son gün ({last['LAST_OFFER_DATE']:%d.%m.%Y}) bu günle karşılaştırılır.",
            )
            ref = ref_candidates[ref_candidates["LAST_OFFER_DATE"] == ref_date].iloc[0]
    ref_date = None if ref is None else ref["LAST_OFFER_DATE"]

    st.title("Günlük Trend")
    window = "1 günlük" if ctx.period_days == 1 else f"{ctx.period_days} günlük kayan pencere"
    st.caption(
        f"{ctx.source_label} · {window} · {ctx.basis_label} bazında · "
        f"{start:%d.%m.%Y} – {end:%d.%m.%Y} · {len(daily)} gün"
    )
    if ctx.period_days > 1:
        st.info(
            f"Her nokta, o tarihte biten {ctx.period_days} günlük pencerenin toplamıdır. "
            "Ardışık noktaların pencereleri örtüştüğü için eğri doğal olarak yumuşaktır.",
            icon="ℹ️",
        )
    # ---------------------------------------------------------------- son gün özeti
    def change(col: str, fmt):
        if ref is None or pd.isna(last[col] - ref[col]):
            return None
        return fmt(last[col] - ref[col])

    def ref_help(col: str, fmt) -> str | None:
        return None if ref is None else f"Referans ({ref_date:%d.%m.%Y}): {fmt(ref[col])}"

    if ref is None:
        ref_text = "karşılaştırılacak önceki gün yok"
    elif ref_mode == "Bir önceki gün":
        ref_text = f"değişimler bir önceki güne ({ref_date:%d.%m.%Y}) göre"
    else:
        ref_text = f"değişimler seçilen referans güne (**{ref_date:%d.%m.%Y}**) göre"
    st.markdown(f"**Son gün: {last['LAST_OFFER_DATE']:%d.%m.%Y}** · {ref_text}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Pilot satış oranı", fmt_pct(last["pilot_satis_oran"]),
        delta=change("pilot_satis_oran", fmt_points), help=ref_help("pilot_satis_oran", fmt_pct),
    )
    c2.metric(
        "NBA satış oranı", fmt_pct(last["nba_satis_oran"]),
        delta=change("nba_satis_oran", fmt_points), help=ref_help("nba_satis_oran", fmt_pct),
    )
    c3.metric(
        "Satış lift", fmt_num(last["satis_lift"]),
        delta=change("satis_lift", lambda v: fmt_num(v, sign=True)), help=ref_help("satis_lift", fmt_num),
    )
    c4.metric(
        "Pilot satış", fmt_int(last["pilot_satis"]),
        delta=change("pilot_satis", lambda v: fmt_int(v, sign=True)), help=ref_help("pilot_satis", fmt_int),
    )
    c5.metric(
        "NBA satış", fmt_int(last["nba_satis"]),
        delta=change("nba_satis", lambda v: fmt_int(v, sign=True)), help=ref_help("nba_satis", fmt_int),
    )

    # ---------------------------------------------------------------- grafikler
    events, event_errors = load_events()
    for msg in event_errors:
        st.warning(msg)
    st.subheader("Satış oranı")
    st.plotly_chart(
        charts.time_lines(
            daily, "satis_oran", "Satış oranı", ".2%", ".3%",
            from_zero=False, ref_date=ref_date, events=events,
        ),
        width="stretch",
    )

    st.subheader("Satış adedi")
    st.plotly_chart(
        charts.time_lines(
            daily, "satis", "Satış adedi", ",d", ",d",
            from_zero=True, ref_date=ref_date, events=events,
        ),
        width="stretch",
    )

    with st.expander("Satış lift (Pilot / NBA)", expanded=False):
        st.plotly_chart(charts.lift_line(daily, ref_date=ref_date, events=events), width="stretch")

    visible_events = events[events["tarih"].between(daily["LAST_OFFER_DATE"].min(), daily["LAST_OFFER_DATE"].max())]
    with st.expander(f"📌 Önemli tarihler ({len(visible_events)})", expanded=False):
        if visible_events.empty:
            st.caption("Seçili tarih aralığında önemli tarih yok.")
        else:
            st.dataframe(
                visible_events,
                hide_index=True,
                width="stretch",
                column_config={
                    "tarih": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
                    "baslik": "Başlık",
                    "aciklama": st.column_config.TextColumn("Açıklama", width="large"),
                },
            )
        st.caption("Tarihler `config/onemli_tarihler.toml` dosyasından okunur.")

    with st.expander("Günlük değerler tablosu", expanded=False):
        table = daily[
            ["LAST_OFFER_DATE", "pilot_yanitlayan", "nba_yanitlayan", "pilot_satis", "nba_satis",
             "pilot_satis_oran", "nba_satis_oran", "satis_lift", "satis_adet_farki", "oran_bazli_ek_satis"]
        ].sort_values("LAST_OFFER_DATE", ascending=False)
        st.dataframe(
            table,
            hide_index=True,
            width="stretch",
            column_config={
                "LAST_OFFER_DATE": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
                "pilot_yanitlayan": st.column_config.NumberColumn("Pilot yanıtlayan", format="localized"),
                "nba_yanitlayan": st.column_config.NumberColumn("NBA yanıtlayan", format="localized"),
                "pilot_satis": st.column_config.NumberColumn("Pilot satış", format="localized"),
                "nba_satis": st.column_config.NumberColumn("NBA satış", format="localized"),
                "pilot_satis_oran": st.column_config.NumberColumn("Pilot satış oranı", format="percent"),
                "nba_satis_oran": st.column_config.NumberColumn("NBA satış oranı", format="percent"),
                "satis_lift": st.column_config.NumberColumn("Satış lift", format="%.3f"),
                "satis_adet_farki": st.column_config.NumberColumn("Adet farkı", format="%+d"),
                "oran_bazli_ek_satis": st.column_config.NumberColumn("Oran bazlı ek satış", format="%+.0f"),
            },
        )
        st.download_button(
            "Excel için CSV indir",
            table.to_csv(index=False, sep=";", decimal=",", date_format="%d.%m.%Y").encode("utf-8-sig"),
            file_name=f"nba_pilot_trend_{ctx.period_days}g_{ctx.basis.lower()}.csv",
            mime="text/csv",
        )
