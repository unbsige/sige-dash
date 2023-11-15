import logging
import sys

from dotenv import load_dotenv

from app import main
from config import config_logger, settings


def load_env(file_path):
    load_dotenv(file_path)


if __name__ == "__main__":
    try:
        load_env(settings.ROOT_DIR / ".env")
        sys.path.append(str(settings.ROOT_DIR))
        config_logger()
        main()
    except Exception as e:
        logging.error(f"Erro ao iniciar app: {e}", exc_info=True)
