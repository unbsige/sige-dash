import json
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config.styles import render_col_divider
from src.data.data_loader import get_daily_data, load_historical_data
from src.models.physical.params import PVSystemParameters
from src.models.physical.run import run_pv_simulation


def initialize_daily_session_state():
    if "daily_cache" not in st.session_state:
        st.session_state.daily_cache = {}

    if "daily_selected_date" not in st.session_state:
        st.session_state.daily_selected_date = datetime.now().date()

    if "daily_prediction_cache" not in st.session_state:
        st.session_state.daily_prediction_cache = {}


def load_daily_data_with_cache(plant, selected_date):
    plant_key = plant["code"]
    device_id = plant["device"]["id"]
    date_str = selected_date.strftime("%Y-%m-%d")

    cache_key = f"{plant_key}_{device_id}_{date_str}"
    if cache_key in st.session_state.daily_cache:
        return st.session_state.daily_cache[cache_key]

    with st.spinner(f"Carregando dados de {selected_date.strftime('%d/%m/%Y')}..."):
        try:
            daily_data = get_daily_data(plant, selected_date)

            if daily_data and not daily_data["power"].empty:
                st.session_state.daily_cache[cache_key] = daily_data

                if len(st.session_state.daily_cache) > 30:
                    oldest_key = min(st.session_state.daily_cache.keys())
                    del st.session_state.daily_cache[oldest_key]

            return daily_data

        except Exception as e:
            st.error(f"Erro ao carregar dados: {str(e)}")
            return None


def generate_daily_prediction(plant, selected_date):
    """Gera previsão NBR 16274 para o dia selecionado"""

    date_str = selected_date.strftime("%Y-%m-%d")
    pred_cache_key = f"{plant['code']}_pred_{date_str}"

    if pred_cache_key in st.session_state.daily_prediction_cache:
        return st.session_state.daily_prediction_cache[pred_cache_key]

    try:
        df_historical = load_historical_data(plant, freq="5min")
        if df_historical.empty:
            st.warning("Dados históricos com radiação não disponíveis para previsão")
            return None

        if df_historical.index.tz is not None:
            start_datetime = pd.Timestamp(selected_date).tz_localize(df_historical.index.tz)
            end_datetime = start_datetime + pd.Timedelta(days=1, seconds=-1)
        else:
            start_datetime = pd.Timestamp(selected_date)
            end_datetime = start_datetime + pd.Timedelta(days=1, seconds=-1)

        df_day = df_historical.loc[start_datetime:end_datetime].copy()
        # pred_data = df_day[["ac_power_kw_est"]].copy()
        # pred_data = pred_data.rename(columns={"ac_power_kw_est": "pv_power_pred"})
        # st.session_state.daily_prediction_cache[pred_cache_key] = pred_data
        # return pred_data

        if df_day.empty:
            st.warning(f"Dados meteorológicos não disponíveis para {selected_date.strftime('%d/%m/%Y')}")
            return None

        default_params = PVSystemParameters(capacity_kwp=plant["power_kwp"])

        with st.spinner("Gerando previsão NBR 16274..."):
            results = run_pv_simulation(
                df_data=df_day,
                params=default_params,
                apply_dc_losses=True,
                apply_ac_losses=True,
                use_nbr_efficiency=True,
            )

        prediction_data = results[["ac_power_kw_est"]].copy()
        prediction_data = prediction_data.rename(columns={"ac_power_kw_est": "pv_power_pred"})

        st.session_state.daily_prediction_cache[pred_cache_key] = prediction_data

        if len(st.session_state.daily_prediction_cache) > 10:
            oldest_key = min(st.session_state.daily_prediction_cache.keys())
            del st.session_state.daily_prediction_cache[oldest_key]

        return prediction_data

    except Exception as e:
        st.error(f"Erro ao gerar previsão: {str(e)}")
        return None


