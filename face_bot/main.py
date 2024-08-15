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
)

from face_bot.database.db import init_db

from face_bot.handlers.common_handler import start, get_phone, send_warning_phone
from face_bot.handlers.subscriptions_handler import (
    subscriptions_callback,
    get_name,
    send_warning_name,
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

load_dotenv()


def main():
    print("MAIN")

    """
    TODO 
    1. нужна фотка татьяны или массажа оставить
    2. добавить видосы и указать их время в таймингах для джобов
    3. создать 3 времени: 12, 15, 18 
        - если ничего не купил, присылаем кейсы и переводим на меню покупок
        - если купил какую-то одну, не фул, присылаем информацию о других подписках
    """

    application = Application.builder().token(os.getenv("TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PROGREV_MESSAGES: [
                CallbackQueryHandler(user_progrev_callback),
            ],
            PHONE: [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.Regex("^7\d{10}$"), get_phone),
                MessageHandler(
                    filters.TEXT & (~filters.Regex("^7\d{10}$")) & (~filters.CONTACT),
                    send_warning_phone,
                ),
            ],
            ADMIN_COMMANDS: [
                CallbackQueryHandler(admin_callbacks),
            ],
            MAILING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mail)],
            SUBSCRIPTIONS: [
                CallbackQueryHandler(subscriptions_callback),
            ],
            NAME: [
                MessageHandler(filters.Regex("^[A-Za-zА-Яа-яёЁ\-'\s]+$"), get_name),
                MessageHandler(
                    filters.TEXT & (~filters.Regex("^[A-Za-zА-Яа-яёЁ\-'\s]+$")),
                    send_warning_name,
                ),
            ],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())

    main()
