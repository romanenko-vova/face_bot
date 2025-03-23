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
from face_bot.static.keys import CURRENT_CASE
from face_bot.static.callbacks import LEARN_HOW, YES_TRY, NO_TRY
from face_bot.static.conversions import TRY_GUIDE_CONV

from face_bot.static.texts import CONTACT_MESSAGE

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import update_status

from face_bot.handlers.subscriptions_handler import show_subscriptions

from face_bot.jobs.jobs import (
    send_case_job,
    already_try_job,
    remove_job_if_exists,
    remove_all_jobs,
)
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
        await remove_all_jobs(chat_id, context)
        await send_case_job(context, CASES_TIME, user_id)

        keyboard = [
            [KeyboardButton("📱 Отправить контакт", request_contact=True)]
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(CONTACT_MESSAGE),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
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

        await remove_all_jobs(chat_id, context)

        await update_status(status=TRY_GUIDE_CONV, user_id=user_id)
        
        return await show_subscriptions(update, context)


    else:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.effective_message.message_id,
        )
