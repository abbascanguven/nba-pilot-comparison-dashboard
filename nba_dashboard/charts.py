"""Plotly grafikleri. Renkler: Pilot = mavi, NBA = turuncu, anlamlı olmayan fark = gri."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

PILOT_COLOR = "#2a78d6"
NBA_COLOR = "#eb6834"
NEUTRAL_COLOR = "#a3a29c"
EVENT_COLOR = "#4a3aa7"

VERDICT_COLORS = {
    "Pilot daha iyi": PILOT_COLOR,
    "NBA daha iyi": NBA_COLOR,
    "Fark anlamlı değil": NEUTRAL_COLOR,
}

_HOVER = (
    "<b>%{customdata[0]}</b><br>"
    "Pilot: %{customdata[1]:,} yanıt · %{customdata[2]:,} satış · %{customdata[3]:.3%}<br>"
    "NBA: %{customdata[4]:,} yanıt · %{customdata[5]:,} satış · %{customdata[6]:.3%}<br>"
    "Satış lift: %{customdata[7]:.3f} · p = %{customdata[8]:.3f}"
    "<extra>%{customdata[9]}</extra>"
)
_HOVER_COLS = [
    "ACTION_GROUP_DESC", "pilot_yanitlayan", "pilot_satis", "pilot_satis_oran",
    "nba_yanitlayan", "nba_satis", "nba_satis_oran", "satis_lift", "p_degeri", "sonuc",
]


def _layout(fig: go.Figure, height: int, **kwargs) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0),
        hoverlabel=dict(align="left"),
        separators=",.",  # Türkçe: ondalık virgül, binlik nokta
        **kwargs,
    )
    fig.update_xaxes(gridcolor="rgba(128,128,128,0.15)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.15)", zeroline=False)
    return fig


def lift_bars(groups: pd.DataFrame) -> go.Figure:
    """Aksiyon grubu başına pilot satış oranının NBA'ya göre % farkı."""
    d = groups.dropna(subset=["satis_lift"]).copy()
    d["fark_yuzde"] = (d["satis_lift"] - 1) * 100
    d = d.sort_values("fark_yuzde")

    fig = go.Figure()
    for label, color in VERDICT_COLORS.items():
        part = d[d["sonuc"] == label]
        if part.empty:
            continue
        fig.add_bar(
            x=part["fark_yuzde"],
            y=part["ACTION_GROUP_DESC"],
            orientation="h",
            name=label,
            marker=dict(color=color, cornerradius=4),
            customdata=part[_HOVER_COLS].to_numpy(),
            hovertemplate=_HOVER,
        )
    fig.add_vline(x=0, line_width=1, line_color="rgba(128,128,128,0.6)")
    fig.update_xaxes(title="Pilot satış oranı, NBA'ya göre (% fark)", ticksuffix="%")
    fig.update_yaxes(categoryorder="array", categoryarray=d["ACTION_GROUP_DESC"].tolist())
    return _layout(fig, height=max(320, 22 * len(d) + 90), barmode="overlay", bargap=0.25)


def rate_scatter(groups: pd.DataFrame) -> go.Figure:
    """NBA satış oranı (x) ve Pilot satış oranı (y). Köşegenin üstü = Pilot daha iyi."""
    d = groups[(groups["pilot_satis_oran"] > 0) & (groups["nba_satis_oran"] > 0)].copy()
    size = np.sqrt(d["pilot_yanitlayan"] + d["nba_yanitlayan"])
    d["marker_size"] = 8 + 32 * size / size.max() if len(d) else []

    fig = go.Figure()
    for label, color in VERDICT_COLORS.items():
        part = d[d["sonuc"] == label]
        if part.empty:
            continue
        fig.add_scatter(
            x=part["nba_satis_oran"],
            y=part["pilot_satis_oran"],
            mode="markers",
            name=label,
            marker=dict(size=part["marker_size"], color=color, opacity=0.8, line=dict(width=2, color="white")),
            customdata=part[_HOVER_COLS].to_numpy(),
            hovertemplate=_HOVER,
        )
    if len(d):
        lo = min(d["nba_satis_oran"].min(), d["pilot_satis_oran"].min()) * 0.7
        hi = max(d["nba_satis_oran"].max(), d["pilot_satis_oran"].max()) * 1.4
        fig.add_scatter(
            x=[lo, hi], y=[lo, hi], mode="lines", name="Eşit oran",
            line=dict(color="rgba(128,128,128,0.6)", width=1, dash="dash"), hoverinfo="skip",
        )
    fig.update_xaxes(type="log", title="NBA satış oranı", tickformat=".2%")
    fig.update_yaxes(type="log", title="Pilot satış oranı", tickformat=".2%")
    return _layout(fig, height=520)


