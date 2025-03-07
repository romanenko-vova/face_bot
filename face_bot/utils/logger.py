import logging
import os
from logging.handlers import RotatingFileHandler

# Создаем директорию для логов, если ее нет
os.makedirs('logs', exist_ok=True)

# Настройка логгера
def setup_logger():
    """Настройка логгера с ротацией файлов"""
    logger = logging.getLogger('face_bot')
    logger.setLevel(logging.INFO)
    
    # Форматирование логов
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Обработчик для вывода в файл с ротацией (максимум 10 МБ, 5 бэкапов)
    file_handler = RotatingFileHandler('logs/bot.log', maxBytes=10*1024*1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Создаем экземпляр логгера
logger = setup_logger() 