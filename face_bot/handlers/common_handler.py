from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)

from face_bot.static.ids import ADMINS
from face_bot.static.states import ADMIN_COMMANDS, PROGREV_MESSAGES, PHONE
from face_bot.static.callbacks import (
    CONVERSIONS,
    LEADER_BOARD,
    MAIL,
    LEARN_HOW,
)
from face_bot.static.keys import GROUP_MESSAGE, FIRST_MSG, CURRENT_CASE
from face_bot.static.texts import (
    FIRST_PROGREV_MESSAGE,
    SEND_CONTACT_GROUP_MSG,
)
from face_bot.static.ids import GROUP_ID

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import register, save_phone

from face_bot.handlers.subscriptions_handler import show_subscriptions

from face_bot.jobs.jobs import (
    young_guide_job,
    already_try_job,
    remove_job_if_exists,
    send_case_job,
)
from face_bot.jobs.id_jobs import YOUNG_JOB_ID, ALREADY_TRY_JOB_ID, CASE_JOB_ID
from face_bot.jobs.times import YOUNG_GUIDE_TIME, ALREADY_TRY_JOB_TIME, CASES_TIME


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id in ADMINS:
        """open admin panel"""

        keyboard = [
            [
                InlineKeyboardButton("Конверсии", callback_data=CONVERSIONS),
                InlineKeyboardButton(
                    "Список Пользователей", callback_data=LEADER_BOARD
                ),
            ],
            [
                InlineKeyboardButton("Отправить рассылку", callback_data=MAIL),
            ],
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text("Hey! You are in *Admin Panel*"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        return ADMIN_COMMANDS

    elif len(context.args) == 0 or context.args[0] == "1":
        """Default user"""

        keyboard = [
            [
                InlineKeyboardButton("Узнать", callback_data=LEARN_HOW),
            ],
        ]

        with open("face_bot/img/face.jpeg", "rb") as f:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=f,
                caption=escape_text(FIRST_PROGREV_MESSAGE),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN_V2,
            )

        """ save if user doesn't have username """
        context.user_data[GROUP_MESSAGE] = {
            FIRST_MSG: update.effective_message.id,
        }

        """ Register User """
        await register(
            user_id=user_id,
            name=f"{update.effective_user.first_name} {update.effective_user.last_name}",
        )

        return PROGREV_MESSAGES

    else:
        return await show_subscriptions(update, context)


async def send_warning_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text(
            "*Неверный формат номера. Пришлите номер в формате __79998765432__* или нажмите на кнопку снизу ⬇️"
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if update.effective_message.contact:
        phone_number = f"{update.effective_message.contact.phone_number}"
    elif update.effective_message.text:
        phone_number = f"{update.effective_message.text}"

    await save_phone(user_id=user_id, phone_number=phone_number)

    """send user to group"""
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=SEND_CONTACT_GROUP_MSG,
    )

    if "@" in update.effective_user.name:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=update.effective_user.name,
        )

    else:
        await context.bot.forwardMessage(
            chat_id=GROUP_ID,
            from_chat_id=chat_id,
            message_id=context.user_data[GROUP_MESSAGE][FIRST_MSG],
        )

    """delete job БОЛЬНОЕ СООБЩЕНИЕ - 1"""
    remove_job_if_exists(name=f"{user_id}-{CASE_JOB_ID}-1", context=context)

    """send free movie"""
    # with open("face_bot/video/free.MP4", "rb") as f:
    #     await context.bot.send_message(
    #         chat_id=chat_id,
    #         text="send video",
    #     )

    # send video

    # await context.bot.send_video(
    #     chat_id=chat_id,
    #     video=f,
    #     caption=escape_text(VIDEO_CAPTION),
    #     parse_mode=ParseMode.MARKDOWN_V2,
    #     reply_markup=ReplyKeyboardRemove(),
    #     read_timeout=60,
    #     write_timeout=60,
    # )

    # await context.bot.send_document(
    #     chat_id=chat_id,
    #     document=f,
    #     caption=escape_text(VIDEO_CAPTION),
    #     parse_mode=ParseMode.MARKDOWN_V2,
    #     read_timeout=60,
    #     write_timeout=60,
    # )

    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text("Спасибо ❤"),
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN_V2,
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
        text=escape_text("Смотрите видео на удобной для Вас площадке"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    # await context.bot.send_message(
    #     chat_id=chat_id,
    #     text="отправляется 'ПРИЕМЫ ДОПОЛНЯЮТ' через 10 секунд (10 минут в релизе)",
    # )

    """create job with ПРИЕМЫ ДОПОЛНЯЮТ"""
    context.job_queue.run_once(
        young_guide_job,
        YOUNG_GUIDE_TIME,
        chat_id=user_id,
        name=f"{user_id}-{YOUNG_JOB_ID}",
    )

    # await context.bot.send_message(
    #     chat_id=chat_id,
    #     text="отправляется вопрос 'попробовала?' через 15 секунд (15 минут в релизе)",
    # )

    """create job already try"""
    context.job_queue.run_once(
        already_try_job,
        ALREADY_TRY_JOB_TIME,
        chat_id=user_id,
        name=f"{user_id}-{ALREADY_TRY_JOB_ID}",
    )

    """send БОЛЬНОЕ СООБЩЕНИЕ - 2"""

    # await context.bot.send_message(
    #     chat_id=chat_id,
    #     text="отправляется кейс через 60 секунд (60 минут в релизе)",
    # )

    context.job_queue.run_once(
        send_case_job,
        CASES_TIME * 4,
        chat_id=user_id,
        name=f"{user_id}-{CASE_JOB_ID}-2",
        data={CURRENT_CASE: 2},
    )

    # TODO may be send already try again

    return PROGREV_MESSAGES
