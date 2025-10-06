from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import settings
from src.config.styles import render_col_divider

st.set_page_config(page_title="PV Forecast Dashboard", page_icon="☀️", layout="wide")

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .status-good {
        color: #28a745;
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)
st.title("PV Storage - Solar Energy Forecast")

file_name = "fcte_ued_pt1d.csv"
csv_path = Path(settings.DATA_DIR / "result" / file_name)

if csv_path.exists():
    df = pd.read_csv(csv_path)
else:
    st.info("👆 Please upload a CSV file to begin")

    st.markdown("### Expected CSV Format:")
    st.code("""
    date_time,pv_energy,pv_energy_est,pv_energy_pred,gti,ghi,air_temp,day_category,dataset
    2023-01-01,489.26,487.8,483.42,5.63,6.03,24.24,1,train
    2023-01-02,452.19,496.13,468.96,5.63,6.12,25.06,1,train
            """)


tab1, tab2, tab3, tab4 = st.tabs(["📊 Status", "🔔 Alarms", "📅 Events", "⚙️ Customize"])

with tab1:
    df["date_time"] = pd.to_datetime(df["date_time"])
    current_date = pd.to_datetime("2025-10-05")

    with st.sidebar:
        st.header("STATUS")
        st.markdown("### ✅ Good")
        st.caption(f"Last Update: {datetime.now().strftime('%b %d, %Y %I:%M:%S %p')}")

        st.markdown("---")
        st.subheader("ACTIVE ALARMS")
        st.info("No Active Alarms")

        st.markdown("---")
        st.subheader("STATUS")

        st.markdown("---")
        st.subheader("PROPERTIES")
        st.text("Tag Name: PVForecast")

    col1, col_div1, col2 = st.columns([2, 0.1, 8])

    with col1:
        st.markdown("**Time Range**")
        date_start = st.date_input("Start", current_date - timedelta(days=30))
        date_end = st.date_input("End", current_date + timedelta(days=14))

    with col_div1:
        render_col_divider(height=200)

    mask = (df["date_time"] >= pd.to_datetime(date_start)) & (df["date_time"] <= pd.to_datetime(date_end))
    df_filtered = df[mask].copy()

    df_historical = df_filtered[df_filtered["dataset"] == "test"].copy()
    df_forecast = df_filtered[df_filtered["dataset"] == "forecast"].copy()

    # ====================================================================================================================================
    # MÉTRICAS DE PERFORMANCE
    # ====================================================================================================================================

    with col2:
        if len(df_historical) > 0:
            mae_physical = np.mean(np.abs(df_historical["pv_energy"] - df_historical["pv_energy_est"]))
            mae_ml = np.mean(np.abs(df_historical["pv_energy"] - df_historical["pv_energy_pred"]))

            rmse_physical = np.sqrt(np.mean((df_historical["pv_energy"] - df_historical["pv_energy_est"]) ** 2))
            rmse_ml = np.sqrt(np.mean((df_historical["pv_energy"] - df_historical["pv_energy_pred"]) ** 2))

            # R² Score
            ss_res_physical = np.sum((df_historical["pv_energy"] - df_historical["pv_energy_est"]) ** 2)
            ss_tot = np.sum((df_historical["pv_energy"] - df_historical["pv_energy"].mean()) ** 2)
            r2_physical = 1 - (ss_res_physical / ss_tot)

            ss_res_ml = np.sum((df_historical["pv_energy"] - df_historical["pv_energy_pred"]) ** 2)
            r2_ml = 1 - (ss_res_ml / ss_tot)

            st.markdown("**Model Performance Metrics**")

            metric_col1, metric_col2, metric_col3, col_div, metric_col4, metric_col5, metric_col6 = st.columns([
                1.5,
                1.5,
                1.5,
                0.5,
                1.5,
                1.5,
                1.5,
            ])

            with metric_col1:
                st.metric("📐 MAE", f"{mae_physical:.2f} kWh", help="Mean Absolute Error - Physical Model")
            with metric_col2:
                st.metric("📏 RMSE", f"{rmse_physical:.2f} kWh", help="Root Mean Square Error - Physical Model")
            with metric_col3:
                st.metric("📊 R²", f"{r2_physical:.3f}", help="R² Score - Physical Model")
            with col_div:
                render_col_divider(height=120, width=0.8)
            with metric_col4:
                st.metric(
                    "🤖 MAE",
                    f"{mae_ml:.2f} kWh",
                    delta=f"{mae_physical - mae_ml:.2f}",
                    delta_color="inverse",
                    help="Mean Absolute Error - ML Model",
                )
            with metric_col5:
                st.metric(
                    "🤖 RMSE",
                    f"{rmse_ml:.2f} kWh",
                    delta=f"{rmse_physical - rmse_ml:.2f}",
                    delta_color="inverse",
                    help="Root Mean Square Error - ML Model",
                )
            with metric_col6:
                st.metric(
                    "🤖 R²",
                    f"{r2_ml:.3f}",
                    delta=f"{r2_ml - r2_physical:.3f}",
                    delta_color="normal",
                    help="R² Score - ML Model",
                )

    # ====================================================================================================================================
    # GRÁFICO 1: PV ENERGY PRODUCTION
    # ====================================================================================================================================
    st.markdown("---")

    color_observed = "#0d6efd"
    color_physical = "#A23B72"
    color_ml = "#F18F01"

    fig_power = go.Figure()

    # Observed Energy (apenas histórico)
    if len(df_historical) > 0:
        fig_power.add_trace(
            go.Scatter(
                x=df_historical["date_time"],
                y=df_historical["pv_energy"],
                mode="lines+markers",
                name="Observed Energy",
                line=dict(color=color_observed, width=3.5),
                marker=dict(size=7, color="white", line=dict(color=color_observed, width=3.5)),
                fill="tozeroy",
                fillcolor="rgba(13, 110, 253, 0.1)",
                opacity=0.9,
            )
        )

    fig_power.add_trace(
        go.Scatter(
            x=df_filtered["date_time"],
            y=df_filtered["pv_energy_est"],
            mode="lines+markers",
            name="Physical Model (NBR 16274)",
            line=dict(color=color_physical, width=3.5),
            marker=dict(size=7, color="white", line=dict(color=color_physical, width=3.5)),
            fill="tozeroy",
            fillcolor="rgba(162, 59, 114, 0.05)",
            opacity=0.9,
        )
    )

    fig_power.add_trace(
        go.Scatter(
            x=df_filtered["date_time"],
            y=df_filtered["pv_energy_pred"],
            mode="lines+markers",
            name="ML Model (XGBoost)",
            line=dict(color=color_ml, width=3.5),
            marker=dict(size=7, color="white", line=dict(color=color_ml, width=3.5)),
            fill="tozeroy",
            fillcolor="rgba(241, 143, 1, 0.05)",
            opacity=0.9,
        )
    )

    fig_power.add_shape(
        type="line",
        x0=current_date,
        x1=current_date,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="rgba(100, 100, 100, 0.5)", width=2, dash="dash"),
    )

    fig_power.add_annotation(
        x=current_date, y=1.02, yref="paper", text="Now", showarrow=False, font=dict(size=11, color="#777")
    )

    if len(df_historical) > 0:
        obs_mean = df_historical["pv_energy"].mean()
        phys_mean = df_filtered["pv_energy_est"].mean()
        ml_mean = df_filtered["pv_energy_pred"].mean()

        fig_power.add_annotation(
            x=0.02,
            y=0.4,
            xref="paper",
            yref="paper",
            text=f"<b>Average Daily Production:</b><br>"
            f"Observed: {obs_mean:.1f} kWh<br>"
            f"Physical Model: {phys_mean:.1f} kWh<br>"
            f"ML Model: {ml_mean:.1f} kWh",
            showarrow=False,
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="rgba(0, 0, 0, 0.15)",
            borderwidth=1,
            borderpad=8,
            font=dict(size=15, color="#2c3e50"),
            align="left",
            xanchor="left",
            yanchor="top",
        )

    fig_power.update_layout(
        title={
            "text": "PV Energy Production: Observed vs Predicted<br><sub style='font-size:10px; color:#777'> </sub>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 22, "color": "#2c3e50"},
        },
        # xaxis_title="Date",
        yaxis_title="Energy Production (kWh)",
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.2)",
            tickfont=dict(size=16),
            title_font=dict(size=16, color="#192430"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.3)",
            tickfont=dict(size=16),
            title_font=dict(size=16, color="#192430"),
            zeroline=False,
            rangemode="tozero",
        ),
        plot_bgcolor="white",
        paper_bgcolor="#fafafa",
        height=500,
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(0, 0, 0, 0.1)",
            borderwidth=1,
            font=dict(size=16),
        ),
        margin=dict(l=60, r=40, t=100, b=80),
    )

    st.plotly_chart(fig_power, use_container_width=True)

    # ====================================================================================================================================
    # GRÁFICO 2: IRRADIANCE
    # ====================================================================================================================================
    st.markdown("---")

    color_ghi = "#E63946"
    color_gti = "#457B9D"

    fig_irr = go.Figure()

    # GTI
    fig_irr.add_trace(
        go.Scatter(
            x=df_filtered["date_time"],
            y=df_filtered["gti"],
            mode="lines+markers",
            name="Global Tilted Irradiance (GTI)",
            line=dict(color=color_gti, width=3.5),
            marker=dict(size=7, color="white", line=dict(color=color_gti, width=3.5)),
            fill="tozeroy",
            fillcolor="rgba(69, 123, 157, 0.05)",
            opacity=0.9,
        )
    )

    # GHI
    fig_irr.add_trace(
        go.Scatter(
            x=df_filtered["date_time"],
            y=df_filtered["ghi"],
            mode="lines+markers",
            name="Global Horizontal Irradiance (GHI)",
            line=dict(color=color_ghi, width=3.5),
            marker=dict(size=7, color="white", line=dict(color=color_ghi, width=3.5)),
            fill="tozeroy",
            fillcolor="rgba(230, 57, 70, 0.05)",
            opacity=0.9,
        )
    )

    # Linha "Now"
    fig_irr.add_shape(
        type="line",
        x0=current_date,
        x1=current_date,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="rgba(100, 100, 100, 0.5)", width=2, dash="dash"),
    )

    fig_irr.add_annotation(
        x=current_date, y=1.02, yref="paper", text="Now", showarrow=False, font=dict(size=11, color="#777")
    )

    # Anotação com médias
    ghi_mean = df_filtered["ghi"].mean()
    gti_mean = df_filtered["gti"].mean()

    fig_irr.add_annotation(
        x=0.02,
        y=0.4,
        xref="paper",
        yref="paper",
        text=f"<b>Average Daily Irradiance:</b><br>GHI: {ghi_mean:.2f} kWh/m²<br>GTI: {gti_mean:.2f} kWh/m²",
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.95)",
        bordercolor="rgba(0, 0, 0, 0.15)",
        borderwidth=1,
        borderpad=8,
        font=dict(size=15, color="#2c3e50"),
        align="left",
        xanchor="left",
        yanchor="top",
    )

    fig_irr.update_layout(
        title={
            "text": "Solar Irradiance Components<br><sub style='font-size:13px; color:#777'>Global Horizontal (GHI) and Global Tilted (GTI)</sub>",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 28, "color": "#2c3e50"},
        },
        # xaxis_title="Date",
        yaxis_title="Irradiance (kWh/m²)",
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.2)",
            tickfont=dict(size=16),
            title_font=dict(size=16, color="#192430"),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.3)",
            tickfont=dict(size=16),
            title_font=dict(size=16, color="#192430"),
            zeroline=False,
            rangemode="tozero",
        ),
        plot_bgcolor="white",
        paper_bgcolor="#fafafa",
        height=500,
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(0, 0, 0, 0.1)",
            borderwidth=1,
            font=dict(size=16),
        ),
        margin=dict(l=60, r=40, t=100, b=80),
    )

    st.plotly_chart(fig_irr, use_container_width=True)

    # ============================================
    # TABELA DE DADOS
    # ============================================
    st.markdown("---")
    st.subheader("📋 Data Table")

    display_cols = [
        "date_time",
        "pv_energy",
        "pv_energy_est",
        "pv_energy_pred",
        "gti",
        "ghi",
        "air_temp",
        "day_category",
        "dataset",
    ]

    st.dataframe(
        df_filtered[display_cols].style.format({
            "pv_energy": "{:.2f}",
            "pv_energy_est": "{:.2f}",
            "pv_energy_pred": "{:.2f}",
            "gti": "{:.2f}",
            "ghi": "{:.2f}",
            "air_temp": "{:.2f}",
        }),
        use_container_width=True,
        height=400,
    )


with tab2:
    st.info("🔔 No active alarms")

with tab3:
    st.info("📅 No events to display")

with tab4:
    st.subheader("⚙️ Customize Dashboard")
    st.write("Configuration options will be available here")

st.markdown("---")
st.caption("Copyright ©2015-2025 MEPA All rights reserved.")
