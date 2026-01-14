import logging
import os
from logging.handlers import RotatingFileHandler
from src.app.constants import USER_CACHE_DIR

def setup_logger(name="ConversorApp", log_file=None):
    if log_file is None:
        log_file = os.path.join(USER_CACHE_DIR, "logs", "system.log")
    """
    Configura um logger rotacionado.
    Salva em logs/ com rotação de 5MB e backup de 3 arquivos.
    """
    # Garante que a pasta logs existe
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Evita duplicidade de handlers
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler (Rotacionado)
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024, # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"AVISO: Nao foi possivel criar log em arquivo ({log_file}): {e}")

    # Console Handler (Opcional, mas útil para debug durante dev)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO) # Info no console para nao poluir

    logger.addHandler(console_handler)

    return logger
