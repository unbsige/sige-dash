import time
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config.styles import render_col_divider
from src.data.data_loader import get_daily_data

# from src.data.data_loader import get_available_plants, get_daily_data

warnings.filterwarnings("ignore")


def initialize_realtime_session_state():
    if "rt_last_update" not in st.session_state:
        st.session_state.rt_last_update = None

    if "rt_auto_refresh" not in st.session_state:
        st.session_state.rt_auto_refresh = False

    if "rt_selected_date" not in st.session_state:
        st.session_state.rt_selected_date = datetime.now().date()


# def load_realtime_data_all_plants(selected_date):
#     available_plants = get_available_plants()
#     all_plants_data = {}

#     with st.spinner("Atualizando dados de todas as plantas..."):
#         for plant_key, plant_config in available_plants.items():
#             device_id = plant_config["device"]["device_id"]

#             try:
#                 daily_data = get_daily_data(plant_key, device_id, selected_date)

#                 if daily_data and not daily_data["power"].empty:
#                     all_plants_data[plant_key] = {
#                         "config": plant_config,
#                         "power_data": daily_data["power"],
#                         "energy_data": daily_data["energy"],
#                         "status": "online",
#                         "device_id": device_id,
#                     }
#                 else:
#                     all_plants_data[plant_key] = {
#                         "config": plant_config,
#                         "power_data": pd.DataFrame(),
#                         "energy_data": pd.DataFrame(),
#                         "status": "offline",
#                         "device_id": device_id,
#                     }
#             except Exception:
#                 all_plants_data[plant_key] = {
#                     "config": plant_config,
#                     "power_data": pd.DataFrame(),
#                     "energy_data": pd.DataFrame(),
#                     "status": "error",
#                     "device_id": device_id,
#                 }

#     st.session_state.rt_last_update = datetime.now()
#     return all_plants_data


def calculate_plant_metrics_today(power_data, energy_data, capacity_kwp):
    if power_data.empty:
        return {
            "current_power": 0,
            "energy_today": 0,
            "peak_power": 0,
            "capacity_factor": 0,
            "performance_ratio": 0,
            "peak_time": "N/A",
            "avg_power": 0,
        }

    current_power = power_data["pv_power"].iloc[-1] if len(power_data) > 0 else 0
    energy_today = power_data["pv_power"].sum() * (5 / 60)  # kWh (5min intervals)
    peak_power = power_data["pv_power"].max()
    avg_power = power_data["pv_power"].mean()
    peak_time = power_data.idxmax()["pv_power"].strftime("%H:%M") if len(power_data) > 0 else "N/A"

    capacity_factor = (current_power / capacity_kwp * 100) if capacity_kwp > 0 else 0
    performance_ratio = (peak_power / capacity_kwp * 100) if capacity_kwp > 0 else 0

    return {
        "current_power": current_power,
        "energy_today": energy_today,
        "peak_power": peak_power,
        "capacity_factor": capacity_factor,
        "performance_ratio": performance_ratio,
        "peak_time": peak_time,
        "avg_power": avg_power,
    }


def render_header():
    current_time = datetime.now().strftime("%H:%M:%S")

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
            padding: 20px 25px;
            border-radius: 8px;
            margin-bottom: 30px;
            color: white;
            box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 style="margin: 0; font-size: 1.8rem; font-weight: 500;">MEPA Monitoramento - Dashboard Plantas</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 1rem;">Monitoramento comparativo do sistema solar</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.1rem; font-weight: 500;">{current_time}</div>
                    <div style="opacity: 0.9; font-size: 0.85rem;">Sistema conectado</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# def render_system_overview_cards(all_plants_data, cols_cards):
#     total_current = 0
#     total_capacity = 0
#     total_energy_today = 0
#     plants_online = 0

#     for plant_key, data in all_plants_data.items():
#         capacity = data["config"]["capacity_kwp"]
#         total_capacity += capacity

