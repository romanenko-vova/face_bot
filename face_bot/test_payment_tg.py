import os

from dotenv import load_dotenv

from telegram import LabeledPrice, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()


PAYMENT_PROVIDER_TOKEN = "381764678:TEST:92284"

# TODO создать нового бота и к нему этот токен


async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    msg = "Use /shop"

    await update.message.reply_text(msg)


async def buy_face_massage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    await context.bot.send_invoice(
        chat_id=chat_id,
        title="Массаж лица",
        description="Описание массажа лица",
        payload="Custom-Payload",
        provider_token=os.getenv("PROVIDER_TOKEN"),
        currency="RUB",
        prices=[LabeledPrice("Массаж лица", 1790 * 100)],
    )


async def precheckout_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.pre_checkout_query

    if query.invoice_payload != "Custom-Payload":
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)


async def successful_payment_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.message.reply_text("Thank you for your payment!")
    await update.message.reply_text(update.effective_user.id)


def main() -> None:
    print("MAIN")

    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start_callback))

    application.add_handler(CommandHandler("shop", buy_face_massage))

    application.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
