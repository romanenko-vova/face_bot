from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from face_bot.static.ids import ADMINS
from face_bot.static.states import ADMIN_COMMANDS, PROGREV_MESSAGES, PHONE
from face_bot.static.callbacks import (
    CONVERSIONS,
    LEADER_BOARD,
    MAIL,
    LEARN_HOW,
    GET_MAIL,
    YES_MAIL,
    NO_MAIL,
)
from face_bot.static.keys import (
    GROUP_MESSAGE,
    USERNAME,
    FIRST_MSG,
    MESSAGE_MAIL,
)
from face_bot.static.texts import FIRST_PROGREV_MESSAGE, GUIDE_MESSAGE

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import register, save_phone

from face_bot.jobs.jobs import young_guide_job
from face_bot.jobs.id_jobs import YOUNG_JOB_ID
from face_bot.jobs.times import YOUNG_GUIDE_TIME


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

    elif len(context.args) == 0 or context.args[0] == 1:
        """Default user"""

        keyboard = [
            [
                InlineKeyboardButton("Узнать как", callback_data=LEARN_HOW),
            ],
        ]

        with open("face_bot/img/face.jpg", "rb") as f:
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
        """TODO difficult logic"""
        pass


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

    if update.effective_message.contact:
        phone_number = f"{update.effective_message.contact.phone_number}"
    elif update.effective_message.text:
        phone_number = f"{update.effective_message.text}"

    await save_phone(user_id=user_id, phone_number=phone_number)

    """send url with guide"""
    keyboard = [
        [
            InlineKeyboardButton(
                "Чек-лист",
                url="https://www.notion.so/51287ed9579b405da2640f30dd4669cb?pvs=21",
            ),
        ],
    ]

    """create job with express in 1 hour"""
    context.job_queue.run_once(
        young_guide_job,
        YOUNG_GUIDE_TIME,
        chat_id=user_id,
        name=f"{user_id}-{YOUNG_JOB_ID}",
    )

    await context.bot.send_message(
        chat_id=user_id,
        text=escape_text(GUIDE_MESSAGE),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    """TODO create job in 1 hour"""
