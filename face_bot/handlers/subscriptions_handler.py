from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from face_bot.static.states import PHONE, SUBSCRIPTIONS
from face_bot.static.callbacks import MASSAGE_1, MASSAGE_2, MASSAGE_3, MASSAGE_4
from face_bot.static.conversions import TRY_GUIDE_CONV

from face_bot.static.texts import (
    CONTACT_MESSAGE,
    SUBSCRIPTION_DESCRIPTION_MSG,
    DESCRIPTION_1_MSG,
    DESCRIPTION_2_MSG,
    DESCRIPTION_3_MSG,
    DESCRIPTION_4_MSG,
)

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import update_status

from face_bot.jobs.jobs import show_cases_job, already_try_job
from face_bot.jobs.id_jobs import CASE_JOB_ID, ALREADY_TRY_JOB_ID
from face_bot.jobs.times import CASES_TIME, ALREADY_TRY_JOB_TIME


async def show_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    keyboard = [
        [
            InlineKeyboardButton("Массаж глаз — 490р", callback_data=MASSAGE_1),
        ],
        [
            InlineKeyboardButton("Массаж щек — 590р", callback_data=MASSAGE_2),
        ],
        [
            InlineKeyboardButton("Массаж лба — 790р", callback_data=MASSAGE_3),
        ],
        [
            InlineKeyboardButton(
                "Массаж всего лица + клуб — 1490р", callback_data=MASSAGE_4
            ),
        ],
    ]

    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text(SUBSCRIPTION_DESCRIPTION_MSG),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    """TODO create job in 1 hour"""

    return SUBSCRIPTIONS


async def subscriptions_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user_id = update._effective_user.id

    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.effective_message.message_id,
    )

    """TODO add payment"""

    if int(query.data) == MASSAGE_1:
        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url="https://www.notion.so/51287ed9579b405da2640f30dd4669cb?pvs=21",
                ),
            ],
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(DESCRIPTION_1_MSG),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    elif int(query.data) == MASSAGE_2:
        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url="https://www.notion.so/51287ed9579b405da2640f30dd4669cb?pvs=21",
                ),
            ],
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(DESCRIPTION_2_MSG),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    elif int(query.data) == MASSAGE_3:
        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url="https://www.notion.so/51287ed9579b405da2640f30dd4669cb?pvs=21",
                ),
            ],
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(DESCRIPTION_3_MSG),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    elif int(query.data) == MASSAGE_4:
        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url="https://www.notion.so/51287ed9579b405da2640f30dd4669cb?pvs=21",
                ),
            ],
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(DESCRIPTION_4_MSG),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
