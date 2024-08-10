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
from face_bot.static.texts import CONTACT_MESSAGE

from face_bot.utils.escape_text import escape_text


async def user_progrev_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user_id = update._effective_user.id

    if int(query.data) == LEARN_HOW:
        """TODO send video"""

        """TODO create job"""

        keyboard = [[KeyboardButton("Отправить контакт", request_contact=True)]]

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(CONTACT_MESSAGE),
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                one_time_keyboard=True,
                resize_keyboard=True,
            ),
        )

        return PHONE

    else:
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.effective_message.message_id,
        )
