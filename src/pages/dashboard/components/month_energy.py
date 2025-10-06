import calendar
from calendar import monthrange
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly import express as px
from plotly.subplots import make_subplots

from src.config.settings import MONTH_MAPPING
from src.config.styles import ThemeManager, render_col_divider
from src.data.data_loader import load_historical_data
from src.models.physical.params import PVSystemParameters, create_system_parameters
from src.models.physical.run import run_pv_simulation


def initialize_monthly_session_state():
    if "monthly_prediction_cache" not in st.session_state:
        st.session_state.monthly_prediction_cache = {}

    if "monthly_show_predictions" not in st.session_state:
        st.session_state.monthly_show_predictions = {}


def generate_monthly_predictions(plant, year, month):
    cache_key = f"{plant['code']}_monthly_pred_{year}_{month}"

    if cache_key in st.session_state.monthly_prediction_cache:
        return st.session_state.monthly_prediction_cache[cache_key]

    try:
        df_historical = load_historical_data(plant, freq="5min")

        if df_historical.empty:
            st.warning("Dados históricos com radiação não disponíveis para previsão")
            return None

        default_params = PVSystemParameters(capacity_kwp=plant["power_kwp"])

        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, monthrange(year, month)[1])

        if df_historical.index.tz is not None:
            start_datetime = pd.Timestamp(start_date).tz_localize(df_historical.index.tz)
            end_datetime = pd.Timestamp(end_date + timedelta(days=1, seconds=-1)).tz_localize(df_historical.index.tz)
        else:
            start_datetime = pd.Timestamp(start_date)
            end_datetime = pd.Timestamp(end_date + timedelta(days=1, seconds=-1))

        df_month = df_historical.loc[start_datetime:end_datetime].copy()

        if df_month.empty:
            st.warning(f"Dados meteorológicos não disponíveis para {MONTH_MAPPING[month]} de {year}")
            return None

        with st.spinner(f"Gerando previsões NBR 16274 para {MONTH_MAPPING[month]} de {year}..."):
            results = run_pv_simulation(
                df_data=df_month,
                params=default_params,
                apply_dc_losses=True,
                apply_ac_losses=True,
                use_nbr_efficiency=True,
            )

        daily_predictions = (
            results.groupby(results.index.date)
            .agg({
                "ac_power_kw_est": lambda x: x.sum() * (5 / 60)  # Converter para energia diária (kWh)
            })
            .rename(columns={"ac_power_kw_est": "pv_energy_pred"})
        )

        daily_predictions.index = pd.to_datetime(daily_predictions.index)

        st.session_state.monthly_prediction_cache[cache_key] = daily_predictions

        if len(st.session_state.monthly_prediction_cache) > 5:
            oldest_key = min(st.session_state.monthly_prediction_cache.keys())
            del st.session_state.monthly_prediction_cache[oldest_key]

        return daily_predictions

    except Exception as e:
        st.error(f"Erro ao gerar previsões mensais: {str(e)}")
        return None


def calculate_prediction_metrics(prediction_data, monthly_metrics):
    if prediction_data is None or prediction_data.empty:
        return None

    predicted_total = prediction_data["pv_energy_pred"].sum()
    real_total = monthly_metrics["total_energy"]

    predicted_avg = prediction_data["pv_energy_pred"].mean()
    real_avg = monthly_metrics["avg_daily"]

    return {
        "predicted_total": predicted_total,
        "predicted_total_mwh": predicted_total / 1000,
        "predicted_avg": predicted_avg,
        "total_difference": real_total - predicted_total,
        "total_difference_pct": ((real_total - predicted_total) / predicted_total * 100) if predicted_total > 0 else 0,
        "avg_difference": real_avg - predicted_avg,
        "avg_difference_pct": ((real_avg - predicted_avg) / predicted_avg * 100) if predicted_avg > 0 else 0,
    }


def create_full_month_dataframe(df, year, month):
    df_month = df.copy()

    month_mask = (df_month.index.year == year) & (df_month.index.month == month)
    df_month = df_month.loc[month_mask]

    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, monthrange(year, month)[1])

    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    full_month_df = pd.DataFrame(index=date_range, columns=["pv_energy"])
    full_month_df.index.name = df.index.name
    full_month_df["pv_energy"] = 0.0

    full_month_df.update(df_month)
    full_month_df["pv_energy"] = full_month_df["pv_energy"].fillna(0.0)

    return full_month_df


