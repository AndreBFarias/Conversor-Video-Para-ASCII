import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name="ConversorApp", log_file="logs/system.log"):
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
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024, # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Console Handler (Opcional, mas útil para debug durante dev)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
