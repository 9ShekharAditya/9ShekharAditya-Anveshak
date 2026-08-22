"""
components/plots.py — Reusable Plotly chart builders.

Each function returns a Plotly figure that can be displayed with
st.plotly_chart(fig, use_container_width=True)
"""

import plotly.express as px
import plotly.graph_objects as go
import numpy as np

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TIER_COLORS, SOURCE_COLORS


DARK_TEMPLATE = "plotly_dark"
DARK_BG = "rgba(8, 8, 16, 0.0)"


def _apply_dark_style(fig):
    """Apply consistent dark + gold theme to charts."""
    fig.update_layout(
        template=DARK_TEMPLATE,
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font_color="#8a8070",
        title_font_color="#d4a843",
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(gridcolor="rgba(180,155,80,0.08)", zerolinecolor="rgba(180,155,80,0.12)"),
        yaxis=dict(gridcolor="rgba(180,155,80,0.08)", zerolinecolor="rgba(180,155,80,0.12)"),
    )
    return fig


def radius_vs_insol_scatter(df):
    """
    Planet radius vs. insolation flux scatter plot.
    Color-coded by habitability tier.
    """
    plot_df = df.dropna(subset=["radius", "insol"]).copy()
    if len(plot_df) == 0:
        return go.Figure()

    # Cap insol for better visualization
    plot_df["insol_display"] = plot_df["insol"].clip(upper=1000)

    fig = px.scatter(
        plot_df,
        x="insol_display",
        y="radius",
        color="habitability_tier",
        color_discrete_map=TIER_COLORS,
        hover_name="name",
        hover_data={"insol": ":.2f", "radius": ":.2f", "eq_temp": ":.0f",
                    "esi": ":.3f", "insol_display": False},
        log_x=True,
        title="Planet Radius vs. Insolation Flux",
        labels={"insol_display": "Insolation (Earth flux)", "radius": "Radius (R⊕)"},
        opacity=0.7,
    )

    # Add Earth reference
    fig.add_trace(go.Scatter(
        x=[1.0], y=[1.0], mode="markers+text",
        marker=dict(size=14, color="#2ecc71", symbol="star"),
        text=["Earth"], textposition="top right",
        name="Earth", showlegend=True,
    ))

    # HZ region (insol ~ 0.25 to 1.1 for conservative)
    fig.add_vrect(x0=0.25, x1=1.1, fillcolor="green", opacity=0.08,
                  annotation_text="Conservative HZ flux range", annotation_position="top left")

    return _apply_dark_style(fig)


def radius_distribution(df):
    """Histogram of planet radii with Earth/Neptune/Jupiter reference lines."""
    plot_df = df.dropna(subset=["radius"]).copy()
    plot_df["radius_display"] = plot_df["radius"].clip(upper=25)

    fig = px.histogram(
        plot_df,
        x="radius_display",
        nbins=60,
        color="source",
        color_discrete_map=SOURCE_COLORS,
        title="Planet Radius Distribution",
        labels={"radius_display": "Radius (R⊕)"},
        barmode="overlay",
        opacity=0.7,
    )

    # Reference lines
    for name, r, color in [("Earth", 1.0, "#2ecc71"), ("Neptune", 3.88, "#3498db"),
                            ("Jupiter", 11.2, "#e74c3c")]:
        fig.add_vline(x=r, line_dash="dash", line_color=color,
                      annotation_text=name, annotation_position="top right")

    return _apply_dark_style(fig)


def period_vs_radius_scatter(df):
    """Period vs. Radius scatter — shows detection biases."""
    plot_df = df.dropna(subset=["period", "radius"]).copy()
    plot_df = plot_df[plot_df["period"] > 0]

    fig = px.scatter(
        plot_df,
        x="period",
        y="radius",
        color="source",
        color_discrete_map=SOURCE_COLORS,
        hover_name="name",
        log_x=True,
        title="Orbital Period vs. Planet Radius",
        labels={"period": "Orbital Period (days)", "radius": "Radius (R⊕)"},
        opacity=0.5,
    )

    return _apply_dark_style(fig)


def source_pie_chart(df):
    """Pie chart of candidates by source mission."""
    counts = df["source"].value_counts().reset_index()
    counts.columns = ["source", "count"]

    fig = px.pie(
        counts,
        values="count",
        names="source",
        color="source",
        color_discrete_map=SOURCE_COLORS,
        title="Candidates by Mission",
    )
    fig.update_traces(textinfo="percent+value")

    return _apply_dark_style(fig)


def hz_occupancy_chart(df):
    """Bar chart: fraction of candidates in HZ by mission."""
    data = []
    for source in df["source"].unique():
        subset = df[df["source"] == source]
        total = len(subset)
        in_hz = subset["in_hz_optimistic"].fillna(False).sum()
        data.append({
            "source": source,
            "In HZ": in_hz,
            "Outside HZ": total - in_hz,
            "HZ %": f"{in_hz/total*100:.1f}%" if total > 0 else "0%",
        })

    import pandas as pd
    chart_df = pd.DataFrame(data)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="In Habitable Zone",
        x=chart_df["source"],
        y=chart_df["In HZ"],
        marker_color="#2ecc71",
    ))
    fig.add_trace(go.Bar(
        name="Outside HZ",
        x=chart_df["source"],
        y=chart_df["Outside HZ"],
        marker_color="#95a5a6",
    ))
    fig.update_layout(barmode="stack", title="Habitable Zone Occupancy by Mission")

    return _apply_dark_style(fig)


def esi_distribution(df):
    """Histogram of Earth Similarity Index values."""
    plot_df = df[df["esi"] > 0].copy()

    fig = px.histogram(
        plot_df,
        x="esi",
        nbins=50,
        color="source",
        color_discrete_map=SOURCE_COLORS,
        title="Earth Similarity Index Distribution",
        labels={"esi": "ESI (0 = nothing like Earth, 1 = identical)"},
        barmode="overlay",
        opacity=0.7,
    )

    fig.add_vrect(x0=0.8, x1=1.0, fillcolor="green", opacity=0.1,
                  annotation_text="Earth-like", annotation_position="top left")

    return _apply_dark_style(fig)


def tier_summary_chart(df):
    """Horizontal bar chart showing count per habitability tier."""
    tier_order = ["High Potential", "Moderate Potential", "Low Potential", "Not Habitable"]
    counts = df["habitability_tier"].value_counts()

    fig = go.Figure(go.Bar(
        y=[t for t in tier_order if t in counts.index],
        x=[counts.get(t, 0) for t in tier_order if t in counts.index],
        orientation="h",
        marker_color=[TIER_COLORS.get(t, "#999") for t in tier_order if t in counts.index],
    ))
    fig.update_layout(title="Candidates by Habitability Tier",
                      xaxis_title="Count", yaxis_title="")

    return _apply_dark_style(fig)
