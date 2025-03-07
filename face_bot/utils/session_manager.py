import os
import time
import pickle
import datetime
from face_bot.utils.logger import logger
from face_bot.static.config import USERS_CACHE_PATH, SESSION_EXPIRY_DAYS, MAX_CACHE_SIZE_MB

class SessionManager:
    """Класс для управления сессиями пользователей бота"""
    
    @staticmethod
    def check_and_clean_sessions():
        """Проверка и очистка устаревших сессий"""
        try:
            if not os.path.exists(USERS_CACHE_PATH):
                logger.warning(f"Файл кэша {USERS_CACHE_PATH} не найден")
                return
                
            # Проверка размера файла кэша
            file_size_mb = os.path.getsize(USERS_CACHE_PATH) / (1024 * 1024)
            if file_size_mb > MAX_CACHE_SIZE_MB:
                logger.warning(f"Файл кэша превысил установленный лимит ({file_size_mb:.2f} MB > {MAX_CACHE_SIZE_MB} MB)")
                
            # Загрузка данных сессий
            with open(USERS_CACHE_PATH, 'rb') as f:
                try:
                    data = pickle.load(f)
                except (pickle.PickleError, EOFError):
                    logger.error("Ошибка при загрузке файла кэша")
                    return
            
            if not data or not isinstance(data, dict):
                logger.warning("Файл кэша поврежден или имеет неверный формат")
                return
                
            # Текущая дата
            now = datetime.datetime.now()
            expiry_threshold = now - datetime.timedelta(days=SESSION_EXPIRY_DAYS)
            
            # Данные пользователей обычно хранятся в data['user_data']
            if 'user_data' in data and isinstance(data['user_data'], dict):
                old_count = len(data['user_data'])
                
                # Проверка каждой сессии на время последней активности
                expired_users = []
                for user_id, user_data in data['user_data'].items():
                    # Проверка времени последней активности, если оно есть
                    if 'last_activity' in user_data:
                        last_activity = user_data['last_activity']
                        if isinstance(last_activity, datetime.datetime) and last_activity < expiry_threshold:
                            expired_users.append(user_id)
                
                # Удаление устаревших сессий
                for user_id in expired_users:
                    del data['user_data'][user_id]
                
                new_count = len(data['user_data'])
                if old_count != new_count:
                    logger.info(f"Очищено {old_count - new_count} устаревших сессий")
                    
                    # Сохранение обновленных данных
                    with open(USERS_CACHE_PATH, 'wb') as f:
                        pickle.dump(data, f)
        
        except Exception as e:
            logger.error(f"Ошибка при очистке сессий: {str(e)}")

    @staticmethod
    def update_user_activity(context, user_id):
        """Обновление времени последней активности пользователя"""
        try:
            if hasattr(context, 'user_data') and user_id is not None:
                context.user_data['last_activity'] = datetime.datetime.now()
        except Exception as e:
            logger.error(f"Ошибка при обновлении активности пользователя {user_id}: {str(e)}")

# Асинхронная обертка для синхронного метода
async def async_clean_sessions(context):
    """Асинхронная обертка для вызова синхронного метода очистки сессий"""
    SessionManager.check_and_clean_sessions()

# Функция для запуска проверки сессий по расписанию
def schedule_session_cleanup(application):
    """Добавление задачи очистки сессий в планировщик приложения"""
    job_queue = application.job_queue
    # Запуск очистки каждые 24 часа
    job_queue.run_repeating(
        async_clean_sessions, 
        interval=86400,  
        first=10  
    )
    logger.info("Запланирована регулярная очистка устаревших сессий") 