#         if data["status"] == "online" and not data["power_data"].empty:
#             plants_online += 1
#             power_data = data["power_data"]
#             current_power = power_data["pv_power"].iloc[-1] if len(power_data) > 0 else 0
#             energy_today = power_data["pv_power"].sum() * (5 / 60)

#             total_current += current_power
#             total_energy_today += energy_today

#     col1, col2, col3, col4 = cols_cards

#     with col1:
#         st.markdown(
#             f"""
#             <div style="
#                 background: white;
#                 border: 1px solid #E0E0E0;
#                 border-left: 4px solid #2196F3;
#                 border-radius: 8px;
#                 padding: 20px;
#                 text-align: center;
#                 box-shadow: 0 1px 3px rgba(0,0,0,0.1);
#                 margin: 10px 0;
#             ">
#                 <div style="color: #2196F3; font-size: 1.5rem; margin-bottom: 8px;">⚡</div>
#                 <div style="color: #1976D2; font-size: 1.6rem; font-weight: 600;">{total_current:.1f}</div>
#                 <div style="color: #666; font-size: 0.9rem; margin: 4px 0;">kW Sistema</div>
#                 <div style="color: #999; font-size: 0.8rem;">
#                     {(total_current / total_capacity * 100) if total_capacity > 0 else 0:.1f}% capacidade
#                 </div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )

#     with col2:
#         st.markdown(
#             f"""
#             <div style="
#                 background: white;
#                 border: 1px solid #E0E0E0;
#                 border-left: 4px solid #4CAF50;
#                 border-radius: 8px;
#                 padding: 20px;
#                 text-align: center;
#                 box-shadow: 0 1px 3px rgba(0,0,0,0.1);
#                 margin: 10px 0;
#             ">
#                 <div style="color: #4CAF50; font-size: 1.5rem; margin-bottom: 8px;">🔋</div>
#                 <div style="color: #388E3C; font-size: 1.6rem; font-weight: 600;">{total_energy_today:.1f}</div>
#                 <div style="color: #666; font-size: 0.9rem; margin: 4px 0;">kWh Hoje</div>
#                 <div style="color: #999; font-size: 0.8rem;">
#                     Energia total gerada
#                 </div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )

#     with col3:
#         total_plants = len(all_plants_data)
#         online_percent = (plants_online / total_plants * 100) if total_plants > 0 else 0
#         status_color = "#4CAF50" if online_percent >= 80 else "#FF9800"

#         st.markdown(
#             f"""
#             <div style="
#                 background: white;
#                 border: 1px solid #E0E0E0;
#                 border-left: 4px solid {status_color};
#                 border-radius: 8px;
#                 padding: 20px;
#                 text-align: center;
#                 box-shadow: 0 1px 3px rgba(0,0,0,0.1);
#                 margin: 10px 0;
#             ">
#                 <div style="color: {status_color}; font-size: 1.5rem; margin-bottom: 8px;">🏭</div>
#                 <div style="color: #333; font-size: 1.6rem; font-weight: 600;">{plants_online}/{total_plants}</div>
#                 <div style="color: #666; font-size: 0.9rem; margin: 4px 0;">Plantas Online</div>
#                 <div style="color: #999; font-size: 0.8rem;">
#                     {online_percent:.0f}% operacional
#                 </div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )

#     with col4:
#         st.markdown(
#             f"""
#             <div style="
#                 background: white;
#                 border: 1px solid #E0E0E0;
#                 border-left: 4px solid #607D8B;
#                 border-radius: 8px;
#                 padding: 20px;
#                 text-align: center;
#                 box-shadow: 0 1px 3px rgba(0,0,0,0.1);
#                 margin: 10px 0;
#             ">
#                 <div style="color: #607D8B; font-size: 1.5rem; margin-bottom: 8px;">📊</div>
#                 <div style="color: #455A64; font-size: 1.6rem; font-weight: 600;">{total_capacity:.1f}</div>
#                 <div style="color: #666; font-size: 0.9rem; margin: 4px 0;">kWp Total</div>
#                 <div style="color: #999; font-size: 0.8rem;">
#                     Capacidade instalada
#                 </div>
#             </div>
#             """,
#             unsafe_allow_html=True,
#         )


