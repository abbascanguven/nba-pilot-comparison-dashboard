"""Plotly grafikleri. Renkler: Pilot = mavi, NBA = turuncu, anlamlı olmayan fark = gri."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

PILOT_COLOR = "#2a78d6"
NBA_COLOR = "#eb6834"
NEUTRAL_COLOR = "#a3a29c"
EVENT_COLOR = "#4a3aa7"
ACTION_COLOR = "#e69500"  # kehribar: uyarı hissi, hariç tutmanın kırmızısından ayrı
EXCLUSION_COLOR = "#d03b3b"

VERDICT_COLORS = {
    "Pilot daha iyi": PILOT_COLOR,
    "NBA daha iyi": NBA_COLOR,
    "Fark anlamlı değil": NEUTRAL_COLOR,
}

_HOVER = (
    "<b>%{customdata[0]}</b><br>"
    "Model: %{customdata[10]}<br>"
    "Pilot: %{customdata[1]:,} yanıt · %{customdata[2]:,} satış · %{customdata[3]:.3%}<br>"
    "NBA: %{customdata[4]:,} yanıt · %{customdata[5]:,} satış · %{customdata[6]:.3%}<br>"
    "Satış lift: %{customdata[7]:.3f} · p = %{customdata[8]:.3f}"
    "<extra>%{customdata[9]}</extra>"
)
_HOVER_COLS = [
    "ACTION_GROUP_DESC", "pilot_yanitlayan", "pilot_satis", "pilot_satis_oran",
    "nba_yanitlayan", "nba_satis", "nba_satis_oran", "satis_lift", "p_degeri", "sonuc",
    "MEVCUT_MODEL_KIMLIGI",
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


def rate_bars(d: pd.DataFrame, label_col: str, model_col: str | None = None) -> go.Figure:
    """`label_col` kategorileri için Pilot ve NBA satış oranı yan yana (en kalabalık üstte).

    model_col verilirse, çubuğun üzerine gelince bağlı olduğu model de gösterilir.
    """
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
            customdata=d[[f"{side}_yanitlayan", f"{side}_satis"] + ([model_col] if model_col else [])].to_numpy(),
            hovertemplate=(
                "%{y}<br>"
                + ("Model: %{customdata[2]}<br>" if model_col else "")
                + name + ": %{x:.3%} (%{customdata[1]:,} / %{customdata[0]:,})<extra></extra>"
            ),
        )
    fig.update_xaxes(title="Satış oranı", tickformat=".2%")
    fig.update_yaxes(categoryorder="array", categoryarray=d[label_col].tolist())
    return _layout(fig, height=max(320, 34 * len(d) + 90), barmode="group", bargap=0.25, bargroupgap=0.05,
                   legend_traceorder="reversed")


def _mark_reference(
    fig: go.Figure, ref_date: pd.Timestamp | tuple[pd.Timestamp, pd.Timestamp] | None, daily: pd.DataFrame
) -> None:
    """Referansı işaretler: tek gün gri noktalı çizgi, ortalama aralığı gri bant (gösterilen aralıktaysa)."""
    if ref_date is None or daily.empty:
        return
    lo, hi = daily["LAST_OFFER_DATE"].min(), daily["LAST_OFFER_DATE"].max()
    if isinstance(ref_date, tuple):
        start, end = ref_date
        if end < lo or start > hi:
            return
        half_day = pd.Timedelta(hours=12)
        x0, x1 = max(start, lo) - half_day, min(end, hi) + half_day
        fig.add_shape(
            type="rect", x0=x0, x1=x1, y0=0, y1=1, yref="paper",
            fillcolor="rgba(128,128,128,0.10)", line=dict(width=0), layer="below",
        )
        fig.add_annotation(
            x=x0, y=1, yref="paper", text="Referans (ort.)", showarrow=False,
            xanchor="left", yanchor="top", xshift=4, font=dict(size=11),
        )
        return
    if not lo <= ref_date <= hi:
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


# Simge satırları: her işaret türü çizim alanının üstünde kendi satırında durur, böylece farklı
# türler aynı güne düşse de çakışmaz. Satır yüksekliği piksel cinsindendir.
ICON_ROW_PX = 18
ICON_ROWS = 3  # 📌 önemli tarih, ⛔ hariç tutulan tarih, ⚠️ iş birimi aksiyonu
# Aynı satırdaki iki simge, gösterilen tarih aralığının bu oranından daha yakınsa tek simgede birleşir
# (≈ 16 piksel simge ÷ ~600 piksel çizim alanı; 30 günde ardışık günler ayrı kalır, 365 günde ~10 günden
# yakın simgeler birleşir).
ICON_MERGE_FRACTION = 0.028

IconItem = tuple[pd.Timestamp, str]  # (simgenin x konumu, üzerine gelince görünecek metin)


def _mark_day_markers(
    fig: go.Figure,
    entries: pd.DataFrame | None,
    daily: pd.DataFrame,
    y_col: str,
    *,
    color: str,
    icon: str,
    dash: str,
) -> list[IconItem]:
    """Tek günlük kayıtlar için dikey çizgi ve hover notu çizer; simge konumlarını döner."""
    if entries is None or entries.empty or daily.empty:
        return []
    lo, hi = daily["LAST_OFFER_DATE"].min(), daily["LAST_OFFER_DATE"].max()
    ev = entries[entries["tarih"].between(lo, hi)]
    if ev.empty:
        return []

    def describe(g: pd.DataFrame) -> str:
        return "<br>".join(
            f"<b>{r.baslik}</b>"
            + (f" · {r.birim}" if getattr(r, "birim", "") else "")
            + (f"<br>{r.aciklama}" if r.aciklama else "")
            for r in g.itertuples()
        )

    by_day = ev.groupby("tarih").apply(describe, include_groups=False)
    for day in by_day.index:
        fig.add_shape(
            type="line", x0=day, x1=day, y0=0, y1=1, yref="paper",
            line=dict(color=color, width=1.5, dash=dash), opacity=0.7,
        )
    # Günün üzerine gelindiğinde birleşik hover kutusunda da açıklama görünsün.
    points = daily.set_index("LAST_OFFER_DATE")[y_col].reindex(by_day.index)
    fig.add_scatter(
        x=by_day.index, y=points.values, mode="markers", name=icon,
        marker=dict(size=1, opacity=0), showlegend=False,
        customdata=by_day.values, hovertemplate=icon + " %{customdata}<extra></extra>",
    )
    return [(day, f"{icon} {day:%d.%m.%Y}<br>{text}") for day, text in by_day.items()]


def _mark_ranges(
    fig: go.Figure,
    entries: pd.DataFrame | None,
    daily: pd.DataFrame,
    y_col: str,
    *,
    color: str,
    icon: str,
    prefix: str,
) -> list[IconItem]:
    """Tek gün ya da aralık kayıtlarını çizer (tek gün kesikli çizgi, aralık gölgeli bant + kenar çizgileri).

    Kapsanan günlerin birleşik hover kutusuna not ekler ve simge konumlarını (aralığın ortası) döner.
    """
    if entries is None or entries.empty or daily.empty:
        return []
    lo, hi = daily["LAST_OFFER_DATE"].min(), daily["LAST_OFFER_DATE"].max()
    half_day = pd.Timedelta(hours=12)
    items: list[IconItem] = []
    hover_x, hover_y, hover_text = [], [], []
    for r in entries.itertuples():
        if r.bitis < lo or r.baslangic > hi:
            continue
        start, end = max(r.baslangic, lo), min(r.bitis, hi)
        span = (
            f"{r.baslangic:%d.%m.%Y}" if r.baslangic == r.bitis
            else f"{r.baslangic:%d.%m.%Y} – {r.bitis:%d.%m.%Y}"
        )
        text = (
            f"<b>{icon} {prefix}{r.baslik}</b> ({span})"
            + (f" · {r.birim}" if getattr(r, "birim", "") else "")
            + (f"<br>{r.aciklama}" if r.aciklama else "")
        )
        if start == end:
            fig.add_shape(
                type="line", x0=start, x1=start, y0=0, y1=1, yref="paper",
                line=dict(color=color, width=2, dash="dash"),
            )
        else:
            fig.add_shape(
                type="rect", x0=start - half_day, x1=end + half_day, y0=0, y1=1, yref="paper",
                fillcolor=color, opacity=0.12, line=dict(width=0), layer="below",
            )
            for edge in (start - half_day, end + half_day):
                fig.add_shape(
                    type="line", x0=edge, x1=edge, y0=0, y1=1, yref="paper",
                    line=dict(color=color, width=1.5, dash="dash"),
                )
        items.append((start + (end - start) / 2, text))
        # Veri gösteriliyorsa, kapsanan günlerin birleşik hover kutusunda da not görünsün.
        covered = daily[daily["LAST_OFFER_DATE"].between(r.baslangic, r.bitis)].dropna(subset=[y_col])
        hover_x += covered["LAST_OFFER_DATE"].tolist()
        hover_y += covered[y_col].tolist()
        hover_text += [text] * len(covered)
    if hover_x:
        fig.add_scatter(
            x=hover_x, y=hover_y, mode="markers", name=icon,
            marker=dict(size=1, opacity=0), showlegend=False,
            customdata=hover_text, hovertemplate="%{customdata}<extra></extra>",
        )
    return items


def _cluster_icons(items: list[IconItem], min_gap: pd.Timedelta) -> list[tuple[pd.Timestamp, int, str]]:
    """Birbirine `min_gap`'ten yakın simgeleri tek simgede birleştirir: (x, adet, birleşik metin)."""
    clusters: list[list[IconItem]] = []
    for item in sorted(items, key=lambda it: it[0]):
        if clusters and item[0] - clusters[-1][-1][0] < min_gap:
            clusters[-1].append(item)
        else:
            clusters.append([item])
    result = []
    for group in clusters:
        xs = [x for x, _ in group]
        center = xs[0] + (xs[-1] - xs[0]) / 2
        result.append((center, len(group), "<br><br>".join(text for _, text in group)))
    return result