def rate_bars(d: pd.DataFrame, label_col: str) -> go.Figure:
    """`label_col` kategorileri için Pilot ve NBA satış oranı yan yana (en kalabalık üstte)."""
    d = d.sort_values("pilot_yanitlayan")
    fig = go.Figure()
    # Yatay gruplu çubukta ilk iz altta çizilir; Pilot üstte görünsün diye NBA önce eklenir.
    for side, name, color in (("nba", "NBA", NBA_COLOR), ("pilot", "Pilot", PILOT_COLOR)):
        fig.add_bar(
            x=d[f"{side}_satis_oran"],
            y=d[label_col],
            orientation="h",
            name=name,
            marker=dict(color=color, cornerradius=4),
            customdata=d[[f"{side}_yanitlayan", f"{side}_satis"]].to_numpy(),
            hovertemplate="%{y}<br>" + name + ": %{x:.3%} (%{customdata[1]:,} / %{customdata[0]:,})<extra></extra>",
        )
    fig.update_xaxes(title="Satış oranı", tickformat=".2%")
    fig.update_yaxes(categoryorder="array", categoryarray=d[label_col].tolist())
    return _layout(fig, height=max(320, 34 * len(d) + 90), barmode="group", bargap=0.25, bargroupgap=0.05,
                   legend_traceorder="reversed")


def _mark_reference(fig: go.Figure, ref_date: pd.Timestamp | None, daily: pd.DataFrame) -> None:
    """Referans gününü dikey kesikli çizgiyle işaretler (gösterilen aralıktaysa)."""
    if ref_date is None or daily.empty:
        return
    if not daily["LAST_OFFER_DATE"].min() <= ref_date <= daily["LAST_OFFER_DATE"].max():
        return
    # add_vline'ın annotation parametresi tarih ekseninde hata verdiği için şekil + not ayrı eklenir.
    fig.add_shape(
        type="line", x0=ref_date, x1=ref_date, y0=0, y1=1, yref="paper",
        line=dict(color="rgba(128,128,128,0.8)", width=1, dash="dot"),
    )
    fig.add_annotation(
        x=ref_date, y=1, yref="paper", text="Referans", showarrow=False,
        xanchor="left", yanchor="top", xshift=4, font=dict(size=11),
    )


