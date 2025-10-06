from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly import express as px

from src.config.settings import MONTH_MAPPING
from src.config.styles import ThemeManager, render_col_divider
from src.data.data_loader import load_historical_data


def create_yearly_dataframe(df, year):
    df_year = df.copy()

    year_mask = df_year.index.year == year
    df_year = df_year.loc[year_mask]

    if df_year.empty:
        return pd.DataFrame()

    monthly_data = df_year.groupby(df_year.index.month)["pv_energy"].sum()

    full_year_df = pd.DataFrame(index=range(1, 13), columns=["pv_energy"])
    full_year_df.index.name = "month"
    full_year_df["pv_energy"] = 0.0

    full_year_df.update(monthly_data.to_frame())
    full_year_df["pv_energy"] = full_year_df["pv_energy"].fillna(0.0)
    full_year_df["month_name"] = [MONTH_MAPPING[i] for i in range(1, 13)]

    return full_year_df


def calculate_previous_year_data(df_historical, selected_year):
    prev_year = selected_year - 1
    prev_year_mask = df_historical.index.year == prev_year
    prev_year_df = df_historical.loc[prev_year_mask]

    if prev_year_df.empty:
        return pd.DataFrame()

    return prev_year_df.groupby(prev_year_df.index.month)["pv_energy"].sum()


def calculate_yearly_metrics(plant, yearly_df):
    total_energy = yearly_df["pv_energy"].sum()
    avg_monthly = yearly_df["pv_energy"].mean()
    best_month_value = yearly_df["pv_energy"].max()
    best_month_idx = yearly_df["pv_energy"].idxmax()
    best_month_name = MONTH_MAPPING[best_month_idx] if best_month_value > 0 else "N/A"

    return {
        "total_energy": total_energy / 1000,
        "avg_monthly": avg_monthly / 1000,
        "best_month": best_month_value / 1000,
        "best_month_name": best_month_name,
        "avg_monthly_yield": avg_monthly / plant["power_kwp"] if plant.get("power_kwp", 0) > 0 else 0,
    }


def calculate_previous_year_metrics(plant, prev_year_data):
    if prev_year_data.empty:
        return {"total": 0, "total_mwh": 0, "avg_monthly": 0, "avg_monthly_yield": 0}

    total = prev_year_data.sum()
    avg_monthly = prev_year_data.mean()

    return {
        "total_energy": total / 1000,
        "avg_monthly": avg_monthly / 1000,
        "avg_monthly_yield": avg_monthly / plant["power_kwp"] if plant.get("power_kwp", 0) > 0 else 0,
    }


def initialize_year_session_state(year_options):
    current_year = datetime.now().year

    if "yearly_year_selector" not in st.session_state:
        if current_year in year_options:
            st.session_state.yearly_year_selector = current_year
        else:
            st.session_state.yearly_year_selector = year_options[-1]


def render_year_selector(year_options):
    selected_year = st.selectbox(
        "📅 Seleção de Ano:",
        options=year_options,
        key="yearly_year_selector",
    )

    return selected_year


def render_yearly_metrics_cards(yearly_metrics, prev_metrics, plant, cols_cards):
    col2, col3, col4, col5 = cols_cards

    with col2:
        total_delta = (
            yearly_metrics["total_energy"] - prev_metrics["total_energy"] if prev_metrics["total_energy"] > 0 else None
        )
        total_delta_pct = total_delta / prev_metrics["total_energy"] * 100 if total_delta is not None else None

        st.metric(
            "🔋 Energia Total Anual",
            f"{yearly_metrics['total_energy']:.1f} MWh",
            delta=f"{total_delta:+.1f} MWh ({total_delta_pct:+.1f}%)"
            if total_delta is not None and total_delta_pct is not None
            else None,
            help="Energia total gerada no ano",
        )

    with col3:
        delta = (
            yearly_metrics["avg_monthly"] - prev_metrics["avg_monthly"] if prev_metrics["avg_monthly"] > 0 else None
        )
        delta_pct = delta / prev_metrics["avg_monthly"] * 100 if delta is not None else None

        st.metric(
            "📊 Média Mensal",
            f"{yearly_metrics['avg_monthly']:.1f} MWh",
            delta=f"{delta:+.1f} MWh ({delta_pct:+.1f}%)" if delta is not None and delta_pct is not None else None,
            help="Média de energia gerada por mês",
        )

    with col4:
        st.metric(
            "🏆 Melhor Mês",
            f"{yearly_metrics['best_month']:.1f} MWh",
            delta=f"{yearly_metrics['best_month_name']}",
            help="Mês com maior geração de energia",
        )

    with col5:
        if plant.get("power_kwp", 0) > 0:
            delta = (
                yearly_metrics["avg_monthly_yield"] - prev_metrics["avg_monthly_yield"]
                if prev_metrics["avg_monthly_yield"] > 0
                else None
            )
            delta_pct = delta / prev_metrics["avg_monthly_yield"] * 100 if delta is not None else None

            st.metric(
                "⚡ Produtividade Média",
                f"{yearly_metrics['avg_monthly_yield']:.2f} kWh/kWp",
                delta=f"{delta:+.2f} kWh/kWp ({delta_pct:+.2f}%)"
                if delta is not None and delta_pct is not None
                else None,
                help="Produtividade média mensal por kWp instalado (no ano)",
            )
        else:
            st.metric("⚡ Produtividade Média", "N/A")


