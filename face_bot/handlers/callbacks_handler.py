from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from face_bot.static.states import PHONE
from face_bot.static.callbacks import LEARN_HOW, YES_TRY, NO_TRY
from face_bot.static.conversions import TRY_GUIDE_CONV

from face_bot.static.texts import CONTACT_MESSAGE, CASE_2_MSG

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import update_status

from face_bot.jobs.jobs import show_cases_job, already_try_job
from face_bot.jobs.id_jobs import CASE_JOB_ID, ALREADY_TRY_JOB_ID
from face_bot.jobs.times import CASES_TIME, ALREADY_TRY_JOB_TIME


async def user_progrev_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user_id = update._effective_user.id

    if int(query.data) == LEARN_HOW:
        """TODO send video"""

        """create job with cases"""
        context.job_queue.run_once(
            show_cases_job,
            CASES_TIME,
            chat_id=user_id,
            name=f"{user_id}-{CASE_JOB_ID}",
        )

        keyboard = [[KeyboardButton("Отправить контакт", request_contact=True)]]

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(CONTACT_MESSAGE),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                one_time_keyboard=True,
                input_field_placeholder="79998765432 или ⬇️",
            ),
        )

        return PHONE

    elif int(query.data) == YES_TRY:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.effective_message.message_id,
        )

        """change status to 3"""
        update_status(status=TRY_GUIDE_CONV, user_id=user_id)

        with open("face_bot/img/case_2.jpg", "rb") as f:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=f,
                caption=escape_text(CASE_2_MSG),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN_V2,
            )

    elif int(query.data) == NO_TRY:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.effective_message.message_id,
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Посмотреть",
                    url="https://www.notion.so/51287ed9579b405da2640f30dd4669cb?pvs=21",
                ),
            ],
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text("*Скорее смотри*"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        context.job_queue.run_once(
            already_try_job,
            ALREADY_TRY_JOB_TIME,
            chat_id=user_id,
            name=f"{user_id}-{ALREADY_TRY_JOB_ID}",
        )

        """TODO start 2"""
        """TODO update admin with 3"""

    else:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.effective_message.message_id,
        )
