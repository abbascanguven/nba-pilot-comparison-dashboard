"""NBA pilot karşılaştırma dashboard'u.

Çalıştırma:  streamlit run app.py

Ortak filtreler (periyot, hesaplama bazı, model, aksiyon grup kodu) burada çizilir ve tüm
sayfalarda geçerlidir; sayfalar kendi ek filtrelerini (dönem, tarih aralığı) ekler.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from nba_dashboard.context import Context
from nba_dashboard.data import load_data
from nba_dashboard.events import load_exclusions, overlaps_exclusion
from nba_dashboard.views import comparison, trend

st.set_page_config(page_title="NBA Pilot Karşılaştırma", page_icon="📊", layout="wide")


@st.cache_data(show_spinner="Veri yükleniyor…")
def get_data() -> tuple[pd.DataFrame, str]:
    return load_data()


try:
    data, source_label = get_data()
except Exception as exc:  # bağlantı / konfigürasyon hatası kullanıcıya gösterilsin
    st.error(f"Veri yüklenemedi: {exc}")
    st.stop()


def trend_page() -> None:
    trend.render(ctx)


def comparison_page() -> None:
    comparison.render(ctx)


page = st.navigation(
    [
        st.Page(trend_page, title="Günlük Trend", icon="📈", url_path="trend", default=True),
        st.Page(comparison_page, title="Dönem Karşılaştırması", icon="📊", url_path="karsilastirma"),
    ]
)

with st.sidebar:
    st.header("Filtreler")

    period_options = sorted(data["HESAPLAMA_GUN_SAYISI"].dropna().unique().tolist())
    period_days = st.radio(
        "Periyot",
        period_options,
        format_func=lambda n: f"{n} günlük",
        horizontal=True,
        key="period_days",
        help="Hesaplama penceresinin uzunluğu (HESAPLAMA_GUN_SAYISI)",
    )
    df = data[data["HESAPLAMA_GUN_SAYISI"] == period_days]

    injection_points = sorted(df["INJECTION_POINT_ID"].dropna().unique().tolist())
    if len(injection_points) > 1:
        chosen_ip = st.multiselect("Injection point", injection_points, default=injection_points, key="ip")
        df = df[df["INJECTION_POINT_ID"].isin(chosen_ip)]

    basis_label = st.radio(
        "Hesaplama bazı",
        ["Tekil", "Toplam"],
        horizontal=True,
        key="basis",
        help="Tekil: tekil müşteri sayıları · Toplam: toplam yanıt/satış adetleri",
    )

    model_state = st.radio("Model durumu", ["Tümü", "Modelli", "Modelsiz"], horizontal=True, key="model_state")
    if model_state == "Modelli":
        df = df[df["MODEL_FLAG"] == 1]
    elif model_state == "Modelsiz":
        df = df[df["MODEL_FLAG"] != 1]

    model_options = sorted(df["MEVCUT_MODEL_KIMLIGI"].unique().tolist())
    chosen_models = st.multiselect("Model", model_options, placeholder="Tüm modeller", key="models")
    if chosen_models:
        df = df[df["MEVCUT_MODEL_KIMLIGI"].isin(chosen_models)]

    code_names = (
        df.drop_duplicates("ACTION_GROUP_CODE").set_index("ACTION_GROUP_CODE")["ACTION_GROUP_DESC"].to_dict()
    )
    code_options = sorted(code_names, key=lambda c: (not c.isdigit(), int(c) if c.isdigit() else 0, c))
    chosen_codes = st.multiselect(
        "Aksiyon grup kodu",
        code_options,
        format_func=lambda c: f"{c} · {code_names.get(c, '')}",
        placeholder="Tüm kodlar",
        key="codes",
        help="Kod ya da açıklama yazarak arayabilirsiniz.",
    )
    if chosen_codes:
        df = df[df["ACTION_GROUP_CODE"].isin(chosen_codes)]

    exclusions, exclusion_errors = load_exclusions()
    for msg in exclusion_errors:
        st.warning(msg)
    removed_dates: tuple[pd.Timestamp, ...] = ()
    exclude = False
    if not exclusions.empty:
        exclude = st.toggle(
            "Hariç tutulan tarihleri çıkar",
            value=False,
            key="exclude",
            help=(
                "config/haric_tutulan_tarihler.toml dosyasındaki tarihlere denk gelen veriler tüm "
                "hesaplamalardan çıkarılır. 7 günlük periyotta, o tarihleri içeren tüm pencereler çıkarılır."
            ),
        )
        if exclude:
            hit = overlaps_exclusion(df, exclusions)
            removed_dates = tuple(pd.DatetimeIndex(df.loc[hit, "LAST_OFFER_DATE"].dropna().unique()).sort_values())
            df = df[~hit]
            st.caption(f"🔴 {len(exclusions)} tarih kaydı tanımlı · {len(removed_dates)} gün hesaplamadan çıkarıldı")
        else:
            st.caption(f"🔴 {len(exclusions)} tarih kaydı tanımlı · hesaplamaya dahil")

    if st.button("Veriyi yenile", width="stretch"):
        get_data.clear()
        st.rerun()
    st.divider()

ctx = Context(
    df=df,
    basis=basis_label.upper(),
    basis_label=basis_label,
    period_days=int(period_days),
    source_label=source_label,
    exclusions=exclusions,
    exclude_active=exclude,
    removed_dates=removed_dates,
)
page.run()