def calculate_previous_month_data(df_historical, monthly_df):
    prev_month_start = (monthly_df.index.min().replace(day=1) - pd.Timedelta(days=1)).replace(day=1)
    prev_month_end = monthly_df.index.min().replace(day=1) - pd.Timedelta(days=1)
    prev_month_mask = (df_historical.index >= prev_month_start) & (df_historical.index <= prev_month_end)
    return df_historical.loc[prev_month_mask]


def calculate_monthly_metrics(plant, monthly_df):
    return {
        "total_energy": monthly_df["pv_energy"].sum(),
        "total_energy_mwh": monthly_df["pv_energy"].sum() / 1000,
        "avg_daily": monthly_df["pv_energy"].mean(),
        "best_day": monthly_df["pv_energy"].max(),
        "avg_daily_yield": monthly_df["pv_energy"].mean() / plant["power_kwp"],
        "best_day_date": monthly_df[monthly_df["pv_energy"] == monthly_df["pv_energy"].max()]
        .index[0]
        .strftime("%d/%m"),
    }


def calculate_previous_month_metrics(plant, prev_month_df):
    if prev_month_df.empty:
        return {"total": 0, "total_mwh": 0, "avg_daily": 0, "avg_daily_yield": 0}

    return {
        "total": prev_month_df["pv_energy"].sum(),
        "total_mwh": prev_month_df["pv_energy"].sum() / 1000,
        "avg_daily": prev_month_df["pv_energy"].mean(),
        "avg_daily_yield": prev_month_df["pv_energy"].mean() / plant["power_kwp"],
    }


def initialize_session_state(year_options):
    current_date = datetime.now()

    if "year_selector" not in st.session_state:
        st.session_state.year_selector = year_options[-1]

    if "month_selector" not in st.session_state:
        st.session_state.month_selector = current_date.month


def render_date_selector(year_options):
    """Renderiza seletores de data"""
    selected_year = st.selectbox(
        "📅 Seleção de Período:",
        options=year_options,
        key="year_selector",
    )

    selected_month = st.selectbox(
        "Selecione o mês:",
        options=list(MONTH_MAPPING.keys()),
        format_func=lambda x: MONTH_MAPPING[x],
        key="month_selector",
        label_visibility="collapsed",
    )

    return selected_year, selected_month


def render_metrics_cards_with_prediction(monthly_metrics, prev_metrics, prediction_metrics, plant, cols_cards):
    col2, col3, col4, col5 = cols_cards

    with col2:
        total_delta = (
            monthly_metrics["total_energy_mwh"] - prev_metrics["total_mwh"] if prev_metrics["total"] > 0 else None
        )
        total_delta_pct = total_delta / prev_metrics["total_mwh"] * 100 if total_delta is not None else None

        # Mostrar comparação com previsão se disponível
        prediction_info = ""
        if prediction_metrics:
            pred_diff = prediction_metrics["total_difference_pct"]
            prediction_info = f"\n🔮 vs NBR: {pred_diff:+.1f}%"

        st.metric(
            "🔋 Energia Total",
            f"{monthly_metrics['total_energy_mwh']:.1f} MWh",
            delta=f"{total_delta:+.1f} MWh ({total_delta_pct:+.1f}%){prediction_info}"
            if total_delta is not None and total_delta_pct is not None
            else prediction_info
            if prediction_info
            else None,
            help="Energia total gerada no período",
        )

    with col3:
        delta = monthly_metrics["avg_daily"] - prev_metrics["avg_daily"] if prev_metrics["avg_daily"] > 0 else None
        delta_pct = delta / prev_metrics["avg_daily"] * 100 if delta is not None else None

        # Mostrar comparação com previsão se disponível
        prediction_info = ""
        if prediction_metrics:
            pred_diff = prediction_metrics["avg_difference_pct"]
            prediction_info = f"\n🔮 vs NBR: {pred_diff:+.1f}%"

        st.metric(
            "📊 Média Diária",
            f"{monthly_metrics['avg_daily']:.1f} kWh",
            delta=f"{delta:+.1f} kWh  ({delta_pct:+.1f}%){prediction_info}"
            if delta is not None and delta_pct is not None
            else prediction_info
            if prediction_info
            else None,
            help="Média de energia gerada por dia",
        )

    with col4:
        st.metric(
            "🏆 Melhor Dia",
            f"{monthly_metrics['best_day']:.1f} kWh",
            delta=f"Dia {monthly_metrics['best_day_date']}",
            help="Dia com maior geração de energia",
        )

    with col5:
        if plant.get("power_kwp", 0) > 0:
            delta = (
                monthly_metrics["avg_daily_yield"] - prev_metrics["avg_daily_yield"]
                if prev_metrics["avg_daily_yield"] > 0
                else None
            )
            delta_pct = delta / prev_metrics["avg_daily_yield"] * 100 if delta is not None else None

            st.metric(
                "⚡ Produtividade",
                f"{monthly_metrics['avg_daily_yield']:.2f} kWh/kWp",
                delta=f"{delta:+.2f} kWh/kWp ({delta_pct:+.2f}%)"
                if delta is not None and delta_pct is not None
                else None,
                help="Produtividade média por kWp instalado",
            )
        else:
            st.metric("⚡ Produtividade", "N/A")


