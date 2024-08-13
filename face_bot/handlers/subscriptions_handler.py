import os

from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice

from face_bot.static.keys import (
    GROUP_MESSAGE,
    FIRST_MSG,
)

from face_bot.static.states import NAME, SUBSCRIPTIONS
from face_bot.static.callbacks import MASSAGE_1, MASSAGE_2, MASSAGE_3, MASSAGE_4, ENROLL
from face_bot.static.ids import GROUP_ID
from face_bot.static.keys import SUBSCRIPTION_TYPE

from face_bot.static.texts import (
    SUBSCRIPTION_DESCRIPTION_MSG,
    DESCRIPTION_1_MSG,
    DESCRIPTION_2_MSG,
    DESCRIPTION_3_MSG,
    DESCRIPTION_4_MSG,
    FEEDBACK_NAME_MSG,
    SEND_NAME_MSG,
)

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import save_name

from face_bot.jobs.jobs import dont_buy_job
from face_bot.jobs.id_jobs import DONT_BUY_JOB_ID
from face_bot.jobs.times import DONT_BUY_JOB_TIME


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

    """
    create job in 1 hour & TODO kill if buy
    """
    context.job_queue.run_once(
        dont_buy_job,
        DONT_BUY_JOB_TIME,
        chat_id=user_id,
        name=f"{user_id}-{DONT_BUY_JOB_ID}",
    )

    return SUBSCRIPTIONS


async def subscriptions_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id

    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.effective_message.message_id,
    )

    """TODO add payment"""

    if int(query.data) == ENROLL:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Как Вас зовут?",
        )

        return NAME

    elif int(query.data) == MASSAGE_1:
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
        """push subscription into context"""
        context.user_data[SUBSCRIPTION_TYPE] = "4"

        await context.bot.send_invoice(
            chat_id=chat_id,
            title="Массаж лица",
            description=DESCRIPTION_4_MSG,
            payload="Custom-Payload",
            provider_token=os.getenv("PROVIDER_TOKEN"),
            currency="RUB",
            prices=[LabeledPrice("Массаж лица", 1790 * 100)],
        )

        return SUBSCRIPTIONS


async def successful_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.message.reply_text("Спасибо за оплату!")
    await update.message.reply_text(
        f"Вы приобрели - {context.user_data[SUBSCRIPTION_TYPE]}"
    )

    """TODO Save into DB"""


async def send_warning_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text(
            "*Неверный формат имени.* Имя *не может* содержать __цифры и иные специальные символы__"
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    name = update.effective_message.text

    """send user name to the group"""
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=escape_text(SEND_NAME_MSG),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    if "@" in update.effective_user.name:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"{update.effective_user.name} - {name}",
        )

    else:
        await context.bot.forwardMessage(
            chat_id=GROUP_ID,
            from_chat_id=chat_id,
            message_id=context.user_data[GROUP_MESSAGE][FIRST_MSG],
        )

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=name,
        )

    await save_name(user_id=user_id, name=name)

    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text(FEEDBACK_NAME_MSG),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    """TODO set up periodic jobs"""
