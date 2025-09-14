import logging
import os
import sys
from pathlib import Path

from rich.logging import RichHandler

# from logging.handlers import RotatingFileHandler


LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


LOG_FORMATS = {
    "RICH": "%(module)-12s: [line: %(lineno)-3s] %(message)s",
    "DEBUG": "%(levelname)-8s %(module)-12s %(funcName) -15s : %(lineno)-3s %(message)s",
    "INFO": "%(levelname)-8s: %(message)s",
    "WARNING": "%(levelname)-8s: %(module)-8s:%(lineno)-3s %(message)s",
    "ERROR": "%(asctime)s: %(levelname)-8s: %(funcName)s :%(lineno)d %(message)s",
    "CRITICAL": "%(asctime)-15s %(levelname)-8s %(filename)-15s %(module)-8s:%(lineno)-3s %(message)s",
}

DATE_FORMAT = "%d-%m-%Y %H:%M:%S"


def create_logs_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True)
        print(f"Logs directory created: {path}")


def setup_logging(config):
    console_level = os.getenv("CONSOLE_LOG_LEVEL", "WARNING")
    file_level = os.getenv("FILE_LOG_LEVEL", "WARNING")
    file_path = os.getenv("LOG_FILE_PATH", "logs/app.log")
    log_path = Path(file_path).parent

    # Criar diretório para logs
    create_logs_dir(log_path)

    # Config o root logger
    root_logger = logging.getLogger("solar_app")
    # root_logger.setLevel(LOG_LEVELS[console_level])
    root_logger.setLevel(logging.DEBUG)

    # Config log para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVELS[console_level])
    console_formatter = logging.Formatter(LOG_FORMATS[console_level], DATE_FORMAT)
    console_handler.setFormatter(console_formatter)

    # Config handler e formato para arquivo
    file_handler = logging.FileHandler(file_path)
    # file_handler = RotatingFileHandler(file_path, maxBytes=10*1024*1024, backupCount=5)
    file_formatter = logging.Formatter(LOG_FORMATS[file_level])
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(LOG_LEVELS[file_level])

    # Config rich handler (console)
    rich_handler = RichHandler(level=logging.DEBUG, rich_tracebacks=True)
    rich_handler.setFormatter(logging.Formatter(LOG_FORMATS["RICH"], DATE_FORMAT))

    # adicionar handlers ao logger
    root_logger.addHandler(rich_handler)
    # root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