def _mark_events(fig: go.Figure, events: pd.DataFrame | None, daily: pd.DataFrame, y_col: str) -> None:
    """Önemli tarihleri dikey çizgi + 📌 etiketiyle işaretler; üzerine gelince açıklama görünür."""
    if events is None or events.empty or daily.empty:
        return
    lo, hi = daily["LAST_OFFER_DATE"].min(), daily["LAST_OFFER_DATE"].max()
    ev = events[events["tarih"].between(lo, hi)]
    if ev.empty:
        return

    def describe(g: pd.DataFrame) -> str:
        return "<br>".join(
            f"<b>{r.baslik}</b>" + (f"<br>{r.aciklama}" if r.aciklama else "") for r in g.itertuples()
        )

    by_day = ev.groupby("tarih").apply(describe, include_groups=False)
    for day, text in by_day.items():
        fig.add_shape(
            type="line", x0=day, x1=day, y0=0, y1=1, yref="paper",
            line=dict(color=EVENT_COLOR, width=1, dash="dash"), opacity=0.6,
        )
        fig.add_annotation(
            x=day, y=1, yref="paper", yanchor="bottom", text="📌", showarrow=False,
            hovertext=f"{day:%d.%m.%Y}<br>{text}", font=dict(size=14),
        )
    # Günün üzerine gelindiğinde birleşik hover kutusunda da açıklama görünsün.
    points = daily.set_index("LAST_OFFER_DATE")[y_col].reindex(by_day.index)
    fig.add_scatter(
        x=by_day.index, y=points.values, mode="markers", name="📌 Önemli tarih",
        marker=dict(size=1, opacity=0), showlegend=False,
        customdata=by_day.values, hovertemplate="📌 %{customdata}<extra></extra>",
    )


def time_lines(
    daily: pd.DataFrame,
    metric: str,
    y_title: str,
    y_format: str,
    hover_format: str,
    from_zero: bool,
    ref_date: pd.Timestamp | None = None,
    events: pd.DataFrame | None = None,
) -> go.Figure:
    """Pilot ve NBA için `{side}_{metric}` kolonlarının günlük seyri."""
    fig = go.Figure()
    for side, name, color in (("pilot", "Pilot", PILOT_COLOR), ("nba", "NBA", NBA_COLOR)):
        col = f"{side}_{metric}"
        fig.add_scatter(
            x=daily["LAST_OFFER_DATE"],
            y=daily[col],
            mode="lines+markers",
            name=name,
            line=dict(color=color, width=2),
            marker=dict(size=8, color=color, line=dict(width=2, color="white")),
            hovertemplate=f"{name}: %{{y:{hover_format}}}<extra></extra>",
        )
        # Son noktaya doğrudan etiket: renk tek başına kimlik taşımasın.
        last = daily.dropna(subset=[col]).tail(1)
        if not last.empty:
            fig.add_annotation(
                x=last["LAST_OFFER_DATE"].iloc[0], y=last[col].iloc[0], text=name,
                showarrow=False, xanchor="left", xshift=10, font=dict(size=12),
            )
    fig.update_xaxes(tickformat="%d.%m", hoverformat="%d.%m.%Y", title=None)
    fig.update_yaxes(title=y_title, tickformat=y_format, rangemode="tozero" if from_zero else "normal")
    _mark_reference(fig, ref_date, daily)
    _mark_events(fig, events, daily, f"pilot_{metric}")
    fig = _layout(fig, height=360, hovermode="x unified")
    fig.update_layout(margin=dict(r=50))
    return fig


def lift_line(
    daily: pd.DataFrame, ref_date: pd.Timestamp | None = None, events: pd.DataFrame | None = None
) -> go.Figure:
    """Günlük satış lift (Pilot oranı / NBA oranı); 1 çizgisi eşitlik."""
    fig = go.Figure()
    fig.add_scatter(
        x=daily["LAST_OFFER_DATE"],
        y=daily["satis_lift"],
        mode="lines+markers",
        name="Satış lift",
        line=dict(color=PILOT_COLOR, width=2),
        marker=dict(size=8, color=PILOT_COLOR, line=dict(width=2, color="white")),
        hovertemplate="Satış lift: %{y:.3f}<extra></extra>",
        showlegend=False,
    )
    fig.add_hline(y=1, line_width=1, line_dash="dash", line_color="rgba(128,128,128,0.7)",
                  annotation_text="Eşit (1,0)", annotation_position="bottom right")
    fig.update_xaxes(tickformat="%d.%m", hoverformat="%d.%m.%Y", title=None)
    fig.update_yaxes(title="Satış lift", tickformat=".2f")
    _mark_reference(fig, ref_date, daily)
    _mark_events(fig, events, daily, "satis_lift")
    return _layout(fig, height=300, hovermode="x unified")
