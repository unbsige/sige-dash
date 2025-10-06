import warnings
from datetime import datetime

import streamlit as st

from src.data.solar_plants_manager import SolarDataManager
from src.pages.dashboard.components.daily_power import show_cache_info, show_daily_production
from src.pages.dashboard.components.month_energy import show_monthly_production
from src.pages.dashboard.components.yearly_energy import show_yearly_production

warnings.filterwarnings("ignore")


def st_plant_selector(manager: SolarDataManager, key="plant_selector"):
    options = manager.get_selectbox_options(status=1)
    plant_options = options.get("plants", {})

    selected = st.selectbox(
        "Selecione uma Usina:",
        options=[""] + list(plant_options.keys()),
        key=key,
    )

    plant_data = plant_options.get(selected) if selected else None
    return selected, plant_data


st.title("Dashboard Solar - Planta Individual")

manager = SolarDataManager("data/solar_plants.json")

with st.sidebar:
    st.subheader("🏭 Seleção de Planta")
    selected, plant = st_plant_selector(manager)

    if selected and plant:
        st.info(f"""
        **{plant["campus"]} - {plant["building"]}**
        - Código: {plant["code"]}
        - Capacidade: {plant["power_kwp"]} kWp
        - Latitude: {plant["coordinates"]["latitude"]:.3f}°
        - Longitude: {plant["coordinates"]["longitude"]:.3f}°
        """)

    st.divider()
    if st.button("🔄 Limpar Cache"):
        st.cache_data.clear()
        st.success("Cache limpo!")


st.write("---")
if not selected:
    st.warning("Por favor, selecione uma planta para continuar.")
    st.stop()

plant = manager.load_env_data(plant)
session_key = f"client_{plant['code']}"

if session_key in st.session_state:
    token_time = st.session_state.get(f"token_time_{session_key}")
    if token_time:
        elapsed = datetime.now() - token_time
        st.success(f"✅ Conectado há {elapsed.seconds // 60} minutos")

tab1, tab2, tab3 = st.tabs(["📊 Produção Diária", "📈 Produção Mensal", "🔄 Produção Anual"])

with tab1:
    show_daily_production(plant)

with tab2:
    show_monthly_production(plant)


with tab3:
    show_yearly_production(plant)


with st.sidebar:
    st.markdown("### Cache Status")
    show_cache_info()
