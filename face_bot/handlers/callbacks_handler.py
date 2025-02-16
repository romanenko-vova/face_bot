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

from face_bot.jobs.jobs import send_case_job, already_try_job, remove_job_if_exists
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
        # with open("face_bot/video/movie_1st.mp4", "rb") as f:
        #     await context.bot.send_video(
        #         chat_id=chat_id,
        #         video=f,
        #         caption=escape_text(VIDEO_CAPTION),
        #         parse_mode=ParseMode.MARKDOWN_V2,
        #     )

        # """TODO send all cases"""
        # for i in range(4):
        #     context.job_queue.run_once(
        #         send_case_job,
        #         CASES_TIME,
        #         chat_id=user_id,
        #         name=f"{user_id}-{CASE_JOB_ID}-{i}",
        #         data={CURRENT_CASE: i},
        #         # data={CURRENT_CASE: await get_current_case(user_id=user_id)},
        #     )

        """send БОЛЬНОЕ СООБЩЕНИЕ - 1"""

        # await context.bot.send_message(
        #     chat_id=chat_id,
        #     text="отправляется кейс через 15 секунд (15 минут в релизе)",
        # )

        context.job_queue.run_once(
            send_case_job,
            CASES_TIME,
            chat_id=user_id,
            name=f"{user_id}-{CASE_JOB_ID}-1",
            data={CURRENT_CASE: 1},
        )

        keyboard = [[KeyboardButton("📱 Отправить контакт", request_contact=True)]]

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

        # remove БОЛЬНОЕ СООБЩЕНИЕ - 2
        remove_job_if_exists(name=f"{user_id}-{CASE_JOB_ID}-2", context=context)

        """change status to 3"""
        await update_status(status=TRY_GUIDE_CONV, user_id=user_id)

        return await show_subscriptions(update, context)

    elif int(query.data) == NO_TRY:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.effective_message.message_id,
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "YouTube",
                    url="https://youtu.be/cOm_aAKFK5Y",
                ),
            ],
            [
                InlineKeyboardButton(
                    "Google Disk",
                    url="https://drive.google.com/file/d/1c7fM94C0jXpd4TBZ4mlYnPSaqxH81V6p/view?usp=drivesdk",
                ),
            ],
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text("*Скорее смотри*"),
            keyboard=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text="отправляется вопрос 'попробовала?' через 15 секунд (15 минут в релизе)",
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