def calculate_daily_metrics(plant, df_power, df_energy):
    if df_power.empty:
        return {
            "daily_energy": 0,
            "max_power": 0,
            "full_power_hours": 0,
            "daily_yield": 0,
            "avg_power": 0,
            "peak_time": "N/A",
            "capacity_factor": 0,
        }

    daily_energy = df_power["pv_power"].sum() * (5 / 60)
    max_power = df_power["pv_power"].max()
    avg_power = df_power["pv_power"].mean()

    if not df_energy.empty and "full_power_hours" in df_energy.columns:
        full_power_hours = df_energy["full_power_hours"].iloc[0] if len(df_energy) > 0 else 0
    else:
        full_power_hours = daily_energy / plant.get("power_kwp", 1) if plant.get("power_kwp", 0) > 0 else 0

    daily_yield = daily_energy / plant["power_kwp"] if plant.get("power_kwp", 0) > 0 else 0
    peak_time = "N/A" if df_power.empty else df_power.idxmax()["pv_power"].strftime("%H:%M")
    capacity_factor = (max_power / plant["power_kwp"]) * 100 if plant.get("power_kwp", 0) > 0 else 0

    return {
        "daily_energy": daily_energy,
        "max_power": max_power,
        "full_power_hours": full_power_hours,
        "daily_yield": daily_yield,
        "avg_power": avg_power,
        "peak_time": peak_time,
        "capacity_factor": capacity_factor,
    }


def calculate_previous_day_metrics(plant, selected_date):
    prev_date = selected_date - timedelta(days=1)
    prev_data = load_daily_data_with_cache(plant, prev_date)

    if not prev_data or prev_data["power"].empty:
        return {"daily_energy": 0, "max_power": 0, "full_power_hours": 0, "daily_yield": 0}

    return calculate_daily_metrics(plant, prev_data["power"], prev_data["energy"])


def render_date_navigation(selected_date, plant_key=None, device_id=None):
    col_prev, col_date, col_next = st.columns([0.5, 2, 0.5])

    with col_prev:
        st.markdown('<div style="margin-top: 23px;">', unsafe_allow_html=True)
        if st.button("◀", key="prev_day", help="Dia anterior", type="primary"):
            st.session_state.daily_selected_date = selected_date - timedelta(days=1)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_date:
        new_date = st.date_input(
            "📅 Data de análise:",
            value=selected_date,
            max_value=datetime.now().date(),
            key="daily_date_selector",
        )
        if new_date != selected_date:
            st.session_state.daily_selected_date = new_date
            st.rerun()

        render_cache_status(plant_key, device_id, selected_date)

    with col_next:
        st.markdown('<div style="margin-top: 23px;">', unsafe_allow_html=True)
        if st.button("▶", key="next_day", help="Próximo dia", type="primary"):
            if selected_date < datetime.now().date():
                st.session_state.daily_selected_date = selected_date + timedelta(days=1)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    return st.session_state.daily_selected_date


def render_cache_status(plant_key, device_id, selected_date):
    selected_date_str = selected_date.strftime("%Y-%m-%d")
    cache_key = f"{plant_key}_{device_id}_{selected_date_str}"

    if cache_key in st.session_state.daily_cache:
        st.badge("Cached", color="green")
    else:
        st.badge("Loading...", color="orange")


def render_daily_metrics_cards(daily_metrics, prev_metrics, cols_cards):
    col2, col3, col4, col5 = cols_cards

    with col2:
        energy_delta = (
            daily_metrics["daily_energy"] - prev_metrics["daily_energy"] if prev_metrics["daily_energy"] > 0 else None
        )
        energy_delta_pct = energy_delta / prev_metrics["daily_energy"] * 100 if energy_delta is not None else None

        st.metric(
            "🔋 Energia Gerada",
            f"{daily_metrics['daily_energy']:.1f} kWh",
            delta=f"{energy_delta:+.1f} kWh ({energy_delta_pct:+.1f}%)"
            if energy_delta is not None and energy_delta_pct is not None
            else None,
            help="Energia total gerada no dia",
        )

    with col3:
        power_delta = daily_metrics["max_power"] - prev_metrics["max_power"] if prev_metrics["max_power"] > 0 else None
        power_delta_pct = power_delta / prev_metrics["max_power"] * 100 if power_delta is not None else None

        st.metric(
            "⚡ Potência Máxima",
            f"{daily_metrics['max_power']:.1f} kW",
            delta=f"{power_delta:+.1f} kW ({power_delta_pct:+.1f}%)"
            if power_delta is not None and power_delta_pct is not None
            else None,
            help="Pico de potência registrado",
        )

    with col4:
        st.metric(
            "☀️ Horas Sol Pleno",
            f"{daily_metrics['full_power_hours']:.1f}h",
            delta=f"Pico às {daily_metrics['peak_time']}",
            help="Horas equivalentes de sol pleno",
        )

    with col5:
        yield_delta = (
            daily_metrics["daily_yield"] - prev_metrics["daily_yield"] if prev_metrics["daily_yield"] > 0 else None
        )
        yield_delta_pct = yield_delta / prev_metrics["daily_yield"] * 100 if yield_delta is not None else None

        st.metric(
            "📊 Produtividade",
            f"{daily_metrics['daily_yield']:.2f} kWh/kWp",
            delta=f"{yield_delta:+.2f} kWh/kWp ({yield_delta_pct:+.1f}%)"
            if yield_delta is not None and yield_delta_pct is not None
            else None,
            help="Produtividade específica do sistema",
        )