def create_yearly_chart(yearly_df):
    df_plot = yearly_df.reset_index()
    df_plot["moving_avg"] = df_plot["pv_energy"].rolling(window=3, center=True, min_periods=1).mean()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df_plot["month_name"],
            y=df_plot["pv_energy"],
            name="",
            marker=dict(color="rgba(52, 152, 219, 0.2)", line=dict(color="rgba(52, 152, 219, 0.6)", width=1)),
            hovertemplate="<b>%{x}</b><br><b>%{y:.1f} kWh</b><extra></extra>",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_plot["month_name"],
            y=df_plot["moving_avg"],
            mode="lines",
            name="",
            line=dict(color="#3498db", width=3, shape="spline"),
            hovertemplate="<b>%{x}</b><br><b>Média: %{y:.1f} kWh</b><extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor="rgba(0,0,0,0.1)",
            showticklabels=True,
            tickfont=dict(size=12, color="#2c3e50", family="Inter"),
            title=dict(text="Mês", font=dict(size=14, color="#2c3e50")),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(52, 152, 219, 0.1)",
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor="rgba(0,0,0,0.1)",
            tickfont=dict(size=12, color="#2c3e50", family="Inter"),
            title=dict(text="Energia (kWh)", font=dict(size=14, color="#2c3e50")),
        ),
        plot_bgcolor="rgba(255,255,255,0.8)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(t=30, b=50, l=60, r=30),
        font=dict(family="Inter, Arial", size=12),
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(52, 152, 219, 0.3)",
            font_size=12,
            font_color="#2c3e50",
            font_family="Inter",
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": False})


def render_yearly_detailed_statistics(yearly_df, yearly_metrics, plant):
    col1, _ = st.columns([2, 3])
    with col1:
        with st.expander("📊 Estatísticas Anuais Detalhadas", expanded=False):
            total_months = len(yearly_df[yearly_df["pv_energy"] > 0])
            min_energy = yearly_df["pv_energy"].min() // 1000
            max_energy = yearly_df["pv_energy"].max() // 1000
            std_energy = yearly_df["pv_energy"].std() // 1000
            median_energy = yearly_df["pv_energy"].median() // 1000
            above_avg = (yearly_df["pv_energy"] > yearly_metrics["avg_monthly"]).sum()
            above_pct = (above_avg / 12) * 100

            expected_yearly = plant.get("power_kwp", 1) * 4.5 * 365
            efficiency = (yearly_metrics["total_energy"] / expected_yearly) * 100 if expected_yearly > 0 else 0

            metrics = [
                ("📅 Meses com produção", f"{total_months}", "de 12"),
                ("⬇️ Menor produção mensal", f"{min_energy:.1f}", "MWh"),
                ("⬆️ Maior produção mensal", f"{max_energy:.1f}", "MWh"),
                ("📍 Mediana mensal", f"{median_energy:.1f}", "MWh"),
                ("📊 Desvio padrão", f"{std_energy:.1f}", "MWh"),
                ("📈 Meses acima da média", f"{above_avg}", f"({above_pct:.1f}%)"),
                ("🎯 Eficiência estimada", f"{efficiency:.1f}", "%"),
            ]

            metrics_data = {
                "Métrica": [metric[0] for metric in metrics],
                "Valor": [f"{metric[1]} {metric[2]}" for metric in metrics],
            }

            metrics_df = pd.DataFrame(metrics_data)
            st.dataframe(
                metrics_df,
                width="content",
                hide_index=True,
                column_config={
                    "Métrica": st.column_config.TextColumn("Métrica", width="large"),
                    "Valor": st.column_config.TextColumn("Valor", width="medium"),
                },
            )


def show_yearly_production(plant):
    st.subheader("Produção Anual")
    st.markdown("<br>" * 2, unsafe_allow_html=True)

    df_historical = load_historical_data(plant)
    if df_historical.empty:
        st.info("Nenhum dado histórico encontrado. Verifique se o arquivo CSV existe.")
        return

    min_date = df_historical.index.min().date()
    max_date = df_historical.index.max().date()
    year_options = list(range(min_date.year, max_date.year + 1))

    initialize_year_session_state(year_options)
    selected_year = st.session_state.yearly_year_selector

    yearly_df = create_yearly_dataframe(df_historical, selected_year)
    prev_year_data = calculate_previous_year_data(df_historical, selected_year)

    if not yearly_df.empty:
        col1, col_divider, col2, col3, col4, col5 = st.columns([0.6, 0.3, 1, 1, 1, 1])
        cols_cards = [col2, col3, col4, col5]

        yearly_metrics = calculate_yearly_metrics(plant, yearly_df)
        prev_metrics = calculate_previous_year_metrics(plant, prev_year_data)

        with col1:
            selected_year = render_year_selector(year_options)

        with col_divider:
            render_col_divider()

        render_yearly_metrics_cards(yearly_metrics, prev_metrics, plant, cols_cards)
        create_yearly_chart(yearly_df)
        render_yearly_detailed_statistics(yearly_df, yearly_metrics, plant)

    else:
        st.warning(f"""
        ### Nenhum dado encontrado
        Não há dados disponíveis para **{selected_year}**.
        Verifique se há dados disponíveis para este ano no arquivo CSV.
        """)
