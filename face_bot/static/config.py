import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Пути к файлам и директориям
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.path.join(BASE_DIR, "users.db")
USERS_CACHE_PATH = os.path.join(BASE_DIR, "users_cache")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Параметры хранения сессий
SESSION_EXPIRY_DAYS = 30  # Время жизни сессии пользователя в днях
MAX_CACHE_SIZE_MB = 50  # Максимальный размер файла кэша в МБ

# Регулярные выражения для валидации
PHONE_REGEX = r"^(\+7|7|8)?[\s\-]?\(?[9][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$"
NAME_REGEX = r"^[A-Za-zА-Яа-яёЁ\-'\s]{2,50}$"
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Параметры логирования
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_SIZE_MB = 10
LOG_BACKUP_COUNT = 5


# Параметры бота
BOT_COMMAND_TIMEOUT = 60  # Тайм-аут команд бота в секундах
MESSAGE_RETRY_COUNT = 3  # Количество попыток отправки сообщения

# Тексты сообщений об ошибках
ERROR_MESSAGES = {
    "invalid_phone": "Неправильный формат номера телефона. Пожалуйста, введите номер в формате +79XXXXXXXXX или 89XXXXXXXXX",
    "invalid_name": "Неправильный формат имени. Пожалуйста, используйте только буквы, дефис, апостроф и пробелы. Длина имени от 2 до 50 символов.",
    "general_error": "Произошла ошибка. Пожалуйста, попробуйте еще раз или обратитесь к администратору.",
    "session_expired": "Ваша сессия истекла. Пожалуйста, начните сначала с команды /start",
} 

ADMINS = [int(id) for id in os.getenv("ADMIN_IDS").split(",")]


GROUP_ID = -1002150215263

