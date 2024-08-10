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

from face_bot.static.texts import CASE_MESSAGE


async def show_cases_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    with open("face_bot/img/case_img.jpg", "rb") as f:
        await context.bot.send_photo(
            chat_id=job.chat_id,
            photo=f,
            caption=escape_text(CASE_MESSAGE),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
