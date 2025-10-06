from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import settings
from src.config.styles import render_col_divider

st.set_page_config(page_title="Anomaly Detection", page_icon="🔍", layout="wide")

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .alert-critical {
        background-color: #fee;
        border-left: 4px solid #d62728;
        padding: 10px;
        margin: 5px 0;
    }
    .alert-high {
        background-color: #fff5e6;
        border-left: 4px solid #ff7f0e;
        padding: 10px;
        margin: 5px 0;
    }
    .alert-medium {
        background-color: #fffef0;
        border-left: 4px solid #f2cd60;
        padding: 10px;
        margin: 5px 0;
    }
    .alert-low {
        background-color: #f0fff0;
        border-left: 4px solid #8CD867;
        padding: 10px;
        margin: 5px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🔍 Anomaly Detection System")
st.markdown("### Performance Ratio (PR) Based Alert System")

# ====================================================================
# RESUMO EXECUTIVO (calculado após filtros)
# ====================================================================
# Placeholder para métricas - será preenchido depois dos filtros
metrics_placeholder = st.empty()


# Função de detecção de anomalias
def anomaly_detect(pr_model):
    """Classifica o nível de alerta baseado no PR_Model"""
    if pr_model >= 0.90:
        return 1  # Normal
    elif pr_model >= 0.85:
        return 3  # Baixo
    elif pr_model >= 0.80:
        return 5  # Médio
    elif pr_model >= 0.75:
        return 7  # Alto
    else:
        return 10  # Crítico


# Configurações de cores e símbolos
alert_colors = {
    1: "#2ca02c",  # Verde - Normal
    3: "#8CD867",  # Verde claro - Baixo
    5: "#f2cd60",  # Amarelo - Médio
    7: "#ff7f0e",  # Laranja - Alto
    10: "#d62728",  # Vermelho - Crítico
}

marker_symbols = {
    1: "circle",
    3: "diamond",
    5: "triangle-up",
    7: "x",
    10: "star",
}

alert_labels = {1: "Normal", 3: "Baixo", 5: "Médio", 7: "Alto", 10: "Crítico"}


# ====================================================================
# FUNÇÃO DE CÁLCULO DE PERFORMANCE RATIO
# ====================================================================
def calculate_performance_ratios(
    df,
    irrad_col,
    obs_col,
    pred_col=None,
    theo_col=None,
    pv_capacity=125,
    min_irradiance=0.01,
):
    """
    Calcula Performance Ratios (PR) para sistema fotovoltaico.

    PR = Yf / Yr
    onde:
    - Yf (Final Yield) = Energia / Potência [kWh/kWp = h]
    - Yr (Reference Yield) = Irradiância / 1.0 [kWh/m² / kW/m² = h]
    """
    df_result = df.copy()

    # Reference Yield (Yr) - Horas de sol pico equivalente
    yr = df_result[irrad_col].copy()
    yr = yr.replace(0, np.nan)
    yr = yr.fillna(min_irradiance)
    yr = yr.clip(lower=min_irradiance)
    df_result["yr"] = yr / 1.0

    # PR Observado
    if obs_col in df_result.columns:
        df_result["yf_obs"] = df_result[obs_col] / pv_capacity
        df_result["pr_obs"] = df_result["yf_obs"] / df_result["yr"]
        df_result["pr_obs"] = df_result["pr_obs"].replace([np.inf, -np.inf], np.nan)
        df_result["pr_obs"] = df_result["pr_obs"].clip(lower=0, upper=2.0)

    # PR Previsto (ML)
    if pred_col is not None and pred_col in df_result.columns:
        df_result["yf_pred"] = df_result[pred_col] / pv_capacity
        df_result["pr_pred"] = df_result["yf_pred"] / df_result["yr"]
        df_result["pr_pred"] = df_result["pr_pred"].replace([np.inf, -np.inf], np.nan)
        df_result["pr_pred"] = df_result["pr_pred"].clip(lower=0, upper=2.0)

    # PR Teórico/Físico
    if theo_col is not None and theo_col in df_result.columns:
        df_result["yf_theo"] = df_result[theo_col] / pv_capacity
        df_result["pr_theo"] = df_result["yf_theo"] / df_result["yr"]
        df_result["pr_theo"] = df_result["pr_theo"].replace([np.inf, -np.inf], np.nan)
        df_result["pr_theo"] = df_result["pr_theo"].clip(lower=0, upper=2.0)

    return df_result


# ====================================================================
# CARREGAR E PROCESSAR DADOS
# ====================================================================
file_name = "fcte_ued_pt1d.csv"
csv_path = Path(settings.DATA_DIR / "result" / file_name)

if not csv_path.exists():
    st.error("📁 Arquivo de dados não encontrado. Por favor, verifique o caminho do arquivo.")
    st.stop()

df = pd.read_csv(csv_path)
df["date_time"] = pd.to_datetime(df["date_time"])

# Calcular Performance Ratios usando a função otimizada
df = calculate_performance_ratios(
    df,
    irrad_col="gti",
    obs_col="pv_energy",
    pred_col="pv_energy_pred",
    theo_col="pv_energy_est",
    pv_capacity=125,  # kWp - Ajustar conforme seu sistema
)

# Renomear para manter compatibilidade com código existente
df["pr_physical"] = df["pr_theo"]
df["pr_ml"] = df["pr_pred"]

# Aplicar detecção de anomalias
df["alert_physical"] = df["pr_physical"].apply(anomaly_detect)
df["alert_ml"] = df["pr_ml"].apply(anomaly_detect)

# Sidebar
with st.sidebar:
    st.header("ANOMALY DETECTION")

    # Contador de alertas ativos
    current_date = pd.to_datetime("2025-10-05")
    recent_data = df[df["date_time"] >= (current_date - timedelta(days=7))]

    critical_count = len(recent_data[recent_data["alert_ml"] >= 7])

    if critical_count > 0:
        st.markdown(f"### ⚠️ {critical_count} Critical Alerts")
        st.caption("Last 7 days")
    else:
        st.markdown("### ✅ No Critical Alerts")
        st.caption("Last 7 days")

    st.markdown("---")
    st.subheader("ALERT THRESHOLDS")
    st.markdown("""
    - **Normal**: PR ≥ 90%
    - **Low**: 85% ≤ PR < 90%
    - **Medium**: 80% ≤ PR < 85%
    - **High**: 75% ≤ PR < 80%
    - **Critical**: PR < 75%
    """)

    st.markdown("---")
    st.subheader("MODEL SELECTION")
    model_type = st.radio("Select Model for Analysis:", ["ML Model (XGBoost)", "Physical Model (NBR 16274)"], index=0)

alert_col = "alert_ml" if "ML Model" in model_type else "alert_physical"
pr_col = "pr_ml" if "ML Model" in model_type else "pr_physical"
energy_col = "pv_energy_pred" if "ML Model" in model_type else "pv_energy_est"

# Filtros de data
col1, col2, col3 = st.columns([2, 2, 6])

with col1:
    date_start = st.date_input("Start Date", current_date - timedelta(days=90))

with col2:
    date_end = st.date_input("End Date", current_date + timedelta(days=14))

# Filtrar dados por data
mask = (df["date_time"] >= pd.to_datetime(date_start)) & (df["date_time"] <= pd.to_datetime(date_end))
df_filtered = df[mask].copy()

# Separar dados históricos e forecast
df_historical = df_filtered[df_filtered["dataset"] == "test"].copy()
df_forecast = df_filtered[df_filtered["dataset"] == "forecast"].copy()

# ====================================================================
# RESUMO EXECUTIVO NO TOPO
# ====================================================================
with metrics_placeholder.container():
    st.markdown("---")
    st.markdown("### 📊 Executive Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        critical_count_metric = len(df_filtered[df_filtered[alert_col] == 10])
        st.metric(
            "🔴 Critical",
            critical_count_metric,
            delta=f"-{critical_count_metric}" if critical_count_metric > 0 else "0",
            delta_color="inverse",
            help="Alerts with PR < 75%",
        )

    with col2:
        high_count_metric = len(df_filtered[df_filtered[alert_col] == 7])
        st.metric("🔶 High", high_count_metric, help="Alerts with 75% ≤ PR < 80%")

    with col3:
        avg_pr_metric = df_filtered[pr_col].mean()
        pr_delta = (avg_pr_metric - 0.80) * 100  # Comparar com 80% de referência
        st.metric(
            "📈 Avg PR",
            f"{avg_pr_metric:.1%}",
            delta=f"{pr_delta:+.1f}%",
            delta_color="normal",
            help=f"Average Performance Ratio ({model_type})",
        )

    with col4:
        days_analyzed = len(df_filtered)
        st.metric("📅 Days", days_analyzed, help="Total days in selected period")

    with col5:
        alert_rate_metric = (
            (len(df_filtered[df_filtered[alert_col] >= 5]) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
        )
        st.metric(
            "⚠️ Alert Rate",
            f"{alert_rate_metric:.1f}%",
            delta=f"{alert_rate_metric:.1f}%",
            delta_color="inverse",
            help="% of days with Medium+ alerts",
        )

    st.markdown("---")

# Métricas de Alerta
st.markdown("---")
st.subheader("📊 Alert Statistics")

alert_counts = df_filtered[alert_col].value_counts().sort_index()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    normal_count = alert_counts.get(1, 0)
    st.metric("✅ Normal", normal_count, help="PR ≥ 90%")

with col2:
    low_count = alert_counts.get(3, 0)
    st.metric("💚 Low", low_count, help="85% ≤ PR < 90%")

with col3:
    medium_count = alert_counts.get(5, 0)
    st.metric("⚠️ Medium", medium_count, help="80% ≤ PR < 85%")

with col4:
    high_count = alert_counts.get(7, 0)
    st.metric("🔶 High", high_count, help="75% ≤ PR < 80%")

with col5:
    critical_count = alert_counts.get(10, 0)
    st.metric("🔴 Critical", critical_count, help="PR < 75%")

# Percentual de alertas críticos
total_points = len(df_filtered)
high_priority_alerts = len(df_filtered[df_filtered[alert_col] >= 5])
critical_alerts = len(df_filtered[df_filtered[alert_col] >= 7])

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Points Analyzed", total_points)
with col2:
    pct_high = (high_priority_alerts / total_points * 100) if total_points > 0 else 0
    st.metric("Medium+ Alerts (%)", f"{pct_high:.1f}%")
with col3:
    pct_critical = (critical_alerts / total_points * 100) if total_points > 0 else 0
    st.metric("High+ Alerts (%)", f"{pct_critical:.1f}%", delta=f"{pct_critical:.1f}%", delta_color="inverse")

# Gráfico Principal: Energy Production com Sistema de Alertas
st.markdown("---")
st.subheader("📈 Energy Production with Alert System")

fig = go.Figure()

# Cores para train/test
color_train = "#1f77b4"
color_test = "#2ca02c"
color_pred = "#bcbd22"

df_train = df_filtered[df_filtered["dataset"] == "train"]
if len(df_train) > 0:
    fig.add_trace(
        go.Scatter(
            x=df_train["date_time"],
            y=df_train["pv_energy"],
            name="Train",
            mode="lines",
            line=dict(color=color_train, width=3.5),
            opacity=0.9,
        )
    )

if len(df_historical) > 0:
    fig.add_trace(
        go.Scatter(
            x=df_historical["date_time"],
            y=df_historical["pv_energy"],
            name="Test (Observed)",
            mode="lines",
            line=dict(color=color_test, width=3.5),
            opacity=0.9,
        )
    )

fig.add_trace(
    go.Scatter(
        x=df_filtered["date_time"],
        y=df_filtered[energy_col],
        name=f"Prediction ({model_type})",
        mode="lines",
        line=dict(color=color_pred, width=3.5, dash="dash"),
        opacity=0.9,
    )
)

for alert_level in [3, 5, 7, 10]:
    mask_alert = df_filtered[alert_col] == alert_level
    if mask_alert.any():
        fig.add_trace(
            go.Scatter(
                x=df_filtered.loc[mask_alert, "date_time"],
                y=df_filtered.loc[mask_alert, "pv_energy"],
                name=f"Alert {alert_labels[alert_level]}",
                mode="markers",
                marker=dict(
                    color=alert_colors[alert_level],
                    size=10,
                    symbol=marker_symbols[alert_level],
                    line=dict(width=1, color="black"),
                ),
                opacity=0.8,
                hovertemplate=(
                    f"<b>Alert {alert_labels[alert_level]}</b><br>"
                    "Date: %{x}<br>"
                    "PR: %{customdata:.3f}<br>"
                    "Energy: %{y:.2f} kWh<br>"
                    "<extra></extra>"
                ),
                customdata=df_filtered.loc[mask_alert, pr_col],
            )
        )

fig.add_shape(
    type="line",
    x0=current_date,
    x1=current_date,
    y0=0,
    y1=1,
    yref="paper",
    line=dict(color="rgba(100, 100, 100, 0.5)", width=3.5, dash="dash"),
)

fig.add_annotation(x=current_date, y=1.02, yref="paper", text="Now", showarrow=False, font=dict(size=11, color="#777"))


fig.update_layout(
    title={
        "text": f"Energy Production with PR-Based Alert System<br><sub style='font-size:13px; color:#777'>{model_type}</sub>",
        "x": 0.5,
        "xanchor": "center",
        "font": {"size": 22, "color": "#2c3e50"},
    },
    xaxis_title="Date",
    yaxis_title="Energy Production (kWh)",
    xaxis=dict(
        showgrid=True,
        gridcolor="rgba(200, 200, 200, 0.2)",
        tickfont=dict(size=13),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="rgba(200, 200, 200, 0.3)",
        tickfont=dict(size=13),
        zeroline=False,
        rangemode="tozero",
    ),
    plot_bgcolor="white",
    paper_bgcolor="#fafafa",
    height=600,
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
        font=dict(size=12),
    ),
    margin=dict(l=60, r=40, t=100, b=100),
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("📉 Performance Ratio Over Time")

with st.expander("ℹ️ Como o PR é calculado"):
    st.markdown("""
    **Performance Ratio (PR)** mede a eficiência real do sistema:
    
    ```
    PR = Yf / Yr
    ```
    
    Onde:
    - **Yf (Final Yield)** = Energia Produzida / Potência Instalada [kWh/kWp]
    - **Yr (Reference Yield)** = Irradiância / 1.0 kW/m² [horas de sol pico]
    
    **Fórmula Simplificada:**
    ```
    PR = Energia [kWh] / (Irradiância [kWh/m²] × Potência [kWp])
    ```
    
    **Exemplo prático:**
    - Energia produzida: 489.26 kWh
    - Irradiância GTI: 5.63 kWh/m²
    - Potência instalada: 125 kWp
    - **PR = 489.26 / (5.63 × 125) = 0.695 = 69.5%**
    """)

COLORS_PR = {
    "theoretical": "#2E86AB",  # Azul profundo
    "observed": "#A23B72",  # Rosa escuro
    "predicted": "#f36440",  # Laranja vibrante
    "reference": "#2ca02c",  # Verde
    "grid": "rgba(200,200,200,0.3)",
    "bg": "#FAFBFC",
}

fig_pr = go.Figure()

# PR Observado (apenas dados históricos/test) - já calculado pela função
df_hist_pr = df_filtered[df_filtered["dataset"].isin(["train", "test"])].copy()
if len(df_hist_pr) > 0 and "pr_obs" in df_hist_pr.columns:
    fig_pr.add_trace(
        go.Scatter(
            x=df_hist_pr["date_time"],
            y=df_hist_pr["pr_obs"],
            name="PR Observado (Real)",
            mode="lines+markers",
            line=dict(color=COLORS_PR["observed"], width=3),
            marker=dict(size=6, color="white", line=dict(color=COLORS_PR["observed"], width=3.5)),
            opacity=0.9,
            hovertemplate="<b>PR Observado</b><br>Data: %{x}<br>PR: %{y:.3f}<extra></extra>",
        )
    )

# PR do Modelo Físico
fig_pr.add_trace(
    go.Scatter(
        x=df_filtered["date_time"],
        y=df_filtered["pr_physical"],
        name="PR Físico (NBR 16274)",
        mode="lines+markers",
        line=dict(color=COLORS_PR["theoretical"], width=3, dash="dash"),
        marker=dict(size=6, color="white", line=dict(color=COLORS_PR["theoretical"], width=3.5)),
        opacity=0.9,
        hovertemplate="<b>PR Físico</b><br>Data: %{x}<br>PR: %{y:.3f}<extra></extra>",
    )
)

# PR do Modelo ML
fig_pr.add_trace(
    go.Scatter(
        x=df_filtered["date_time"],
        y=df_filtered["pr_ml"],
        name="PR Previsto (XGBoost)",
        mode="lines+markers",
        line=dict(color=COLORS_PR["predicted"], width=3),
        marker=dict(size=6, color="white", line=dict(color=COLORS_PR["predicted"], width=3.5)),
        opacity=0.85,
        hovertemplate="<b>PR Previsto</b><br>Data: %{x}<br>PR: %{y:.3f}<extra></extra>",
    )
)

# Linha de referência PR típico
fig_pr.add_hline(
    y=0.80,
    line_dash="dash",
    line_color=COLORS_PR["reference"],
    line_width=2,
    annotation_text="PR Típico Brasília = 0.80",
    annotation_position="top right",
    annotation=dict(font=dict(size=12, color=COLORS_PR["reference"])),
)

# Linhas de threshold para alertas
alert_thresholds = [
    (0.90, "Normal", "#2ca02c", 0.3),
    (0.85, "Baixo", "#8CD867", 0.25),
    (0.75, "Alto", "#ff7f0e", 0.25),
]

for threshold, label, color, opacity in alert_thresholds:
    fig_pr.add_hline(
        y=threshold,
        line_dash="dot",
        line_color=color,
        line_width=1.5,
        opacity=opacity,
        annotation_text=f"{label} ({threshold:.0%})",
        annotation_position="left",
        annotation=dict(font=dict(size=10, color=color)),
    )

# Linha "Now"
fig_pr.add_shape(
    type="line",
    x0=current_date,
    x1=current_date,
    y0=0,
    y1=1,
    yref="paper",
    line=dict(color="rgba(100, 100, 100, 0.5)", width=3, dash="dash"),
)

fig_pr.add_annotation(
    x=current_date, y=1.02, yref="paper", text="Now", showarrow=False, font=dict(size=11, color="#777")
)

if len(df_hist_pr) > 0 and "pr_obs" in df_hist_pr.columns:
    mean_pr_obs = df_hist_pr["pr_obs"].mean()
    mean_pr_physical = df_filtered["pr_physical"].mean()
    mean_pr_ml = df_filtered["pr_ml"].mean()

    subtitle = (
        f'<span style="font-size:14px; color:#777;">'
        f"PR Médio: Observado = {mean_pr_obs:.3f} | "
        f"Físico = {mean_pr_physical:.3f} | "
        f"ML = {mean_pr_ml:.3f}"
        f"</span>"
    )
else:
    mean_pr_physical = df_filtered["pr_physical"].mean()
    mean_pr_ml = df_filtered["pr_ml"].mean()
    subtitle = (
        f'<span style="font-size:14px; color:#777;">'
        f"PR Médio: Físico = {mean_pr_physical:.3f} | ML = {mean_pr_ml:.3f}"
        f"</span>"
    )

fig_pr.update_layout(
    title={
        "text": f"<b>Performance Ratios - Sistema PV</b><br>{subtitle}",
        "x": 0.5,
        "xanchor": "center",
        "font": {"size": 20, "family": "Inter, Arial, sans-serif", "color": "#2c3e50"},
    },
    xaxis_title="<b> </b>",
    yaxis_title="<b>Performance Ratio</b>",
    xaxis=dict(
        showgrid=True,
        gridcolor=COLORS_PR["grid"],
        gridwidth=1,
        tickfont=dict(size=13),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor=COLORS_PR["grid"],
        gridwidth=1,
        tickformat=".2f",
        range=[0, 1.2],
        tickfont=dict(size=13),
    ),
    plot_bgcolor="white",
    paper_bgcolor=COLORS_PR["bg"],
    height=500,
    margin=dict(t=100, b=60, l=80, r=60),
    hovermode="x unified",
    showlegend=True,
    legend=dict(
        orientation="v",
        yanchor="top",
        y=0.98,
        xanchor="right",
        x=0.98,
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="rgba(0, 0, 0, 0.1)",
        borderwidth=1,
        font=dict(size=12),
    ),
)

st.plotly_chart(fig_pr, use_container_width=True)
st.subheader("📉 Performance Ratio Over Time")

COLORS_PR = {
    "theoretical": "#2E86AB",  # Azul profundo
    "observed": "#A23B72",  # Rosa escuro
    "predicted": "#F18F01",  # Laranja vibrante
    "reference": "#7CB342",  # Verde
    "grid": "rgba(200,200,200,0.3)",
    "bg": "#FAFBFC",
}

fig_pr = go.Figure()

# Calcular PR real (observado) apenas para dados históricos
df_filtered["pr_observed"] = np.where(
    df_filtered["pv_energy"] > 0,
    df_filtered["pv_energy"] / (df_filtered["gti"] * 10),  # Assumindo 10kWp
    np.nan,
)

df_hist_pr = df_filtered[df_filtered["dataset"].isin(["train", "test"])].copy()
if len(df_hist_pr) > 0:
    fig_pr.add_trace(
        go.Scatter(
            x=df_hist_pr["date_time"],
            y=df_hist_pr["pr_observed"],
            name="PR Observado (Real)",
            line=dict(color=COLORS_PR["observed"], width=3),
            opacity=0.9,
            hovertemplate="<b>PR Observado</b><br>Data: %{x}<br>PR: %{y:.3f}<extra></extra>",
        )
    )

# PR do Modelo Físico
fig_pr.add_trace(
    go.Scatter(
        x=df_filtered["date_time"],
        y=df_filtered["pr_physical"],
        name="PR Físico (NBR 16274)",
        line=dict(color=COLORS_PR["theoretical"], width=3.5, dash="dot"),
        opacity=0.8,
        hovertemplate="<b>PR Físico</b><br>Data: %{x}<br>PR: %{y:.3f}<extra></extra>",
    )
)

# PR do Modelo ML
fig_pr.add_trace(
    go.Scatter(
        x=df_filtered["date_time"],
        y=df_filtered["pr_ml"],
        name="PR Previsto (XGBoost)",
        line=dict(color=COLORS_PR["predicted"], width=3),
        opacity=0.85,
        hovertemplate="<b>PR Previsto</b><br>Data: %{x}<br>PR: %{y:.3f}<extra></extra>",
    )
)

# Linha de referência PR típico
fig_pr.add_hline(
    y=0.80,
    line_dash="dash",
    line_color=COLORS_PR["reference"],
    line_width=2,
    annotation_text="PR Típico Brasília = 0.80",
    annotation_position="top right",
    annotation=dict(font=dict(size=12, color=COLORS_PR["reference"])),
)

# Linhas de threshold para alertas
alert_thresholds = [
    (0.90, "Normal", "#2ca02c", 0.3),
    (0.85, "Baixo", "#8CD867", 0.25),
    (0.75, "Alto", "#ff7f0e", 0.25),
]

for threshold, label, color, opacity in alert_thresholds:
    fig_pr.add_hline(
        y=threshold,
        line_dash="dot",
        line_color=color,
        line_width=1.5,
        opacity=opacity,
        annotation_text=f"{label} ({threshold:.0%})",
        annotation_position="left",
        annotation=dict(font=dict(size=10, color=color)),
    )

# Linha "Now"
fig_pr.add_shape(
    type="line",
    x0=current_date,
    x1=current_date,
    y0=0,
    y1=1,
    yref="paper",
    line=dict(color="rgba(100, 100, 100, 0.5)", width=3.5, dash="dash"),
)

fig_pr.add_annotation(
    x=current_date, y=1.02, yref="paper", text="Now", showarrow=False, font=dict(size=11, color="#777")
)

# Calcular médias
if len(df_hist_pr) > 0:
    mean_pr_obs = df_hist_pr["pr_observed"].mean()
    mean_pr_physical = df_filtered["pr_physical"].mean()
    mean_pr_ml = df_filtered["pr_ml"].mean()

    subtitle = (
        f'<span style="font-size:14px; color:#777;">'
        f"PR Médio: Observado = {mean_pr_obs:.3f} | "
        f"Físico = {mean_pr_physical:.3f} | "
        f"ML = {mean_pr_ml:.3f}"
        f"</span>"
    )
else:
    mean_pr_physical = df_filtered["pr_physical"].mean()
    mean_pr_ml = df_filtered["pr_ml"].mean()
    subtitle = (
        f'<span style="font-size:14px; color:#777;">'
        f"PR Médio: Físico = {mean_pr_physical:.3f} | ML = {mean_pr_ml:.3f}"
        f"</span>"
    )

fig_pr.update_layout(
    title={
        "text": f"<b>Performance Ratios - Sistema PV</b><br>{subtitle}",
        "x": 0.5,
        "xanchor": "center",
        "font": {"size": 20, "family": "Inter, Arial, sans-serif", "color": "#2c3e50"},
    },
    xaxis_title="<b> </b>",
    yaxis_title="<b>Performance Ratio</b>",
    xaxis=dict(
        showgrid=True,
        gridcolor=COLORS_PR["grid"],
        gridwidth=1,
        tickfont=dict(size=13),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor=COLORS_PR["grid"],
        gridwidth=1,
        tickformat=".2f",
        range=[0, 1.2],
        tickfont=dict(size=13),
    ),
    plot_bgcolor="white",
    paper_bgcolor=COLORS_PR["bg"],
    height=500,
    margin=dict(t=100, b=60, l=80, r=60),
    hovermode="x unified",
    showlegend=True,
    legend=dict(
        orientation="v",
        yanchor="top",
        y=0.98,
        xanchor="right",
        x=0.98,
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="rgba(0, 0, 0, 0.1)",
        borderwidth=1,
        font=dict(size=12),
    ),
)

st.plotly_chart(fig_pr, use_container_width=True)

# Tabela de Alertas Críticos
st.markdown("---")
st.subheader("🚨 Critical and High Priority Alerts")

critical_data = df_filtered[df_filtered[alert_col] >= 7].copy()

if len(critical_data) > 0:
    critical_data["alert_label"] = critical_data[alert_col].map(alert_labels)

    display_cols = [
        "date_time",
        "pv_energy",
        energy_col,
        pr_col,
        "alert_label",
        "gti",
        "ghi",
        "air_temp",
    ]

    # Renomear colunas para melhor apresentação
    col_names = {
        "date_time": "Date",
        "pv_energy": "Observed Energy (kWh)",
        energy_col: "Predicted Energy (kWh)",
        pr_col: "Performance Ratio",
        "alert_label": "Alert Level",
        "gti": "GTI (kWh/m²)",
        "ghi": "GHI (kWh/m²)",
        "air_temp": "Temp (°C)",
    }

    critical_display = critical_data[display_cols].rename(columns=col_names)

    st.dataframe(
        critical_display.style.format({
            "Observed Energy (kWh)": "{:.2f}",
            "Predicted Energy (kWh)": "{:.2f}",
            "Performance Ratio": "{:.3f}",
            "GTI (kWh/m²)": "{:.2f}",
            "GHI (kWh/m²)": "{:.2f}",
            "Temp (°C)": "{:.2f}",
        }).applymap(
            lambda x: "background-color: #fee"
            if x == "Crítico"
            else ("background-color: #fff5e6" if x == "Alto" else ""),
            subset=["Alert Level"],
        ),
        use_container_width=True,
        height=400,
    )

    # Primeira detecção de alerta crítico
    first_critical = critical_data["date_time"].min()
    st.info(f"📅 First critical alert detected on: {first_critical.strftime('%Y-%m-%d')}")

    # Análise de tendência de alertas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 Alert Distribution")
        # Gráfico de pizza com distribuição de alertas críticos
        alert_dist = critical_data[alert_col].value_counts()

        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=[alert_labels[level] for level in alert_dist.index],
                    values=alert_dist.values,
                    marker=dict(colors=[alert_colors[level] for level in alert_dist.index]),
                    hole=0.4,
                    textinfo="label+percent",
                    textposition="auto",
                )
            ]
        )

        fig_pie.update_layout(
            title="Distribution of Critical Alerts",
            height=350,
            showlegend=True,
            paper_bgcolor=COLORS_PR["bg"],
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.markdown("### 📈 Alert Frequency Over Time")
        # Gráfico de barras com frequência de alertas por semana
        critical_data_copy = critical_data.copy()
        critical_data_copy["week"] = critical_data_copy["date_time"].dt.to_period("W").astype(str)
        weekly_alerts = critical_data_copy.groupby(["week", alert_col]).size().reset_index(name="count")

        fig_bar = go.Figure()

        for alert_level in [7, 10]:
            if alert_level in weekly_alerts[alert_col].values:
                data_level = weekly_alerts[weekly_alerts[alert_col] == alert_level]
                fig_bar.add_trace(
                    go.Bar(
                        x=data_level["week"],
                        y=data_level["count"],
                        name=alert_labels[alert_level],
                        marker_color=alert_colors[alert_level],
                    )
                )

        fig_bar.update_layout(
            title="Weekly Alert Frequency",
            xaxis_title="Week",
            yaxis_title="Number of Alerts",
            barmode="stack",
            height=350,
            showlegend=True,
            paper_bgcolor=COLORS_PR["bg"],
            plot_bgcolor="white",
        )

        st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.success("✅ No critical or high priority alerts in the selected period!")

# Gráfico adicional: Correlation entre PR e condições ambientais
st.markdown("---")
st.subheader("🌡️ PR vs Environmental Conditions")

col1, col2 = st.columns(2)

with col1:
    # PR vs Temperatura
    fig_temp = go.Figure()

    # Colorir pontos por nível de alerta
    for alert_level, color in alert_colors.items():
        mask_temp = df_filtered[alert_col] == alert_level
        if mask_temp.any():
            fig_temp.add_trace(
                go.Scatter(
                    x=df_filtered.loc[mask_temp, "air_temp"],
                    y=df_filtered.loc[mask_temp, pr_col],
                    mode="markers",
                    name=alert_labels[alert_level],
                    marker=dict(
                        color=color,
                        size=8,
                        opacity=0.6,
                        symbol=marker_symbols[alert_level],
                    ),
                )
            )

    fig_temp.update_layout(
        title="PR vs Air Temperature",
        xaxis_title="Air Temperature (°C)",
        yaxis_title="Performance Ratio",
        height=400,
        showlegend=True,
        paper_bgcolor=COLORS_PR["bg"],
        plot_bgcolor="white",
        hovermode="closest",
    )

    st.plotly_chart(fig_temp, use_container_width=True)

with col2:
    # PR vs Irradiância
    fig_irr = go.Figure()

    for alert_level, color in alert_colors.items():
        mask_irr = df_filtered[alert_col] == alert_level
        if mask_irr.any():
            fig_irr.add_trace(
                go.Scatter(
                    x=df_filtered.loc[mask_irr, "gti"],
                    y=df_filtered.loc[mask_irr, pr_col],
                    mode="markers",
                    name=alert_labels[alert_level],
                    marker=dict(
                        color=color,
                        size=8,
                        opacity=0.6,
                        symbol=marker_symbols[alert_level],
                    ),
                )
            )

    fig_irr.update_layout(
        title="PR vs Global Tilted Irradiance",
        xaxis_title="GTI (kWh/m²)",
        yaxis_title="Performance Ratio",
        height=400,
        showlegend=True,
        paper_bgcolor=COLORS_PR["bg"],
        plot_bgcolor="white",
        hovermode="closest",
    )

    st.plotly_chart(fig_irr, use_container_width=True)

# Detalhes Técnicos e Recomendações
with st.expander("ℹ️ About the PR-Based Alert System"):
    st.markdown("""
    ### Performance Ratio (PR)
    
    O Performance Ratio (PR) é um indicador chave que mede a eficiência real de um sistema fotovoltaico 
    comparado com sua eficiência teórica. É calculado como:
    
    **PR = Energia Real Produzida / Energia Teórica Esperada**
    
    ### Sistema de Classificação de Alertas
    
    O sistema classifica automaticamente o desempenho do sistema em 5 níveis:
    
    - **Normal (PR ≥ 90%)**: Sistema operando dentro dos parâmetros esperados
    - **Baixo (85% ≤ PR < 90%)**: Leve degradação, requer monitoramento
    - **Médio (80% ≤ PR < 85%)**: Degradação moderada, verificar possíveis causas
    - **Alto (75% ≤ PR < 80%)**: Problema significativo, investigação recomendada
    - **Crítico (PR < 75%)**: Falha crítica, ação imediata necessária
    
    ### Possíveis Causas de Baixo PR
    
    - Sombreamento de painéis
    - Sujeira ou poeira acumulada
    - Problemas em inversores
    - Degradação de componentes
    - Falhas em conexões elétricas
    - Condições climáticas adversas
    """)

# Recomendações baseadas nos alertas
if len(df_filtered[df_filtered[alert_col] >= 5]) > 0:
    with st.expander("💡 Recommended Actions Based on Current Alerts"):
        # Contar alertas por nível
        alert_summary = df_filtered[alert_col].value_counts().sort_index(ascending=False)

        st.markdown("### 🔍 Alert Analysis")

        # Alertas Críticos
        if alert_summary.get(10, 0) > 0:
            st.markdown("""
            #### 🔴 CRITICAL Alerts Detected
            
            **Immediate Actions Required:**
            1. **Emergency Inspection**: Dispatch technical team immediately
            2. **System Check**: Verify inverter status and error logs
            3. **Visual Inspection**: Check for obvious damage or disconnections
            4. **Safety First**: Ensure all safety protocols are followed
            5. **Documentation**: Log all findings and actions taken
            
            **Possible Root Causes:**
            - Inverter failure or shutdown
            - Major electrical fault
            - Complete module failure
            - Severe weather damage
            - Grid connection issues
            """)

        # Alertas Altos
        if alert_summary.get(7, 0) > 0:
            st.markdown("""
            #### 🔶 HIGH Priority Alerts
            
            **Actions to Take Within 24-48 Hours:**
            1. **Schedule Inspection**: Plan on-site visit for detailed assessment
            2. **Remote Monitoring**: Review SCADA data for patterns
            3. **Performance Analysis**: Compare with nearby systems
            4. **Weather Check**: Rule out environmental factors
            5. **Maintenance Planning**: Prepare for potential repairs
            
            **Common Causes:**
            - Significant soiling on panels
            - Partial inverter degradation
            - String-level issues
            - Shading problems
            - Temperature-related efficiency loss
            """)

        # Alertas Médios
        if alert_summary.get(5, 0) > 0:
            st.markdown("""
            #### ⚠️ MEDIUM Priority Alerts
            
            **Actions to Take Within 1 Week:**
            1. **Data Analysis**: Review historical trends
            2. **Cleaning Schedule**: Consider panel cleaning
            3. **Preventive Maintenance**: Schedule routine inspection
            4. **Performance Benchmarking**: Compare with expected values
            5. **Monitoring**: Increase frequency of checks
            
            **Typical Causes:**
            - Accumulated dust/dirt
            - Minor shading issues
            - Aging components
            - Seasonal variations
            - Grid curtailment
            """)

        st.markdown("---")
        st.markdown("### 📋 Maintenance Checklist")
        st.markdown("""
        - [ ] Check inverter display for error codes
        - [ ] Inspect DC and AC circuit breakers
        - [ ] Verify module connections and wiring
        - [ ] Clean panels if soiling is evident
        - [ ] Test string voltages and currents
        - [ ] Review monitoring system data
        - [ ] Compare with weather data
        - [ ] Document all findings
        - [ ] Update maintenance log
        - [ ] Schedule follow-up inspection
        """)

# Estatísticas gerais do sistema
st.markdown("---")
st.subheader("📊 System Performance Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### Availability")
    # Calcular disponibilidade (dias sem alertas críticos)
    days_total = len(df_filtered)
    days_critical = len(df_filtered[df_filtered[alert_col] == 10])
    availability = ((days_total - days_critical) / days_total * 100) if days_total > 0 else 0
    st.metric("System Availability", f"{availability:.1f}%", help="Percentage of days without critical alerts")

with col2:
    st.markdown("### Average PR")
    avg_pr = df_filtered[pr_col].mean()
    pr_status = "🟢" if avg_pr >= 0.80 else ("🟡" if avg_pr >= 0.70 else "🔴")
    st.metric("Mean Performance Ratio", f"{pr_status} {avg_pr:.3f}", help="Average PR for the selected period")

with col3:
    st.markdown("### Energy Loss")
    # Estimar perda de energia devido a baixo PR
    if "pr_obs" in df_filtered.columns:
        ideal_pr = 0.85  # PR ideal de referência
        actual_energy = df_filtered["pv_energy"].sum()
        potential_energy = df_filtered.apply(
            lambda row: row["gti"] * 125 * ideal_pr if pd.notna(row["gti"]) else 0, axis=1
        ).sum()
        energy_loss_pct = ((potential_energy - actual_energy) / potential_energy * 100) if potential_energy > 0 else 0
        st.metric(
            "Estimated Energy Loss",
            f"{energy_loss_pct:.1f}%",
            delta=f"-{energy_loss_pct:.1f}%",
            delta_color="inverse",
            help="Estimated energy loss vs ideal PR of 85%",
        )
    else:
        st.metric("Energy Loss", "N/A", help="Requires observed energy data")

with col4:
    st.markdown("### Alert Rate")
    alert_rate = (
        (len(df_filtered[df_filtered[alert_col] >= 5]) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
    )
    st.metric(
        "Medium+ Alert Rate",
        f"{alert_rate:.1f}%",
        delta=f"{alert_rate:.1f}%",
        delta_color="inverse",
        help="Percentage of days with medium or higher alerts",
    )

st.markdown("---")
st.caption("Copyright ©2015-2025 MEPA All rights reserved.")


# =====================================================================================================================
# from datetime import datetime, timedelta
# from pathlib import Path

# import numpy as np
# import pandas as pd
# import plotly.graph_objects as go
# import streamlit as st

# from src.config import settings
# from src.config.styles import render_col_divider

# st.set_page_config(page_title="Anomaly Detection", page_icon="🔍", layout="wide")

# st.markdown(
#     """
#     <style>
#     .metric-card {
#         background-color: #f0f2f6;
#         padding: 15px;
#         border-radius: 5px;
#         margin: 5px 0;
#     }
#     .alert-critical {
#         background-color: #fee;
#         border-left: 4px solid #d62728;
#         padding: 10px;
#         margin: 5px 0;
#     }
#     .alert-high {
#         background-color: #fff5e6;
#         border-left: 4px solid #ff7f0e;
#         padding: 10px;
#         margin: 5px 0;
#     }
#     .alert-medium {
#         background-color: #fffef0;
#         border-left: 4px solid #f2cd60;
#         padding: 10px;
#         margin: 5px 0;
#     }
#     .alert-low {
#         background-color: #f0fff0;
#         border-left: 4px solid #8CD867;
#         padding: 10px;
#         margin: 5px 0;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# st.title("🔍 Anomaly Detection System")
# st.markdown("### Performance Ratio (PR) Based Alert System")


# def anomaly_detect(pr_model):
#     """Classifica o nível de alerta baseado no PR_Model"""
#     if pr_model >= 0.90:
#         return 1  # Normal
#     elif pr_model >= 0.85:
#         return 3  # Baixo
#     elif pr_model >= 0.80:
#         return 5  # Médio
#     elif pr_model >= 0.75:
#         return 7  # Alto
#     else:
#         return 10  # Crítico


# # Configurações de cores e símbolos
# alert_colors = {
#     1: "#2ca02c",  # Verde - Normal
#     3: "#8CD867",  # Verde claro - Baixo
#     5: "#f2cd60",  # Amarelo - Médio
#     7: "#ff7f0e",  # Laranja - Alto
#     10: "#d62728",  # Vermelho - Crítico
# }

# marker_symbols = {
#     1: "circle",
#     3: "diamond",
#     5: "triangle-up",
#     7: "x",
#     10: "star",
# }

# alert_labels = {1: "Normal", 3: "Baixo", 5: "Médio", 7: "Alto", 10: "Crítico"}

# # Carregar dados
# file_name = "fcte_ued_pt1d.csv"
# csv_path = Path(settings.DATA_DIR / "result" / file_name)

# if not csv_path.exists():
#     st.error("📁 Arquivo de dados não encontrado. Por favor, verifique o caminho do arquivo.")
#     st.stop()

# df = pd.read_csv(csv_path)
# df["date_time"] = pd.to_datetime(df["date_time"])

# # Calcular PR_Model para os dados
# df["pr_physical"] = df["pv_energy_est"] / (df["gti"] * 10)  # Assumindo 10kWp de potência instalada
# df["pr_ml"] = df["pv_energy_pred"] / (df["gti"] * 10)

# # Aplicar detecção de anomalias
# df["alert_physical"] = df["pr_physical"].apply(anomaly_detect)
# df["alert_ml"] = df["pr_ml"].apply(anomaly_detect)

# st.write("---")
# st.dataframe(
#     df[
#         [
#             "date_time",
#             "pv_energy",
#             "pv_energy_est",
#             "pv_energy_pred",
#             "gti",
#             "pr_physical",
#             "pr_ml",
#             "alert_physical",
#             "alert_ml",
#         ]
#     ].head(100),
#     use_container_width=True,
# )
# st.write("---")

# # Sidebar
# with st.sidebar:
#     st.header("ANOMALY DETECTION")

#     current_date = pd.to_datetime("2025-10-05")
#     recent_data = df[df["date_time"] >= (current_date - timedelta(days=7))]

#     critical_count = len(recent_data[recent_data["alert_ml"] >= 7])

#     if critical_count > 0:
#         st.markdown(f"### ⚠️ {critical_count} Critical Alerts")
#         st.caption("Last 7 days")
#     else:
#         st.markdown("### ✅ No Critical Alerts")
#         st.caption("Last 7 days")

#     st.markdown("---")
#     st.subheader("ALERT THRESHOLDS")
#     st.markdown("""
#     - **Normal**: PR ≥ 90%
#     - **Low**: 85% ≤ PR < 90%
#     - **Medium**: 80% ≤ PR < 85%
#     - **High**: 75% ≤ PR < 80%
#     - **Critical**: PR < 75%
#     """)

#     st.markdown("---")
#     st.subheader("MODEL SELECTION")
#     model_type = st.radio("Select Model for Analysis:", ["ML Model (XGBoost)", "Physical Model (NBR 16274)"], index=0)

# # Selecionar coluna de alerta baseada no modelo escolhido
# alert_col = "alert_ml" if "ML Model" in model_type else "alert_physical"
# pr_col = "pr_ml" if "ML Model" in model_type else "pr_physical"
# energy_col = "pv_energy_pred" if "ML Model" in model_type else "pv_energy_est"

# # Filtros de data
# col1, col2, col3 = st.columns([2, 2, 6])

# with col1:
#     date_start = st.date_input("Start Date", current_date - timedelta(days=90))

# with col2:
#     date_end = st.date_input("End Date", current_date + timedelta(days=14))

# # Filtrar dados por data
# mask = (df["date_time"] >= pd.to_datetime(date_start)) & (df["date_time"] <= pd.to_datetime(date_end))
# df_filtered = df[mask].copy()

# # Separar dados históricos e forecast
# df_historical = df_filtered[df_filtered["dataset"] == "test"].copy()
# df_forecast = df_filtered[df_filtered["dataset"] == "forecast"].copy()

# # Métricas de Alerta
# st.markdown("---")
# st.subheader("📊 Alert Statistics")

# alert_counts = df_filtered[alert_col].value_counts().sort_index()

# col1, col2, col3, col4, col5 = st.columns(5)

# with col1:
#     normal_count = alert_counts.get(1, 0)
#     st.metric("✅ Normal", normal_count, help="PR ≥ 90%")

# with col2:
#     low_count = alert_counts.get(3, 0)
#     st.metric("💚 Low", low_count, help="85% ≤ PR < 90%")

# with col3:
#     medium_count = alert_counts.get(5, 0)
#     st.metric("⚠️ Medium", medium_count, help="80% ≤ PR < 85%")

# with col4:
#     high_count = alert_counts.get(7, 0)
#     st.metric("🔶 High", high_count, help="75% ≤ PR < 80%")

# with col5:
#     critical_count = alert_counts.get(10, 0)
#     st.metric("🔴 Critical", critical_count, help="PR < 75%")

# # Percentual de alertas críticos
# total_points = len(df_filtered)
# high_priority_alerts = len(df_filtered[df_filtered[alert_col] >= 5])
# critical_alerts = len(df_filtered[df_filtered[alert_col] >= 7])

# col1, col2, col3 = st.columns(3)
# with col1:
#     st.metric("Total Points Analyzed", total_points)
# with col2:
#     pct_high = (high_priority_alerts / total_points * 100) if total_points > 0 else 0
#     st.metric("Medium+ Alerts (%)", f"{pct_high:.1f}%")
# with col3:
#     pct_critical = (critical_alerts / total_points * 100) if total_points > 0 else 0
#     st.metric("High+ Alerts (%)", f"{pct_critical:.1f}%", delta=f"{pct_critical:.1f}%", delta_color="inverse")

# # Gráfico Principal: Energy Production com Sistema de Alertas
# st.markdown("---")
# st.subheader("📈 Energy Production with Alert System")

# fig = go.Figure()

# # Cores para train/test
# color_train = "#1f77b4"
# color_test = "#2ca02c"
# color_pred = "#bcbd22"

# # Dados de treino (se existirem)
# df_train = df_filtered[df_filtered["dataset"] == "train"]
# if len(df_train) > 0:
#     fig.add_trace(
#         go.Scatter(
#             x=df_train["date_time"],
#             y=df_train["pv_energy"],
#             name="Train",
#             mode="lines",
#             line=dict(color=color_train, width=3.5),
#             opacity=0.9,
#         )
#     )

# # Dados de teste (histórico)
# if len(df_historical) > 0:
#     fig.add_trace(
#         go.Scatter(
#             x=df_historical["date_time"],
#             y=df_historical["pv_energy"],
#             name="Test (Observed)",
#             mode="lines",
#             line=dict(color=color_test, width=3.5),
#             opacity=0.9,
#         )
#     )

# # Previsão
# fig.add_trace(
#     go.Scatter(
#         x=df_filtered["date_time"],
#         y=df_filtered[energy_col],
#         name=f"Prediction ({model_type})",
#         mode="lines",
#         line=dict(color=color_pred, width=3.5, dash="dash"),
#         opacity=0.85,
#     )
# )

# # Adicionar marcadores de alerta (exceto Normal)
# for alert_level in [3, 5, 7, 10]:
#     mask_alert = df_filtered[alert_col] == alert_level
#     if mask_alert.any():
#         fig.add_trace(
#             go.Scatter(
#                 x=df_filtered.loc[mask_alert, "date_time"],
#                 y=df_filtered.loc[mask_alert, "pv_energy"],
#                 name=f"Alert {alert_labels[alert_level]}",
#                 mode="markers",
#                 marker=dict(
#                     color=alert_colors[alert_level],
#                     size=10,
#                     symbol=marker_symbols[alert_level],
#                     line=dict(width=1, color="black"),
#                 ),
#                 opacity=0.8,
#                 hovertemplate=(
#                     f"<b>Alert {alert_labels[alert_level]}</b><br>"
#                     "Date: %{x}<br>"
#                     "PR: %{customdata:.3f}<br>"
#                     "Energy: %{y:.2f} kWh<br>"
#                     "<extra></extra>"
#                 ),
#                 customdata=df_filtered.loc[mask_alert, pr_col],
#             )
#         )

# # Linha "Now"
# fig.add_shape(
#     type="line",
#     x0=current_date,
#     x1=current_date,
#     y0=0,
#     y1=1,
#     yref="paper",
#     line=dict(color="rgba(100, 100, 100, 0.5)", width=3.5, dash="dash"),
# )

# fig.add_annotation(x=current_date, y=1.02, yref="paper", text="Now", showarrow=False, font=dict(size=11, color="#777"))

# fig.update_layout(
#     title={
#         "text": f"Energy Production with PR-Based Alert System<br><sub style='font-size:13px; color:#777'>{model_type}</sub>",
#         "x": 0.5,
#         "xanchor": "center",
#         "font": {"size": 22, "color": "#2c3e50"},
#     },
#     xaxis_title="Date",
#     yaxis_title="Energy Production (kWh)",
#     xaxis=dict(
#         showgrid=True,
#         gridcolor="rgba(200, 200, 200, 0.2)",
#         tickfont=dict(size=13),
#     ),
#     yaxis=dict(
#         showgrid=True,
#         gridcolor="rgba(200, 200, 200, 0.3)",
#         tickfont=dict(size=13),
#         zeroline=False,
#         rangemode="tozero",
#     ),
#     plot_bgcolor="white",
#     paper_bgcolor="#fafafa",
#     height=600,
#     hovermode="x unified",
#     showlegend=True,
#     legend=dict(
#         orientation="h",
#         yanchor="top",
#         y=-0.15,
#         xanchor="center",
#         x=0.5,
#         bgcolor="rgba(255, 255, 255, 0.9)",
#         bordercolor="rgba(0, 0, 0, 0.1)",
#         borderwidth=1,
#         font=dict(size=12),
#     ),
#     margin=dict(l=60, r=40, t=100, b=100),
# )

# st.plotly_chart(fig, use_container_width=True)

# # Gráfico de Performance Ratio ao longo do tempo
# st.markdown("---")
# st.subheader("📉 Performance Ratio Over Time")

# # Cores personalizadas
# COLORS_PR = {
#     "theoretical": "#2E86AB",  # Azul profundo
#     "observed": "#A23B72",  # Rosa escuro
#     "predicted": "#F18F01",  # Laranja vibrante
#     "reference": "#7CB342",  # Verde
#     "grid": "rgba(200,200,200,0.3)",
#     "bg": "#FAFBFC",
# }

# fig_pr = go.Figure()

# # Calcular PR real (observado) apenas para dados históricos
# df_filtered["pr_observed"] = np.where(
#     df_filtered["pv_energy"] > 0,
#     df_filtered["pv_energy"] / (df_filtered["gti"] * 10),  # Assumindo 10kWp
#     np.nan,
# )

# # PR Observado (apenas dados históricos/test)
# df_hist_pr = df_filtered[df_filtered["dataset"].isin(["train", "test"])].copy()
# if len(df_hist_pr) > 0:
#     fig_pr.add_trace(
#         go.Scatter(
#             x=df_hist_pr["date_time"],
#             y=df_hist_pr["pr_observed"],
#             name="PR Observado (Real)",
#             line=dict(color=COLORS_PR["observed"], width=3),
#             opacity=0.9,
#             hovertemplate="<b>PR Observado</b><br>Data: %{x}<br>PR: %{y:.3f}<extra></extra>",
#         )
#     )

# # PR do Modelo Físico
# fig_pr.add_trace(
#     go.Scatter(
#         x=df_filtered["date_time"],
#         y=df_filtered["pr_physical"],
#         name="PR Físico (NBR 16274)",
#         line=dict(color=COLORS_PR["theoretical"], width=3.5, dash="dot"),
#         opacity=0.8,
#         hovertemplate="<b>PR Físico</b><br>Data: %{x}<br>PR: %{y:.3f}<extra></extra>",
#     )
# )

# # PR do Modelo ML
# fig_pr.add_trace(
#     go.Scatter(
#         x=df_filtered["date_time"],
#         y=df_filtered["pr_ml"],
#         name="PR Previsto (XGBoost)",
#         line=dict(color=COLORS_PR["predicted"], width=3),
#         opacity=0.85,
#         hovertemplate="<b>PR Previsto</b><br>Data: %{x}<br>PR: %{y:.3f}<extra></extra>",
#     )
# )

# # Linha de referência PR típico
# fig_pr.add_hline(
#     y=0.80,
#     line_dash="dash",
#     line_color=COLORS_PR["reference"],
#     line_width=2,
#     annotation_text="PR Típico Brasília = 0.80",
#     annotation_position="top right",
#     annotation=dict(font=dict(size=12, color=COLORS_PR["reference"])),
# )

# # Linhas de threshold para alertas
# alert_thresholds = [
#     (0.90, "Normal", "#2ca02c", 0.3),
#     (0.85, "Baixo", "#8CD867", 0.25),
#     (0.75, "Alto", "#ff7f0e", 0.25),
# ]

# for threshold, label, color, opacity in alert_thresholds:
#     fig_pr.add_hline(
#         y=threshold,
#         line_dash="dot",
#         line_color=color,
#         line_width=1.5,
#         opacity=opacity,
#         annotation_text=f"{label} ({threshold:.0%})",
#         annotation_position="left",
#         annotation=dict(font=dict(size=10, color=color)),
#     )

# # Linha "Now"
# fig_pr.add_shape(
#     type="line",
#     x0=current_date,
#     x1=current_date,
#     y0=0,
#     y1=1,
#     yref="paper",
#     line=dict(color="rgba(100, 100, 100, 0.5)", width=3.5, dash="dash"),
# )

# fig_pr.add_annotation(
#     x=current_date, y=1.02, yref="paper", text="Now", showarrow=False, font=dict(size=11, color="#777")
# )

# # Calcular médias
# if len(df_hist_pr) > 0:
#     mean_pr_obs = df_hist_pr["pr_observed"].mean()
#     mean_pr_physical = df_filtered["pr_physical"].mean()
#     mean_pr_ml = df_filtered["pr_ml"].mean()

#     subtitle = (
#         f'<span style="font-size:14px; color:#777;">'
#         f"PR Médio: Observado = {mean_pr_obs:.3f} | "
#         f"Físico = {mean_pr_physical:.3f} | "
#         f"ML = {mean_pr_ml:.3f}"
#         f"</span>"
#     )
# else:
#     mean_pr_physical = df_filtered["pr_physical"].mean()
#     mean_pr_ml = df_filtered["pr_ml"].mean()
#     subtitle = (
#         f'<span style="font-size:14px; color:#777;">'
#         f"PR Médio: Físico = {mean_pr_physical:.3f} | ML = {mean_pr_ml:.3f}"
#         f"</span>"
#     )

# fig_pr.update_layout(
#     title={
#         "text": f"<b>Performance Ratios - Sistema PV</b><br>{subtitle}",
#         "x": 0.5,
#         "xanchor": "center",
#         "font": {"size": 20, "family": "Inter, Arial, sans-serif", "color": "#2c3e50"},
#     },
#     xaxis_title="<b> </b>",
#     yaxis_title="<b>Performance Ratio</b>",
#     xaxis=dict(
#         showgrid=True,
#         gridcolor=COLORS_PR["grid"],
#         gridwidth=1,
#         tickfont=dict(size=13),
#     ),
#     yaxis=dict(
#         showgrid=True,
#         gridcolor=COLORS_PR["grid"],
#         gridwidth=1,
#         tickformat=".2f",
#         range=[0, 1.2],
#         tickfont=dict(size=13),
#     ),
#     plot_bgcolor="white",
#     paper_bgcolor=COLORS_PR["bg"],
#     height=500,
#     margin=dict(t=100, b=60, l=80, r=60),
#     hovermode="x unified",
#     showlegend=True,
#     legend=dict(
#         orientation="v",
#         yanchor="top",
#         y=0.98,
#         xanchor="right",
#         x=0.98,
#         bgcolor="rgba(255, 255, 255, 0.9)",
#         bordercolor="rgba(0, 0, 0, 0.1)",
#         borderwidth=1,
#         font=dict(size=12),
#     ),
# )

# st.plotly_chart(fig_pr, use_container_width=True)

# # Tabela de Alertas Críticos
# st.markdown("---")
# st.subheader("🚨 Critical and High Priority Alerts")

# critical_data = df_filtered[df_filtered[alert_col] >= 7].copy()

# if len(critical_data) > 0:
#     critical_data["alert_label"] = critical_data[alert_col].map(alert_labels)

#     display_cols = [
#         "date_time",
#         "pv_energy",
#         energy_col,
#         pr_col,
#         "alert_label",
#         "gti",
#         "ghi",
#         "air_temp",
#     ]

#     st.dataframe(
#         critical_data[display_cols]
#         .style.format({
#             "pv_energy": "{:.2f}",
#             energy_col: "{:.2f}",
#             pr_col: "{:.3f}",
#             "gti": "{:.2f}",
#             "ghi": "{:.2f}",
#             "air_temp": "{:.2f}",
#         })
#         .applymap(
#             lambda x: "background-color: #fee"
#             if x == "Crítico"
#             else ("background-color: #fff5e6" if x == "Alto" else ""),
#             subset=["alert_label"],
#         ),
#         use_container_width=True,
#         height=400,
#     )

#     # Primeira detecção de alerta crítico
#     first_critical = critical_data["date_time"].min()
#     st.info(f"📅 First critical alert detected on: {first_critical.strftime('%Y-%m-%d')}")
# else:
#     st.success("✅ No critical or high priority alerts in the selected period!")

# # Detalhes Técnicos
# with st.expander("ℹ️ About the PR-Based Alert System"):
#     st.markdown("""
#     ### Performance Ratio (PR)

#     O Performance Ratio (PR) é um indicador chave que mede a eficiência real de um sistema fotovoltaico
#     comparado com sua eficiência teórica. É calculado como:

#     **PR = Energia Real Produzida / Energia Teórica Esperada**

#     ### Sistema de Classificação de Alertas

#     O sistema classifica automaticamente o desempenho do sistema em 5 níveis:

#     - **Normal (PR ≥ 90%)**: Sistema operando dentro dos parâmetros esperados
#     - **Baixo (85% ≤ PR < 90%)**: Leve degradação, requer monitoramento
#     - **Médio (80% ≤ PR < 85%)**: Degradação moderada, verificar possíveis causas
#     - **Alto (75% ≤ PR < 80%)**: Problema significativo, investigação recomendada
#     - **Crítico (PR < 75%)**: Falha crítica, ação imediata necessária

#     ### Possíveis Causas de Baixo PR

#     - Sombreamento de painéis
#     - Sujeira ou poeira acumulada
#     - Problemas em inversores
#     - Degradação de componentes
#     - Falhas em conexões elétricas
#     - Condições climáticas adversas
#     """)

# st.markdown("---")
# st.caption("Copyright ©2015-2025 MEPA All rights reserved.")
