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

from face_bot.handlers.common_handler import start, get_phone, send_warning_phone
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

load_dotenv()


def main():
    print("MAIN")
    persistence = PicklePersistence(filepath="users_cache")
    application = (
        Application.builder().token(os.getenv("TOKEN")).persistence(persistence).build()
    )

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
                    filters.TEXT
                    & (~filters.Regex("^7\d{10}$"))
                    & (~filters.CONTACT)
                    & (~filters.COMMAND),
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
        fallbacks=[
            MessageHandler(
                filters.TEXT & filters.Regex("^🛒 Магазин$"), show_subscriptions
            ),
            CommandHandler("start", start),
        ],
        persistent=True,
        name="conv_handler",
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())

    main()
