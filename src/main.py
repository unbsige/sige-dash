import importlib
import logging
import os
import sys
from pathlib import Path

import streamlit as st

from config.styles import ThemeManager


def setup_environment():
    root_dir = Path(__file__).parent.parent.resolve()

    paths_to_add = [
        str(root_dir),
        str(root_dir / "src"),
        str(root_dir / "src" / "config"),
    ]

    for path in paths_to_add:
        if Path(path).exists() and path not in sys.path:
            sys.path.insert(0, path)

    os.environ.setdefault("SETTINGS_MODULE", "config.settings")
    settings_module = os.environ["SETTINGS_MODULE"]

    try:
        settings = importlib.import_module(settings_module)
    except ImportError as e:
        raise ImportError(f"Não foi possível importar as configurações '{settings_module}': {e}")

    return settings


def setup_logging(settings):
    log_level = getattr(settings, "LOG_LEVEL", logging.INFO)
    log_format = getattr(settings, "LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_file = getattr(settings, "LOG_FILE", None)

    logging.basicConfig(level=log_level, format=log_format)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

    logging.info("Logging configurado")


def setup_app_theme():
    """Configura o tema global da aplicação."""
    st.set_page_config(page_title="SIGE Dashboard", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

    ThemeManager.apply_theme()


def start_app():
    home_page = st.Page("streamlit_app.py", title="Home", icon="🏠")
    ml_page = st.Page(
        "./pages/ml_model/machine_learning.py",
        title="Treinar Modelo",
        icon="🤖",
    )

    data_analysis_page = st.Page(
        "./pages/preparation/analysis.py",
        title="Análise de Dados",
        icon="📊",
    )

    physical_page = st.Page(
        "./pages/physical_model/physics.py",
        title="Modelagem Física",
        icon="⚛️",
    )

    pg = st.navigation(
        {
            "Dashboard": [home_page],
            "Análise e Modelagem": [data_analysis_page, ml_page, physical_page],
        },
    )
    pg.run()


if __name__ == "__main__":
    try:
        settings = setup_environment()
        setup_logging(settings)
        setup_app_theme()
        start_app()

    except Exception as e:
        logging.exception(f"Erro ao iniciar a aplicação: {e}")
        sys.exit(1)