def create_daily_power_chart(plant, df_power, selected_date, prediction_data=None, show_prediction=False):
    if df_power.empty:
        st.warning("Nenhum dado de potência disponível para plotagem.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_power.index,
            y=df_power["pv_power"],
            mode="lines",
            name="Real",
            line=dict(color="#2196F3", width=3, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(33, 150, 243, 0.15)",
            hovertemplate="<b>%{x|%H:%M}</b><br><b>Real: %{y:.1f} kW</b><extra></extra>",
        )
    )

    if show_prediction and prediction_data is not None and not prediction_data.empty:
        fig.add_trace(
            go.Scatter(
                x=prediction_data.index,
                y=prediction_data["pv_power_pred"],
                mode="lines",
                name="NBR 16274",
                line=dict(color="#FF9800", width=2, dash="dot"),
                hovertemplate="<b>%{x|%H:%M}</b><br><b>NBR 16274: %{y:.1f} kW</b><extra></extra>",
            )
        )

    if plant.get("power_kwp", 0) > 0:
        fig.add_hline(
            y=plant["power_kwp"],
            line_dash="dash",
            line_color="rgba(231, 76, 60, 0.7)",
            annotation_text=f"Capacidade: {plant['power_kwp']} kW",
            annotation_position="top right",
        )

    selected_date_str = selected_date.strftime("%Y-%m-%d")
    start_time = f"{selected_date_str} 05:00:00"
    end_time = f"{selected_date_str} 19:00:00"

    max_power = df_power["pv_power"].max()
    if show_prediction and prediction_data is not None:
        max_power = max(max_power, prediction_data["pv_power_pred"].max())

    y_max = max(max_power * 1.15, plant.get("power_kwp", 0) * 1.1) if max_power > 0 else 10

    fig.update_layout(
        title=f"Curva de Potência - {selected_date.strftime('%d/%m/%Y')}",
        xaxis=dict(
            title="Horário",
            range=[start_time, end_time],
            dtick=3600000,
            tickformat="%H:%M",
            showgrid=True,
            gridcolor="rgba(52, 152, 219, 0.1)",
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor="rgba(0,0,0,0.1)",
            tickfont=dict(size=12, color="#2c3e50", family="Inter"),
        ),
        yaxis=dict(
            title="Potência (kW)",
            range=[0, y_max],
            showgrid=True,
            gridcolor="rgba(52, 152, 219, 0.1)",
            gridwidth=1,
            zeroline=False,
            showline=True,
            linecolor="rgba(0,0,0,0.1)",
            tickfont=dict(size=12, color="#2c3e50", family="Inter"),
        ),
        plot_bgcolor="rgba(255,255,255,0.8)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=450,
        margin=dict(t=60, b=50, l=60, r=40),
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


def render_prediction_controls(plant, selected_date):
    _, col_btn = st.columns([6, 1])
    with col_btn:
        show_prediction = st.session_state.get(f"show_prediction_{selected_date}", False)
        if not show_prediction:
            if st.button("🔮 Gerar Previsão"):
                prediction_data = generate_daily_prediction(plant, selected_date)
                if prediction_data is not None:
                    st.session_state[f"show_prediction_{selected_date}"] = True
                    st.rerun()
        else:
            if st.button("❌ Remover Previsão"):
                st.session_state[f"show_prediction_{selected_date}"] = False
                st.rerun()
    return st.session_state.get(f"show_prediction_{selected_date}", False)


def render_daily_detailed_statistics(df_power, daily_metrics, plant):
    col1, _ = st.columns([2, 3])
    with col1:
        with st.expander("📊 Análise Detalhada do Dia", expanded=False):
            if not df_power.empty:
                total_measurements = len(df_power)
                active_measurements = (df_power["pv_power"] > 0).sum()

                morning_data = df_power.between_time("06:00", "12:00")
                afternoon_data = df_power.between_time("12:00", "18:00")

                morning_avg = 0 if morning_data.empty else morning_data["pv_power"].mean()
                afternoon_avg = 0 if afternoon_data.empty else afternoon_data["pv_power"].mean()

                if daily_metrics["capacity_factor"] >= 90:
                    day_rating = "🌟 Excelente"
                elif daily_metrics["capacity_factor"] >= 70:
                    day_rating = "✅ Bom"
                elif daily_metrics["capacity_factor"] >= 50:
                    day_rating = "⚠️ Regular"
                else:
                    day_rating = "❌ Baixo"

                metrics = [
                    ("📊 Total de medições", f"{total_measurements}", ""),
                    (
                        "🌞 Medições ativas",
                        f"{active_measurements}",
                        f"({active_measurements / total_measurements * 100:.1f}%)",
                    ),
                    ("🏆 Horário do pico", daily_metrics["peak_time"], ""),
                    ("📈 Potência média", f"{daily_metrics['avg_power']:.1f}", "kW"),
                    ("📊 Desvio padrão", f"{df_power['pv_power'].std():.1f}", "kW"),
                    ("🌅 Média manhã", f"{morning_avg:.1f}", "kW"),
                    ("🌇 Média tarde", f"{afternoon_avg:.1f}", "kW"),
                    ("🔋 Fator de capacidade", f"{daily_metrics['capacity_factor']:.1f}", "%"),
                    ("📊 Classificação", day_rating, ""),
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


def show_daily_production(plant):
    st.subheader("Produção Diária (Curva de Potência)")
    st.markdown("<br>" * 2, unsafe_allow_html=True)

    initialize_daily_session_state()

    col1, col_divider, col2, col3, col4, col5 = st.columns([1.2, 0.2, 1, 1, 1, 1])
    cols_cards = [col2, col3, col4, col5]

    plant_key = plant["code"]
    device_id = plant["device"]["id"]

    with col1:
        selected_date = render_date_navigation(st.session_state.daily_selected_date, plant_key, device_id)

    with col_divider:
        render_col_divider()

    daily_data = load_daily_data_with_cache(plant, selected_date)
    if daily_data and not daily_data["power"].empty:
        df_power = daily_data["power"]
        df_energy = daily_data["energy"]

        daily_metrics = calculate_daily_metrics(plant, df_power, df_energy)
        prev_metrics = calculate_previous_day_metrics(plant, selected_date)

        prediction_data = None
        show_prediction = st.session_state.get(f"show_prediction_{selected_date}", False)
        if show_prediction:
            pred_cache_key = f"{plant['code']}_pred_{selected_date.strftime('%Y-%m-%d')}"
            prediction_data = st.session_state.daily_prediction_cache.get(pred_cache_key)

        create_daily_power_chart(plant, df_power, selected_date, prediction_data, show_prediction)

        render_daily_metrics_cards(daily_metrics, prev_metrics, cols_cards)
        show_prediction = render_prediction_controls(plant, selected_date)

        if show_prediction:
            pred_cache_key = f"{plant_key}_pred_{selected_date.strftime('%Y-%m-%d')}"
            prediction_data = st.session_state.daily_prediction_cache.get(pred_cache_key)

        render_daily_detailed_statistics(df_power, daily_metrics, plant)

    else:
        st.warning(f"""
        ### 📭 Nenhum dado encontrado
        
        Não há dados de potência disponíveis para **{selected_date.strftime("%d/%m/%Y")}**.
        
        Possíveis motivos:
        - Sistema desligado no dia
        - Problemas de comunicação
        - Manutenção programada
        """)


def clear_daily_cache():
    if "daily_cache" in st.session_state:
        st.session_state.daily_cache.clear()
    if "daily_prediction_cache" in st.session_state:
        st.session_state.daily_prediction_cache.clear()
    st.success("Cache diário e de previsões limpo com sucesso!")


def show_cache_info():
    cache = st.session_state.get("daily_cache", {})
    pred_cache = st.session_state.get("daily_prediction_cache", {})

    cache_size = len(cache)
    pred_size = len(pred_cache)

    st.info(f"📦 Cache diário: {cache_size} dia(s)")
    st.info(f"🔮 Cache previsões: {pred_size} dia(s)")

    if (cache_size + pred_size) > 0 and st.button("🗑️ Limpar Cache"):
        clear_daily_cache()


#
