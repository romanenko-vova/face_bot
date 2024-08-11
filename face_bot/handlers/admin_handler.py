from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from face_bot.static.states import ADMIN_COMMANDS, MAILING
from face_bot.static.callbacks import (
    CONVERSIONS,
    LEADER_BOARD,
    MAIL,
    YES_MAIL,
    NO_MAIL,
)
from face_bot.static.keys import (
    MESSAGE_MAIL,
)

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import get_conversions, DB_PATH

from face_bot.handlers.common_handler import start

import aiosqlite


async def admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id

    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.effective_message.message_id,
    )

    if int(query.data) == LEADER_BOARD:
        """send all users"""
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT id, id_tg, status, name, phone FROM users"
            ) as cursor:
                rows = await cursor.fetchall()
                messages = "\n".join(
                    [
                        f"{row[0]}: {row[1]} - {row[2]} - {row[3]} - {row[4]}"
                        for row in rows
                    ]
                )

        if len(messages) != 0:
            await context.bot.send_message(
                chat_id=chat_id,
                text="id: tg_id - status - name - phone",
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text=messages,
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="- no users -",
            )

        return await start(update, context)

    elif int(query.data) == MAIL:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Отправь мне сообщение, которое увидят все пользователи",
        )
        return MAILING

    elif int(query.data) == YES_MAIL:
        await send_mail(query, context)

        return await start(update, context)

    elif int(query.data) == NO_MAIL:
        return await start(update, context)

    elif int(query.data) == CONVERSIONS:
        states_list = [
            "Зарегистрировались",
            "Отправили контакт",
            "Попробовали Экспересс гайд",
            # TODO add
        ]

        number_users = await get_conversions()
        message = f"{states_list[0]}"

        for i in range(len(states_list) - 1):
            conversion = round(number_users[i + 1] / number_users[i] * 100, 2)

            message += f"\n|\n|    {conversion}%\nv\n{states_list[i+1]}"

        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
        )

        return await start(update, context)


async def get_mail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.effective_message.text

    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data=YES_MAIL),
            InlineKeyboardButton("Нет", callback_data=NO_MAIL),
        ]
    ]

    context.user_data[MESSAGE_MAIL] = msg

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=escape_text(f"Отправить это?\n\n{msg}"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    return ADMIN_COMMANDS


async def send_mail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = context.user_data.get(MESSAGE_MAIL, "no message found")

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id_tg FROM users") as cursor:
            async for row in cursor:
                await context.bot.send_message(
                    chat_id=row[0],
                    text=escape_text(msg),
                    parse_mode=ParseMode.MARKDOWN_V2,
                )
