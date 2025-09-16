from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def daily_pv_curve_analyzer(df_5min, obs_column="y_true", pred_column="y_pred"):
    st.subheader("Análise Fotovoltaica")

    df = df_5min.copy()
    df["date"] = df.index.date
    df["hour"] = df.index.hour
    df["time_decimal"] = df["hour"] + df.index.minute / 60

    available_dates = sorted(df["date"].unique())

    if len(available_dates) == 0:
        st.error("❌ Nenhum dado disponível")
        return

    col1, col2 = st.columns([3, 1])

    with col1:
        selected_date = st.selectbox(
            "Selecionar Data",
            available_dates,
            format_func=lambda x: x.strftime("%d/%m/%Y"),
            index=len(available_dates) // 2,
        )

    daily_data = df[df["date"] == selected_date].copy()

    if len(daily_data) == 0:
        st.warning(f"⚠️ Sem dados para {selected_date}")
        return

    real_values = daily_data[obs_column].values
    pred_values = daily_data[pred_column].values

    real_energy = np.trapz(real_values) * 5 / 60
    pred_energy = np.trapz(pred_values) * 5 / 60
    energy_error = abs(real_energy - pred_energy) / max(real_energy, 0.001) * 100

    mae = np.mean(np.abs(real_values - pred_values))
    r2 = 1 - np.sum((real_values - pred_values) ** 2) / np.sum((real_values - np.mean(real_values)) ** 2)

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(" Energia Real", f"{real_energy:.1f} kWh", help="Energia total gerada no dia")

    with col2:
        st.metric(" Energia Prevista", f"{pred_energy:.1f} kWh", delta=f"{pred_energy - real_energy:+.1f} kWh")

    with col3:
        st.metric(" Precisão (R²)", f"{r2:.3f}", delta=f"{(r2 - 0.9) * 100:+.0f}%" if r2 >= 0.9 else None)

    with col4:
        st.metric(" Erro Médio", f"{mae:.2f} kW", delta=f"{energy_error:.1f}% energia")

    st.markdown("---")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily_data["time_decimal"],
            y=daily_data[obs_column],
            mode="lines",
            name="Real",
            line=dict(color="#1f77b4", width=3),
            hovertemplate="<b>Real</b><br>%{x:.1f}h: %{y:.2f} kW<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=daily_data["time_decimal"],
            y=daily_data[pred_column],
            mode="lines",
            name="Previsto",
            line=dict(color="#ff7f0e", width=2, dash="dash"),
            hovertemplate="<b>Previsto</b><br>%{x:.1f}h: %{y:.2f} kW<extra></extra>",
        )
    )

    show_difference = st.checkbox(" Mostrar área de diferença", value=False)

    if show_difference:
        fig.add_trace(
            go.Scatter(
                x=daily_data["time_decimal"],
                y=daily_data[pred_column],
                fill="tonexty",
                mode="none",
                name="Diferença",
                fillcolor="rgba(255, 0, 0, 0.1)",
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        title=dict(text=f"Geração Fotovoltaica - {selected_date.strftime('%d/%m/%Y')}", x=0.5, font=dict(size=20)),
        xaxis=dict(title="Hora do Dia", showgrid=True, gridcolor="rgba(128,128,128,0.2)", tickformat=".0f"),
        yaxis=dict(title="Potência (kW)", showgrid=True, gridcolor="rgba(128,128,128,0.2)"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=500,
        margin=dict(l=50, r=50, t=80, b=50),
    )

    fig.update_xaxes(showline=True, linewidth=1, linecolor="lightgray", mirror=True)
    fig.update_yaxes(showline=True, linewidth=1, linecolor="lightgray", mirror=True)

    st.plotly_chart(fig, use_container_width=True)
