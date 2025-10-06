import warnings
from datetime import datetime

import streamlit as st

from src.data.data_loader import get_available_plants
from src.data.solar_plants_manager import SolarDataManager
from src.pages.dashboard.components.daily_power import show_cache_info, show_daily_production
from src.pages.dashboard.components.month_energy import show_monthly_production
from src.pages.dashboard.components.yearly_energy import show_yearly_production

warnings.filterwarnings("ignore")


available_plants = get_available_plants()
if not available_plants:
    st.error("Nenhuma planta com credenciais configuradas encontrada")
    st.stop()

with st.sidebar:
    st.subheader("🏭 Seleção de Planta")

    plant_options = {key: config["name"] for key, config in available_plants.items()}
    selected_plant_key = st.selectbox(
        "Planta",
        options=[None] + list(plant_options.keys()),
        format_func=lambda x: "Selecione uma planta..." if x is None else plant_options[x],
        index=0,
    )

    if selected_plant_key is None:
        st.warning("Por favor, selecione uma planta para continuar.")
        st.stop()

    plant_config = available_plants[selected_plant_key]

    st.info(f"""
    **{plant_config["name"]}**
    - Localização: {plant_config["location"]}
    - Capacidade: {plant_config["capacity_kwp"]} kWp
    - Latitude: {plant_config["latitude"]:.3f}°
    - Longitude: {plant_config["longitude"]:.3f}°
    """)

    device_id = plant_config["device"]["device_id"]
    st.write(f"**Device ID:** {device_id}")

    st.divider()

    if st.button("🔄 Limpar Cache"):
        st.cache_data.clear()
        st.success("Cache limpo!")

    session_key = f"client_{selected_plant_key}"
    if session_key in st.session_state:
        token_time = st.session_state.get(f"token_time_{session_key}")
        if token_time:
            elapsed = datetime.now() - token_time
            st.success(f"✅ Conectado há {elapsed.seconds // 60} minutos")

tab1, tab2, tab3 = st.tabs(["📊 Produção Diária", "📈 Produção Mensal", "🔄 Produção Anual"])

with tab1:
    show_daily_production(selected_plant_key, device_id, plant_config)

with tab2:
    show_monthly_production(selected_plant_key, plant_config)

with tab3:
    show_yearly_production(selected_plant_key, plant_config)


with st.sidebar:
    st.markdown("### Cache Status")
    show_cache_info()
