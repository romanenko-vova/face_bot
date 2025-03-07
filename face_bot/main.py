import os
import asyncio

from dotenv import load_dotenv

from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    PicklePersistence,
)

from face_bot.database.db import init_db

from face_bot.handlers.common_handler import start, get_phone, send_warning_phone, cancel
from face_bot.handlers.subscriptions_handler import (
    subscriptions_callback,
    get_name,
    send_warning_name,
    show_subscriptions,
)

from face_bot.static.states import (
    PROGREV_MESSAGES,
    PHONE,
    ADMIN_COMMANDS,
    MAILING,
    SUBSCRIPTIONS,
    NAME,
)

from face_bot.handlers.callbacks_handler import user_progrev_callback
from face_bot.handlers.admin_handler import admin_callbacks, get_mail

from face_bot.utils.logger import logger
from face_bot.utils.error_handler import global_error_handler
from face_bot.utils.session_manager import schedule_session_cleanup
from face_bot.static.config import USERS_CACHE_PATH, PHONE_REGEX, NAME_REGEX

load_dotenv()


def main():
    logger.info("Запуск бота")
    try:
        persistence = PicklePersistence(filepath=USERS_CACHE_PATH)
        application = (
            Application.builder()
            .token(os.getenv("TOKEN"))
            .persistence(persistence)
            .build()
        )

        # Добавление глобального обработчика ошибок
        application.add_error_handler(global_error_handler)

        # Настройка обработчика диалога
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                PROGREV_MESSAGES: [
                    CallbackQueryHandler(user_progrev_callback),
                    CommandHandler("cancel", cancel),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: start(u, c)),
                ],
                PHONE: [
                    MessageHandler(filters.CONTACT, get_phone),
                    MessageHandler(filters.Regex(PHONE_REGEX), get_phone),
                    CommandHandler("cancel", cancel),
                    MessageHandler(
                        filters.TEXT
                        & (~filters.Regex(PHONE_REGEX))
                        & (~filters.CONTACT)
                        & (~filters.COMMAND),
                        send_warning_phone,
                    ),
                ],
                ADMIN_COMMANDS: [
                    CallbackQueryHandler(admin_callbacks),
                    CommandHandler("cancel", cancel),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, admin_callbacks),
                ],
                MAILING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, get_mail),
                    CommandHandler("cancel", cancel),
                ],
                SUBSCRIPTIONS: [
                    CallbackQueryHandler(subscriptions_callback),
                    CommandHandler("cancel", cancel),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, show_subscriptions),
                ],
                NAME: [
                    MessageHandler(filters.Regex(NAME_REGEX), get_name),
                    CommandHandler("cancel", cancel),
                    MessageHandler(
                        filters.TEXT & (~filters.Regex(NAME_REGEX)),
                        send_warning_name,
                    ),
                ],
            },
            fallbacks=[
                MessageHandler(
                    filters.TEXT & filters.Regex("^🛒 Магазин$"), show_subscriptions
                ),
                CommandHandler("start", start),
                CommandHandler("cancel", cancel),
                # Обработчик для неизвестных команд
                MessageHandler(filters.COMMAND, start),
                # Обработчик для всех остальных сообщений
                MessageHandler(filters.ALL, lambda u, c: start(u, c)),
            ],
            persistent=True,
            name="conv_handler",
            allow_reentry=True,  # Разрешаем повторный вход в разговор
        )

        application.add_handler(conv_handler)

        # Настройка очистки сессий
        schedule_session_cleanup(application)

        logger.info("Бот запущен и готов к работе")
        application.run_polling()

    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        logger.info("Инициализация базы данных")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(init_db())
        logger.info("База данных успешно инициализирована")

        main()
    except Exception as e:
        logger.critical(f"Ошибка при запуске приложения: {str(e)}", exc_info=True)
