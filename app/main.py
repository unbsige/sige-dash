import logging
import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


def setup_environment():
    root_dir = Path(__file__).parent.parent.resolve()
    sys.path.append(str(root_dir))
    sys.path.append(str(root_dir / "app"))

    env_path = root_dir / ".env"
    load_dotenv(env_path)

    os.environ.setdefault("SETTINGS_MODULE", "config.settings")
    settings_module = os.environ["SETTINGS_MODULE"]

    try:
        settings = __import__(settings_module, fromlist=[''])
    except ImportError as e:
        raise ImportError(f"Não foi possível importar as configurações '{settings_module}': {e}")

    return settings, root_dir


def configure_logging(settings):
    log_level = getattr(settings, 'LOG_LEVEL', logging.INFO)
    log_format = getattr(settings, 'LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = getattr(settings, 'LOG_FILE', None)

    logging.basicConfig(level=log_level, format=log_format)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)

    logging.info("Logging configurado")


def start_app():

    home_page = st.Page("streamlit_app.py", title="Home", icon=":material/home:", )
    eda_page = st.Page("./pages/preparation/data_analisys.py", title="Análise exploratória de dados", icon=":material/add_circle:",)
    chart_page = st.Page("./pages/preparation/data_visualization.py", title="Visualizacao dos dados", icon=":material/add_circle:",)
    ml_page = st.Page("./pages/model_ml/machine_learning.py", title="Aprendizado de maqina", icon=":material/delete:")

    pg = st.navigation(
        {
            "Dashboard": [home_page],
            "Preparation": [eda_page],
            "Machine Learning": [chart_page, ml_page],
        },
    )
    pg.run()


if __name__ == "__main__":
    try:
        settings, root_dir = setup_environment()
        configure_logging(settings)
        start_app()

    except Exception as e:
        logging.exception(f"Erro ao iniciar a aplicação: {e}")
        sys.exit(1)