def render_prediction_controls(year, month):
    period_key = f"{year}_{month}"

    col_space, col_btn = st.columns([8, 2])
    with col_btn:
        show_prediction = st.session_state.monthly_show_predictions.get(period_key, False)

        if not show_prediction:
            if st.button("🔮 Gerar Previsões"):
                st.session_state.monthly_show_predictions[period_key] = True
                st.rerun()
        else:
            if st.button("❌ Remover Previsões"):
                st.session_state.monthly_show_predictions[period_key] = False
                st.rerun()

    return st.session_state.monthly_show_predictions.get(period_key, False)


def create_monthly_chart_with_prediction(monthly_df, prediction_data=None, show_prediction=False):
    df_plot = monthly_df.reset_index()
    df_plot["day"] = df_plot["date_time"].dt.day
    df_plot["moving_avg"] = df_plot["pv_energy"].rolling(window=3, center=True, min_periods=1).mean()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df_plot["day"],
            y=df_plot["pv_energy"],
            name="Real",
            marker=dict(color="rgba(52, 152, 219, 0.2)", line=dict(color="rgba(52, 152, 219, 0.6)", width=1)),
            hovertemplate="<b>Dia %{x}</b><br><b>Real: %{y:.1f} kWh</b><extra></extra>",
        )
    )

    if show_prediction and prediction_data is not None and not prediction_data.empty:
        pred_plot = prediction_data.reset_index()
        pred_plot["day"] = pred_plot["index"].dt.day

        fig.add_trace(
            go.Bar(
                x=pred_plot["day"],
                y=pred_plot["pv_energy_pred"],
                name="NBR 16274",
                marker=dict(color="rgba(255, 152, 0, 0.3)", line=dict(color="rgba(255, 152, 0, 0.8)", width=1)),
                hovertemplate="<b>Dia %{x}</b><br><b>NBR 16274: %{y:.1f} kWh</b><extra></extra>",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=df_plot["day"],
            y=df_plot["moving_avg"],
            mode="lines",
            name="Média Móvel",
            line=dict(color="#3498db", width=3, shape="spline"),
            hovertemplate="<b>Dia %{x}</b><br><b>Média: %{y:.1f} kWh</b><extra></extra>",
        )
    )

    fig.update_layout(
        title="Produção Diária Mensal" + (" vs NBR 16274" if show_prediction else ""),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor="rgba(0,0,0,0.1)",
            showticklabels=True,
            dtick=2,
            tickfont=dict(size=12, color="#2c3e50", family="Inter"),
            title=dict(text="Dia do Mês", font=dict(size=14, color="#2c3e50")),
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
        margin=dict(t=60, b=50, l=60, r=30),
        font=dict(family="Inter, Arial", size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(52, 152, 219, 0.3)",
            font_size=12,
            font_color="#2c3e50",
            font_family="Inter",
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "staticPlot": False})


