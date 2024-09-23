import logging

import streamlit as st
from config import settings
from dash import dashboard

# from feature_utils import create_features
from load_data import load_data
from PIL import Image

# from app.pages import machine_learning

logger = logging.getLogger("solar_app")

st.set_page_config(
    page_title="Produção de Energia",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded",
)


logger.info("Iniciando main")
logo = Image.open(settings.ROOT_DIR / "assets" / "unb_logo.jpeg")
st.sidebar.title("UnB - Solar Production")
st.sidebar.image(logo, use_column_width=True)

load_data()
dashboard()
