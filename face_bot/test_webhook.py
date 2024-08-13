import os

import asyncio
from dotenv import load_dotenv
import html
from dataclasses import dataclass
from http import HTTPStatus

import uvicorn
from asgiref.wsgi import WsgiToAsgi
from flask import Flask, Response, abort, make_response, request

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ExtBot,
    TypeHandler,
)

# Define configuration constants
URL = "https://f501-83-217-200-54.ngrok-free.app"
ADMIN_CHAT_ID = 123456
PORT = 8080
TOKEN = "123:ABC"


load_dotenv()


@dataclass
class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""

    user_id: int
    payload: str


class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    @classmethod
    def from_update(
        cls,
        update: object,
        application: "Application",
    ) -> "CustomContext":
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)


async def start(update: Update, context: CustomContext) -> None:
    payload_url = html.escape(
        f"{URL}/submitpayload?user_id=<your user id>&payload=<payload>"
    )

    text = (
        f"To check if the bot is still running, call <code>{URL}/healthcheck</code>.\n\n"
        f"To post a custom update, call <code>{payload_url}</code>."
    )
    await update.message.reply_html(text=text)


async def webhook_update(update: WebhookUpdate, context: CustomContext) -> None:
    """Handle custom updates."""
    chat_member = await context.bot.get_chat_member(
        chat_id=update.user_id, user_id=update.user_id
    )
    payloads = context.user_data.setdefault("payloads", [])
    payloads.append(update.payload)
    combined_payloads = "</code>\n• <code>".join(payloads)
    text = (
        f"The user {chat_member.user.mention_html()} has sent a new payload. "
        f"So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>"
    )
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID, text=text, parse_mode=ParseMode.HTML
    )


async def main() -> None:
    """Set up PTB application and a web application for handling the incoming requests."""

    print("MAIN")

    context_types = ContextTypes(context=CustomContext)

    application = (
        Application.builder()
        .token(os.getenv("TOKEN"))
        .updater(None)
        .context_types(context_types)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(TypeHandler(type=WebhookUpdate, callback=webhook_update))

    # Pass webhook settings to telegram
    await application.bot.set_webhook(
        url=f"{URL}/telegram", allowed_updates=Update.ALL_TYPES
    )

    flask_app = Flask(__name__)

    @flask_app.post("/telegram")
    async def telegram() -> Response:
        await application.update_queue.put(
            Update.de_json(data=request.json, bot=application.bot)
        )
        return Response(status=HTTPStatus.OK)

    @flask_app.route("/submitpayload", methods=["GET", "POST"])
    async def custom_updates() -> Response:
        try:
            user_id = int(request.args["user_id"])
            payload = request.args["payload"]
        except KeyError:
            abort(
                HTTPStatus.BAD_REQUEST,
                "Please pass both `user_id` and `payload` as query parameters.",
            )
        except ValueError:
            abort(HTTPStatus.BAD_REQUEST, "The `user_id` must be a string!")

        await application.update_queue.put(
            WebhookUpdate(user_id=user_id, payload=payload)
        )
        return Response(status=HTTPStatus.OK)

    @flask_app.get("/healthcheck")
    async def health() -> Response:
        response = make_response("The bot is still running fine :)", HTTPStatus.OK)
        response.mimetype = "text/plain"
        return response

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(flask_app),
            port=PORT,
            use_colors=False,
            host="127.0.0.1",
        )
    )

    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
