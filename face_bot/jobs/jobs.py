from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
)

from telegram.constants import ParseMode

from face_bot.utils.escape_text import escape_text

from face_bot.static.texts import CASES_MESSAGES, EXPRESS_YOUNG_MESSAGE, DONT_BUY_MSG
from face_bot.static.callbacks import YES_TRY, NO_TRY, ENROLL, CONFIRMATION

from face_bot.static.keys import CURRENT_CASE

from face_bot.database.db import update_case

# async def show_cases_job(context: ContextTypes.DEFAULT_TYPE) -> int:
#     job = context.job

#     with open("face_bot/img/case_img.jpg", "rb") as f:
#         await context.bot.send_photo(
#             chat_id=job.chat_id,
#             photo=f,
#             caption=escape_text(CASE_MESSAGE),
#             parse_mode=ParseMode.MARKDOWN_V2,
#         )


async def send_case_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    with open(f"face_bot/img/case_{job.data[CURRENT_CASE]}.jpg", "rb") as f:
        await context.bot.send_photo(
            chat_id=job.chat_id,
            photo=f,
            caption=escape_text(CASES_MESSAGES[job.data[CURRENT_CASE]]),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    await update_case(job.chat_id)


async def young_guide_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=escape_text(EXPRESS_YOUNG_MESSAGE),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def already_try_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    keyboard = [
        [
            InlineKeyboardButton(
                "Да",
                callback_data=YES_TRY,
            ),
        ],
        [
            InlineKeyboardButton(
                "Нет",
                callback_data=NO_TRY,
            ),
        ],
    ]

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=escape_text("Успела попробовать что-нибудь из видео?"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def dont_buy_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    keyboard = [
        [
            InlineKeyboardButton(
                "Записаться",
                callback_data=ENROLL,
            ),
        ],
    ]

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=escape_text(DONT_BUY_MSG),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def pay_confirmation_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job

    keyboard = [
        [InlineKeyboardButton("Проверить", callback_data=CONFIRMATION)],
    ]

    await context.bot.send_message(
        chat_id=job.chat_id,
        text="Проверить оплату?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True
