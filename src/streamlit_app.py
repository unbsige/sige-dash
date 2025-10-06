import logging

import streamlit as st
from PIL import Image

from src.config import settings
from src.load_data import load_data
from src.pages.home import render_homepage

logger = logging.getLogger("solar_app")

st.set_page_config(
    page_title="Produção de Energia",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded",
)


if __name__ == "__main__":
    logger.info("Iniciando main")
    logo = Image.open(settings.ROOT_DIR / "assets" / "unb_logo.jpeg")
    st.sidebar.title("UnB - Solar Production")
    st.sidebar.image(logo, width="stretch")

    # load_data()
    render_homepage()