def render_detailed_statistics_with_prediction(monthly_df, monthly_metrics, plant, prediction_metrics=None):
    col1, col2 = st.columns([2, 2])

    with col1:
        with st.expander("📊 Estatísticas Detalhadas", expanded=False):
            total_days = len(monthly_df)
            min_energy = monthly_df["pv_energy"].min()
            max_energy = monthly_df["pv_energy"].max()
            std_energy = monthly_df["pv_energy"].std()
            median_energy = monthly_df["pv_energy"].median()
            above_avg = (monthly_df["pv_energy"] > monthly_metrics["avg_daily"]).sum()
            above_pct = (above_avg / total_days) * 100
            expected_monthly = plant.get("power_kwp", 1) * 4.5 * total_days
            efficiency = (monthly_metrics["total_energy"] / expected_monthly) * 100 if expected_monthly > 0 else 0

            metrics = [
                ("📅 Total de dias", f"{total_days}", ""),
                ("⬇️ Energia mínima", f"{min_energy:.1f}", "kWh"),
                ("⬆️ Energia máxima", f"{max_energy:.1f}", "kWh"),
                ("📍 Mediana", f"{median_energy:.1f}", "kWh"),
                ("📊 Desvio padrão", f"{std_energy:.1f}", "kWh"),
                ("📈 Dias acima da média", f"{above_avg}", f"({above_pct:.1f}%)"),
                ("🎯 Eficiência", f"{efficiency:.1f}", "%"),
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

    with col2:
        if prediction_metrics:
            with st.expander("🔮 Comparação NBR 16274", expanded=False):
                pred_metrics = [
                    ("🔋 Total Previsto", f"{prediction_metrics['predicted_total_mwh']:.1f}", "MWh"),
                    ("📊 Média Prevista", f"{prediction_metrics['predicted_avg']:.1f}", "kWh/dia"),
                    ("📈 Diferença Total", f"{prediction_metrics['total_difference']:.1f}", "kWh"),
                    ("📊 Diferença %", f"{prediction_metrics['total_difference_pct']:+.1f}", "%"),
                    ("📉 Diferença Média", f"{prediction_metrics['avg_difference']:.1f}", "kWh/dia"),
                    ("📊 Diferença Média %", f"{prediction_metrics['avg_difference_pct']:+.1f}", "%"),
                ]

                pred_data = {
                    "Métrica": [metric[0] for metric in pred_metrics],
                    "Valor": [f"{metric[1]} {metric[2]}" for metric in pred_metrics],
                }

                pred_df = pd.DataFrame(pred_data)
                st.dataframe(
                    pred_df,
                    width="content",
                    hide_index=True,
                    column_config={
                        "Métrica": st.column_config.TextColumn("Métrica", width="large"),
                        "Valor": st.column_config.TextColumn("Valor", width="medium"),
                    },
                )


def show_monthly_production(plant):
    st.subheader("Produção Mensal")
    st.markdown("<br>" * 2, unsafe_allow_html=True)

    initialize_monthly_session_state()
    df_historical = load_historical_data(plant)
    if df_historical.empty:
        st.info("Nenhum dado histórico encontrado. Verifique se o arquivo CSV existe.")
        return

    min_date = df_historical.index.min().date()
    max_date = df_historical.index.max().date()
    year_options = list(range(min_date.year, max_date.year + 1))

    initialize_session_state(year_options)
    selected_year = st.session_state.year_selector
    selected_month = st.session_state.month_selector

    monthly_df = create_full_month_dataframe(df_historical, selected_year, selected_month)
    prev_month_df = calculate_previous_month_data(df_historical, monthly_df)

    if not monthly_df.empty:
        col1, col_divider, col2, col3, col4, col5 = st.columns([0.6, 0.3, 1, 1, 1, 1])
        cols_cards = [col2, col3, col4, col5]

        monthly_metrics = calculate_monthly_metrics(plant, monthly_df)
        prev_metrics = calculate_previous_month_metrics(plant, prev_month_df)

        with col1:
            selected_year, selected_month = render_date_selector(year_options)

        with col_divider:
            render_col_divider()

        show_prediction = render_prediction_controls(selected_year, selected_month)

        prediction_data = None
        prediction_metrics = None

        if show_prediction:
            prediction_data = generate_monthly_predictions(plant, selected_year, selected_month)
            if prediction_data is not None:
                prediction_metrics = calculate_prediction_metrics(prediction_data, monthly_metrics)

        render_metrics_cards_with_prediction(monthly_metrics, prev_metrics, prediction_metrics, plant, cols_cards)
        create_monthly_chart_with_prediction(monthly_df, prediction_data, show_prediction)
        render_detailed_statistics_with_prediction(monthly_df, monthly_metrics, plant, prediction_metrics)

    else:
        st.warning(f"""
        ### Nenhum dado encontrado
        Não há dados disponíveis para **{MONTH_MAPPING[selected_month]} de {selected_year}**.
        Verifique se há dados disponíveis para este período no arquivo CSV.
        """)


def clear_monthly_prediction_cache():
    """Limpa cache de previsões mensais"""
    if "monthly_prediction_cache" in st.session_state:
        st.session_state.monthly_prediction_cache.clear()
    if "monthly_show_predictions" in st.session_state:
        st.session_state.monthly_show_predictions.clear()
    st.success("Cache de previsões mensais limpo com sucesso!")


def show_monthly_prediction_cache_info():
    cache = st.session_state.get("monthly_prediction_cache", {})
    active_predictions = st.session_state.get("monthly_show_predictions", {})

    cache_size = len(cache)
    active_size = sum(bool(v) for v in active_predictions.values())

    st.info(f"🔮 Cache previsões mensais: {cache_size} período(s)")
    st.info(f"📊 Previsões ativas: {active_size} período(s)")

    if cache_size > 0 and st.button("🗑️ Limpar Cache Previsões"):
        clear_monthly_prediction_cache()