def _place_icons(
    fig: go.Figure, rows: list[tuple[str, list[IconItem]]], lo: pd.Timestamp, hi: pd.Timestamp
) -> None:
    """Simgeleri tür başına ayrı satıra yerleştirir; aynı satırda çakışacak simgeleri birleştirir."""
    min_gap = max((hi - lo) * ICON_MERGE_FRACTION, pd.Timedelta(hours=12))
    row = 0
    for icon, items in rows:
        if not items:
            continue
        for x, count, text in _cluster_icons(items, min_gap):
            fig.add_annotation(
                x=x, y=1, yref="paper", yanchor="bottom", yshift=ICON_ROW_PX * row,
                text=icon if count == 1 else f"{icon}<sup>{count}</sup>",
                showarrow=False, hovertext=text, font=dict(size=13),
            )
        row += 1


def _decorate(
    fig: go.Figure,
    daily: pd.DataFrame,
    y_col: str,
    ref_date: pd.Timestamp | tuple[pd.Timestamp, pd.Timestamp] | None,
    events: pd.DataFrame | None,
    exclusions: pd.DataFrame | None,
    actions: pd.DataFrame | None = None,
) -> None:
    """Zaman grafiklerine referans, önemli tarih, hariç tutulan tarih ve iş birimi aksiyonu işaretlerini ekler."""
    _mark_reference(fig, ref_date, daily)
    event_icons = _mark_day_markers(fig, events, daily, y_col, color=EVENT_COLOR, icon="📌", dash="dash")
    exclusion_icons = _mark_ranges(
        fig, exclusions, daily, y_col, color=EXCLUSION_COLOR, icon="⛔", prefix="Hariç: "
    )
    action_icons = _mark_ranges(
        fig, actions, daily, y_col, color=ACTION_COLOR, icon="⚠️", prefix="İş birimi: "
    )
    if not daily.empty:
        _place_icons(
            fig,
            [("📌", event_icons), ("⛔", exclusion_icons), ("⚠️", action_icons)],
            daily["LAST_OFFER_DATE"].min(),
            daily["LAST_OFFER_DATE"].max(),
        )