def render_date_selector():
    col_date, _ = st.columns([1, 4])

    with col_date:
        st.markdown(
            """
            <div style="
                background: linear-gradient(90deg, #2196F3 0%, #1976D2 100%);
                padding: 8px 12px;
                border-radius: 8px;
                color: white;
                margin-bottom: 4px;
                box-shadow: 0 2px 8px rgba(33, 150, 243, 0.10);
                display: flex;
                align-items: center;
            ">
                <span style="font-size: 1rem; font-weight: 500; margin-right: 8px;">📅 Data de análise:</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([2, 0.5, 0.5])
        with col1:
            new_date = st.date_input(
                "",
                value=st.session_state.rt_selected_date,
                max_value=datetime.now().date(),
                key="rt_date_selector",
                label_visibility="collapsed",
            )
            if new_date != st.session_state.rt_selected_date:
                st.session_state.rt_selected_date = new_date
                st.rerun()

        with col2:
            prev_clicked = st.button("◀", key="rt_prev_day", help="Dia anterior", type="primary")
            if prev_clicked:
                st.session_state.rt_selected_date = st.session_state.rt_selected_date - timedelta(days=1)

        with col3:
            next_clicked = st.button("▶", key="rt_next_day", help="Próximo dia", type="primary")
            if next_clicked:
                if st.session_state.rt_selected_date < datetime.now().date():
                    st.session_state.rt_selected_date = st.session_state.rt_selected_date + timedelta(days=1)

    return st.session_state.rt_selected_date


def create_realtime_power_curves(all_plants_data, selected_date):
    fig = go.Figure()

    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
    selected_date_str = selected_date.strftime("%Y-%m-%d")

    for color_idx, (plant_key, data) in enumerate(all_plants_data.items()):
        config = data["config"]
        power_data = data["power_data"]
        color = colors[color_idx % len(colors)]

        if not power_data.empty:
            smoothed_power = power_data["pv_power"].rolling(window=3, center=True, min_periods=1).mean()

            fig.add_trace(
                go.Scatter(
                    x=power_data.index,
                    y=smoothed_power,
                    mode="lines",
                    name=config["acronym"],
                    line=dict(color=color, width=2, shape="spline"),
                    hovertemplate=f"<b>{config['acronym']}</b><br>%{{x|%H:%M}}<br>%{{y:.1f}} kW<extra></extra>",
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=[f"{selected_date_str} 06:00:00", f"{selected_date_str} 18:00:00"],
                    y=[0, 0],
                    mode="lines",
                    name=f"{config['acronym']} (Offline)",
                    line=dict(color=color, width=1.5, dash="dash"),
                    hovertemplate=f"<b>{config['acronym']}</b><br>OFFLINE<extra></extra>",
                )
            )

    fig.update_layout(
        title=dict(
            text=f"Curvas de Potência - {selected_date.strftime('%d/%m/%Y')}", font=dict(size=18, color="#2c3e50")
        ),
        xaxis=dict(
            title="Horário",
            range=[f"{selected_date_str} 05:30:00", f"{selected_date_str} 18:30:00"],
            dtick=3600000,
            tickformat="%H:%M",
            showgrid=True,
            gridcolor="rgba(52, 152, 219, 0.1)",
            tickfont=dict(size=12, color="#2c3e50"),
        ),
        yaxis=dict(
            title="Potência (kW)",
            showgrid=True,
            gridcolor="rgba(52, 152, 219, 0.1)",
            tickfont=dict(size=12, color="#2c3e50"),
        ),
        plot_bgcolor="rgba(255,255,255,0.9)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=500,
        margin=dict(t=60, b=50, l=60, r=30),
        font=dict(family="Inter, Arial", size=12),
        hovermode="x unified",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.90,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
    )

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def create_advanced_table_view(all_plants_data, selected_date):
    df_data = []

    for plant_key, data in all_plants_data.items():
        config = data["config"]
        power_data = data["power_data"]

        metrics = calculate_plant_metrics_today(
            power_data, energy_data=data["energy_data"], capacity_kwp=config["capacity_kwp"]
        )

        meta_diaria = config["capacity_kwp"] * 8 * 0.8
        progresso_meta = (metrics["energy_today"] / meta_diaria) if meta_diaria > 0 else 0

        if data["status"] == "online":
            status_emoji = "🟢"
            status_text = "Online"
        elif data["status"] == "error":
            status_emoji = "🔴"
            status_text = "Erro"
        else:
            status_emoji = "🟡"
            status_text = "Offline"

        if not power_data.empty:
            hourly_data = power_data.resample("H")["pv_power"].mean().fillna(0)
            trend_data = hourly_data.tail(12).tolist()
        else:
            trend_data = [0] * 12

        df_data.append({
            "planta": config["acronym"],
            "status": f"{status_emoji} {status_text}",
            "potencia_atual": metrics["current_power"],
            "energia_hoje": metrics["energy_today"],
            "progresso_meta": min(progresso_meta, 1.2),
            "performance": metrics["performance_ratio"],
            "capacidade": config["capacity_kwp"],
            "trend_data": trend_data,
            "peak_time": metrics["peak_time"],
        })

    df = pd.DataFrame(df_data)

    column_config = {
        "planta": st.column_config.TextColumn("🏭 Planta", help="Nome da planta fotovoltaica", width="medium"),
        "status": st.column_config.TextColumn("📊 Status", help="Status operacional atual", width="small"),
        "potencia_atual": st.column_config.NumberColumn(
            "⚡ Potência", help="Última potência registrada em kW", format="%.1f kW", width="small"
        ),
        "energia_hoje": st.column_config.NumberColumn(
            "🔋 Energia", help="Energia gerada no dia", format="%.1f kWh", width="small"
        ),
        "progresso_meta": st.column_config.ProgressColumn(
            "🎯 Meta",
            help="Progresso da meta diária",
            min_value=0,
            max_value=1.2,
            format="%.0%",
            width="medium",
        ),
        "performance": st.column_config.NumberColumn(
            "📈 Performance", help="% da capacidade máxima atingida", format="%.1f%%", width="small"
        ),
        "capacidade": st.column_config.NumberColumn(
            "⚙️ Capacidade", help="Capacidade instalada", format="%.1f kWp", width="small"
        ),
        "trend_data": st.column_config.LineChartColumn(
            "📊 Tendência 12h", help="Curva de potência das últimas 12 horas", y_min=0, width="large"
        ),
        "peak_time": st.column_config.TextColumn("🏆 Pico", help="Horário do pico de potência", width="small"),
    }

    event = st.dataframe(
        df,
        column_config=column_config,
        width="stretch",
        hide_index=True,
        height=400,
        on_select="rerun",
        selection_mode="single-row",
    )

    if len(event.selection.rows) > 0:
        selected_row = event.selection.rows[0]
        selected_plant = df.iloc[selected_row]

        st.info(
            f"📊 Planta selecionada: **{selected_plant['planta']}** - "
            f"Potência: {selected_plant['potencia_atual']:.1f} kW - "
            f"Performance: {selected_plant['performance']:.1f}%"
        )


def create_cards_view(all_plants_data):
    num_plants = len(all_plants_data)
    cols_per_row = 2 if num_plants <= 4 else 3

    plant_items = list(all_plants_data.items())

    for i in range(0, num_plants, cols_per_row):
        cols = st.columns(cols_per_row)

        for j, col in enumerate(cols):
            plant_idx = i + j
            if plant_idx < num_plants:
                plant_key, data = plant_items[plant_idx]

                with col:
                    render_enhanced_plant_card(plant_key, data)


def render_enhanced_plant_card(plant_key, data):
    config = data["config"]
    power_data = data["power_data"]
    energy_data = data["energy_data"]

    metrics = calculate_plant_metrics_today(power_data, energy_data, config["capacity_kwp"])

    meta_diaria = config["capacity_kwp"] * 8 * 0.8
    progresso_meta = (metrics["energy_today"] / meta_diaria * 100) if meta_diaria > 0 else 0

    if data["status"] == "offline":
        status_color = "#F44336"
        status_text = "OFFLINE"
        border_color = "#F44336"
        status_icon = "🔴"
    elif data["status"] == "error":
        status_color = "#FF9800"
        status_text = "ERRO"
        border_color = "#FF9800"
        status_icon = "🟠"
    elif metrics["capacity_factor"] < 5:
        status_color = "#FF9800"
        status_text = "BAIXA"
        border_color = "#FF9800"
        status_icon = "🟡"
    else:
        status_color = "#4CAF50"
        status_text = "ONLINE"
        border_color = "#4CAF50"
        status_icon = "🟢"

    st.markdown(
        f"""
        <div style="
            background: white;
            border: 1px solid #E0E0E0;
            border-left: 4px solid {border_color};
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h4 style="margin: 0; font-size: 16px; font-weight: 600; color: #333;">{config["acronym"]}</h4>
                <span style="
                    background: #F5F5F5;
                    color: {status_color};
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 500;
                ">{status_icon} {status_text}</span>
            </div>
            
            <div style="margin-bottom: 15px;">
                <div style="font-size: 20px; font-weight: 600; color: #2196F3; margin-bottom: 5px;">
                    {metrics["current_power"]:.1f} kW
                </div>
                <div style="color: #666; font-size: 13px;">
                    Energia hoje: {metrics["energy_today"]:.1f} kWh
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    subcol1, subcol2 = st.columns(2)

    with subcol1:
        st.metric(
            "Pico",
            f"{metrics['peak_power']:.1f} kW",
            delta=f"às {metrics['peak_time']}",
            help="Pico de potência do dia",
        )

    with subcol2:
        st.metric("Performance", f"{metrics['performance_ratio']:.1f}%", help="% da capacidade atingida")

    st.markdown("**Meta Diária**")
    progress_value = min(progresso_meta / 100, 1.0)

    st.markdown(
        f"""
        <div style="
            background: #F5F5F5; 
            border-radius: 4px; 
            height: 8px; 
            margin: 8px 0;
            overflow: hidden;
        ">
            <div style="
                background: {border_color}; 
                height: 100%; 
                width: {progress_value * 100}%;
                transition: width 0.3s ease;
            "></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"{progresso_meta:.1f}% da meta atingida ({meta_diaria:.1f} kWh)")


def render_section_divider(title, icon=""):
    st.markdown(
        f"""
        <div style="
            margin: 30px 0 20px 0;
            padding: 15px 0;
            border-bottom: 2px solid #E0E0E0;
        ">
            <h3 style="
                margin: 0;
                color: #333;
                font-size: 1.3rem;
                font-weight: 500;
            ">{icon} {title}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_energy_comparison_bars(all_plants_data):
    """Cria gráfico de barras comparando energia do dia"""
    plants_data = []
    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]

    color_idx = 0
    for plant_key, data in all_plants_data.items():
        config = data["config"]
        power_data = data["power_data"]

        if not power_data.empty:
            energy_today = power_data["pv_power"].sum() * (5 / 60)
            performance = (energy_today / (config["capacity_kwp"] * 8)) * 100
        else:
            energy_today = 0
            performance = 0

        plants_data.append({
            "name": config["acronym"],
            "energy": energy_today,
            "performance": performance,
            "color": colors[color_idx % len(colors)],
            "status": data["status"],
        })
        color_idx += 1

    plants_data.sort(key=lambda x: x["energy"], reverse=True)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=[p["name"] for p in plants_data],
            y=[p["energy"] for p in plants_data],
            marker=dict(color=[p["color"] for p in plants_data], opacity=0.8, line=dict(color="white", width=1)),
            text=[f"{p['energy']:.1f} kWh<br>{p['performance']:.0f}%" for p in plants_data],
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>Energia: %{y:.1f} kWh<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        title="📊 Energia Gerada por Planta",
        xaxis=dict(title="Plantas", tickfont=dict(size=12, color="#2c3e50")),
        yaxis=dict(
            title="Energia (kWh)",
            showgrid=True,
            gridcolor="rgba(52, 152, 219, 0.1)",
            tickfont=dict(size=12, color="#2c3e50"),
        ),
        plot_bgcolor="rgba(255,255,255,0.9)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin=dict(t=50, b=50, l=60, r=30),
        font=dict(family="Inter, Arial", size=12),
    )

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def show_realtime_multi_plant_dashboard():
    initialize_realtime_session_state()
    render_header()

    with st.sidebar:
        st.markdown("### 🎛️ Controles")

        view_mode = st.radio(
            "Modo de visualização:",
            ["📋 Tabela Avançada", "📱 Cards Visuais"],
            horizontal=True,
            help="Escolha como visualizar as plantas",
        )

        st.markdown("---")
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=False, key="auto_refresh_toggle")
        st.session_state.rt_auto_refresh = auto_refresh

        if st.button("🔄 Atualizar Dados", width="stretch", type="primary"):
            st.cache_data.clear()
            st.rerun()

        if st.session_state.rt_last_update:
            st.success(f"📡 Última atualização: {st.session_state.rt_last_update.strftime('%H:%M:%S')}")

        st.markdown("---")
        st.caption("💡 Use o seletor de data para visualizar dados históricos")

    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    cols_cards = [col2, col3, col4, col5]

    with col1:
        try:
            st.write("")
            photo_path = "assets/campus_fcte_uac.jpeg"
            st.image(photo_path)
        except:
            st.info("📷 Foto da aerea FCTE - Plantas Fotovoltaicas MEPA não disponível")

    selected_date = render_date_selector()
    # all_plants_data = load_realtime_data_all_plants(selected_date)
    all_plants_data = "TODO: Implement data loading for all plants"
    return

    if not all_plants_data:
        st.error("❌ Nenhuma planta com credenciais configuradas encontrada")
        st.info("Verifique as configurações das plantas em `settings.py`")
        return

    render_section_divider("Visão Geral do Sistema", "📊")
    render_system_overview_cards(all_plants_data, cols_cards)

    render_section_divider("Curvas de Potência Comparativas", "📈")
    create_realtime_power_curves(all_plants_data, selected_date)

    if view_mode == "📋 Tabela Avançada":
        render_section_divider("Visão Tabular Detalhada", "📋")
        create_advanced_table_view(all_plants_data, selected_date)

        st.info("💡 Clique em uma linha da tabela para ver mais detalhes da planta selecionada")

    else:
        render_section_divider("Status Individual das Plantas", "📱")
        create_cards_view(all_plants_data)

    render_section_divider("Ranking de Energia", "🏆")

    col_ranking, col_space = st.columns([3, 1])
    with col_ranking:
        create_energy_comparison_bars(all_plants_data)
        st.caption(f"Comparação da energia gerada em {selected_date.strftime('%d/%m/%Y')}")

    st.markdown("---")
    col_footer1, col_footer2, col_footer3 = st.columns(3)

    with col_footer1:
        st.markdown("**Sistema de Monitoramento Solar**")
        st.caption("Dashboard multi-plantas em tempo real")

    with col_footer2:
        if st.session_state.rt_last_update:
            st.markdown("**Status da Conexão**")
            st.caption(f"Última sincronização: {st.session_state.rt_last_update.strftime('%H:%M:%S')}")

    with col_footer3:
        total_plants = len(all_plants_data)
        online_plants = len([p for p in all_plants_data.values() if p["status"] == "online"])
        st.markdown("**Resumo do Sistema**")
        st.caption(f"{online_plants}/{total_plants} plantas operacionais")

    if st.session_state.rt_auto_refresh:
        st.toast("🔄 Dashboard atualizando automaticamente")
        time.sleep(60)
        st.rerun()


if __name__ == "__main__":
    show_realtime_multi_plant_dashboard()
