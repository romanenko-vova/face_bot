from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from face_bot.static.states import PHONE
from face_bot.static.callbacks import (
    LEARN_HOW,
)

from face_bot.static.texts import CONTACT_MESSAGE

from face_bot.utils.escape_text import escape_text

from face_bot.jobs.jobs import show_cases_job
from face_bot.jobs.id_jobs import CASE_JOB_ID
from face_bot.jobs.times import CASES_TIME


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

    else:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.effective_message.message_id,
        )
