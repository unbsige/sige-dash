import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly import express as px

warnings.filterwarnings("ignore")


def plot_metrics(df_pred, metrics):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="R² Score",
            value=f"{metrics['r2']:.3f}",
            delta=None,
            help="Coeficiente de Determinação - Quanto maior, melhor",
        )

    with col2:
        st.metric(
            label="RMSE",
            value=f"{metrics['rmse']:.1f}%",
            delta=None,
            help="Root Mean Square Error",
        )

    with col3:
        st.metric(
            label="MAE",
            value=f"{metrics['mae']:.1f}%",
            delta=None,
            help="Mean Absolute Error",
        )

    with col4:
        st.metric(
            label="nMAE (%)",
            value=f"{metrics['nmae']:.1f}%",
            delta=None,
            help="Erro Absoluto Médio Normalizado",
        )

    st.markdown("---")

    st.subheader("Série Temporal")
    fig_time = go.Figure()
    fig_time.add_trace(go.Scatter(x=df_pred.index, y=df_pred["y_true"], name="Real", line=dict(color="blue")))
    fig_time.add_trace(
        go.Scatter(
            x=df_pred.index,
            y=df_pred["y_pred"],
            name="Predito",
            line=dict(color="red", dash="dot"),
        )
    )

    fig_time.update_layout(
        title="Evolução Temporal dos Valores",
        xaxis_title="Data",
        yaxis_title="Energia (kW)",
        hovermode="x unified",
    )

    st.subheader("Valores Reais vs Preditos")

    fig_scatter = px.scatter(
        x=df_pred["y_true"],
        y=df_pred["y_pred"],
        labels={"x": "Valores Reais (kW)", "y": "Valores Preditos (kW)"},
        title="Correlação entre Valores Reais e Preditos",
    )

    min_val = min(df_pred["y_true"].min(), df_pred["y_pred"].min())
    max_val = max(df_pred["y_true"].max(), df_pred["y_pred"].max())
    fig_scatter.add_trace(
        go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode="lines",
            name="Linha Perfeita",
            line=dict(color="red", dash="dash"),
        )
    )

    st.plotly_chart(fig_time, use_container_width=True)