def time_lines(
    daily: pd.DataFrame,
    metric: str,
    y_title: str,
    y_format: str,
    hover_format: str,
    from_zero: bool,
    ref_date: pd.Timestamp | tuple[pd.Timestamp, pd.Timestamp] | None = None,
    events: pd.DataFrame | None = None,
    exclusions: pd.DataFrame | None = None,
    actions: pd.DataFrame | None = None,
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
    # Son noktaya doğrudan etiket: renk tek başına kimlik taşımasın. Değeri yüksek olan etiket
    # biraz yukarı, düşük olan biraz aşağı kaydırılır; değerler çok yakınsa üst üste binmezler.
    ends = {}
    for side, name in (("pilot", "Pilot"), ("nba", "NBA")):
        last = daily.dropna(subset=[f"{side}_{metric}"]).tail(1)
        if not last.empty:
            ends[name] = (last["LAST_OFFER_DATE"].iloc[0], last[f"{side}_{metric}"].iloc[0])
    higher = max(ends, key=lambda k: ends[k][1]) if len(ends) == 2 else None
    for name, (x, y) in ends.items():
        fig.add_annotation(
            x=x, y=y, text=name, showarrow=False, xanchor="left", xshift=10,
            yshift=0 if higher is None else (8 if name == higher else -8), font=dict(size=12),
        )
    fig.update_xaxes(tickformat="%d.%m", hoverformat="%d.%m.%Y", title=None)
    fig.update_yaxes(title=y_title, tickformat=y_format, rangemode="tozero" if from_zero else "normal")
    _decorate(fig, daily, f"pilot_{metric}", ref_date, events, exclusions, actions)
    fig = _layout(fig, height=420, hovermode="x unified")
    # Lejant figürün en üstüne, 📌 işaretleri onun altında çizim alanının üst kenarına oturur;
    # böylece erken bir önemli tarih lejantla çakışmaz.
    fig.update_layout(
        margin=dict(t=30 + 24 + ICON_ROW_PX * ICON_ROWS, r=50),
        legend=dict(yref="container", y=1, yanchor="top", x=0, xanchor="left"),
    )
    return fig


def lift_line(
    daily: pd.DataFrame,
    ref_date: pd.Timestamp | tuple[pd.Timestamp, pd.Timestamp] | None = None,
    events: pd.DataFrame | None = None,
    exclusions: pd.DataFrame | None = None,
    actions: pd.DataFrame | None = None,
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
    _decorate(fig, daily, "satis_lift", ref_date, events, exclusions, actions)
    fig = _layout(fig, height=320, hovermode="x unified")
    fig.update_layout(margin=dict(t=10 + ICON_ROW_PX * ICON_ROWS))  # 📌 / ⛔ / ⚠️ simge satırlarına yer
    return fig


def count_diff_line(
    daily: pd.DataFrame,
    ref_date: pd.Timestamp | tuple[pd.Timestamp, pd.Timestamp] | None = None,
    events: pd.DataFrame | None = None,
    exclusions: pd.DataFrame | None = None,
    actions: pd.DataFrame | None = None,
) -> go.Figure:
    """Günlük satış adet farkı (Pilot − NBA); 0 çizgisinin üstü Pilot, altı NBA lehine."""
    d = daily.copy()
    fig = go.Figure()
    fig.add_scatter(
        x=d["LAST_OFFER_DATE"],
        y=d["satis_adet_farki"],
        mode="lines+markers",
        name="Adet farkı",
        line=dict(color=PILOT_COLOR, width=2),
        # Nokta rengi farkın yönünü gösterir: mavi Pilot, turuncu NBA lehine.
        marker=dict(
            size=8,
            color=np.where(d["satis_adet_farki"] >= 0, PILOT_COLOR, NBA_COLOR),
            line=dict(width=2, color="white"),
        ),
        customdata=d[["pilot_satis", "nba_satis"]].to_numpy(),
        hovertemplate=(
            "Pilot − NBA: %{y:+,d}<br>Pilot: %{customdata[0]:,d} · NBA: %{customdata[1]:,d}<extra></extra>"
        ),
        showlegend=False,
    )
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="rgba(128,128,128,0.7)")
    fig.update_xaxes(tickformat="%d.%m", hoverformat="%d.%m.%Y", title=None)
    fig.update_yaxes(title="Pilot − NBA satış adedi", tickformat="+,d")
    _decorate(fig, d, "satis_adet_farki", ref_date, events, exclusions, actions)
    fig = _layout(fig, height=320, hovermode="x unified")
    fig.update_layout(margin=dict(t=10 + ICON_ROW_PX * ICON_ROWS))  # 📌 / ⛔ / ⚠️ simge satırlarına yer
    return fig
