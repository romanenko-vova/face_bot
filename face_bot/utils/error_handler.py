import traceback
import functools
from telegram import Update
from telegram.error import (
    TelegramError, 
    BadRequest, 
    TimedOut, 
    NetworkError,
    ChatMigrated,
    Conflict
)
from telegram.ext import ContextTypes
from face_bot.utils.logger import logger
from face_bot.static.config import ERROR_MESSAGES


def error_handler(func):
    """
    Декоратор для обработки исключений в обработчиках команд
    
    Оборачивает функцию-обработчик и перехватывает исключения,
    логируя их и отправляя пользователю сообщение об ошибке
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except BadRequest as e:
            error_msg = f"Ошибка запроса: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            if update and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=ERROR_MESSAGES["general_error"]
                )
        except TimedOut as e:
            error_msg = f"Превышено время ожидания: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            if update and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Превышено время ожидания ответа. Пожалуйста, попробуйте позже."
                )
        except NetworkError as e:
            error_msg = f"Ошибка сети: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            if update and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Ошибка сети. Пожалуйста, проверьте соединение и попробуйте снова."
                )
        except TelegramError as e:
            error_msg = f"Ошибка Telegram: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            if update and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=ERROR_MESSAGES["general_error"]
                )
        except Exception as e:
            error_msg = f"Необработанное исключение: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            if update and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=ERROR_MESSAGES["general_error"]
                )
    return wrapper


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Глобальный обработчик ошибок для Application
    """
    # Получаем информацию об ошибке из контекста
    error = context.error
    
    try:
        raise error
    except ChatMigrated as e:
        logger.warning(f'Чат мигрировал на другой ID: {e.new_chat_id}')
    except Conflict as e:
        logger.error(f'Conflict error: {e}')
    except BadRequest as e:
        logger.error(f'Bad request: {e}')
    except TimedOut as e:
        logger.error(f'Timed out: {e}')
    except NetworkError as e:
        logger.error(f'Network error: {e}')
    except TelegramError as e:
        logger.error(f'Telegram error: {e}')
    except Exception as e:
        logger.error(f'Необработанное исключение: {e}\n{traceback.format_exc()}')
    
    # Если есть обновление и оно содержит id чата
    if update and hasattr(update, 'effective_chat') and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=ERROR_MESSAGES["general_error"]
            )
        except Exception as e:
            logger.error(f'Ошибка при отправке сообщения об ошибке: {e}') 