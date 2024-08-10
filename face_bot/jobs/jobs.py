from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
)

from telegram.constants import ParseMode

from face_bot.jobs.times import CASES_TIME

from face_bot.utils.escape_text import escape_text

from face_bot.static.texts import CASE_MESSAGE, EXPRESS_YOUNG_MESSAGE


async def show_cases_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    with open("face_bot/img/case_img.jpg", "rb") as f:
        await context.bot.send_photo(
            chat_id=job.chat_id,
            photo=f,
            caption=escape_text(CASE_MESSAGE),
            parse_mode=ParseMode.MARKDOWN_V2,
        )


async def young_guide_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    keyboard = [
        [
            InlineKeyboardButton(
                "Посмотреть",
                url="https://www.notion.so/51287ed9579b405da2640f30dd4669cb?pvs=21",
            ),
        ],
    ]

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=escape_text(EXPRESS_YOUNG_MESSAGE),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
