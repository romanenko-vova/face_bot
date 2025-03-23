import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Создаем директорию для логов, если ее нет
os.makedirs('logs', exist_ok=True)

def setup_logger():
    """Настройка логгера с ротацией файлов"""
    logger = logging.getLogger('face_bot')
    logger.setLevel(logging.INFO)
    
    # Форматирование логов
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для вывода в файл с ротацией
    file_handler = RotatingFileHandler(
        'logs/bot.log',
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
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

def log_user_action(user_id: int, action: str, **kwargs):
    """Логирование действий пользователя"""
    details = ' | '.join(f'{k}={v}' for k, v in kwargs.items())
    logger.info(f'User {user_id} | Action: {action} | {details}')

def log_payment(user_id: int, payment_id: str, amount: float, status: str, **kwargs):
    """Логирование платежей"""
    details = ' | '.join(f'{k}={v}' for k, v in kwargs.items())
    logger.info(f'Payment | User {user_id} | ID: {payment_id} | Amount: {amount} | Status: {status} | {details}')

def log_error(error: Exception, user_id: int = None, **kwargs):
    """Логирование ошибок"""
    details = ' | '.join(f'{k}={v}' for k, v in kwargs.items())
    user_info = f'User {user_id} | ' if user_id else ''
    logger.error(f'Error | {user_info}Type: {type(error).__name__} | Message: {str(error)} | {details}', exc_info=True)

def log_info(message: str, **kwargs):
    """Логирование информационных сообщений"""
    details = ' | '.join(f'{k}={v}' for k, v in kwargs.items())
    logger.info(f'Info | {message} | {details}')

def log_warning(message: str, **kwargs):
    """Логирование предупреждений"""
    details = ' | '.join(f'{k}={v}' for k, v in kwargs.items())
    logger.warning(f'Warning | {message} | {details}') 