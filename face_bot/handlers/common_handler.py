from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from datetime import timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)


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
    VIDEO_CAPTION,
    GIFT_MESSAGE,
)
from face_bot.static.config import ADMINS, GROUP_ID

from face_bot.utils.escape_text import escape_text
from face_bot.utils.logger import logger
from face_bot.utils.error_handler import error_handler
from face_bot.utils.session_manager import SessionManager

from face_bot.database.db import register, save_phone, reset_case, get_email

from face_bot.handlers.subscriptions_handler import show_subscriptions, pay_massage_callback

from face_bot.jobs.jobs import (
    young_guide_job,
    young_guide_2_job,
    already_try_job,
    remove_job_if_exists,
    send_case_job,
    send_feedback_job,
    send_video_links_job,
    remove_all_jobs,
)
from face_bot.jobs.id_jobs import YOUNG_JOB_ID, ALREADY_TRY_JOB_ID, CASE_JOB_ID
from face_bot.jobs.times import (
    YOUNG_GUIDE_TIME,
    ALREADY_TRY_JOB_TIME,
    CASES_TIME,
)


@error_handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # После запуска бота обновляем время последней активности пользователя
    SessionManager.update_user_activity(context, user_id)

    logger.info(f"Пользователь {user_id} запустил команду /start")

    await reset_case(user_id)
    context.user_data["user_id"] = user_id

    if user_id in ADMINS:
        """open admin panel"""
        logger.info(f"Администратор {user_id} открыл панель администратора")

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
            text=escape_text("Вы попали в *Панель администратора*"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        return ADMIN_COMMANDS

    elif len(context.args) == 0 or context.args[0] == "1":
        """Обычный пользователь"""

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

        """ сохраняем id сообщения, если пользователь не имеет username """
        context.user_data[GROUP_MESSAGE] = {
            FIRST_MSG: update.effective_message.id,
        }

        """ Регистрация пользователя """
        await register(
            user_id=user_id,
            name=f"{update.effective_user.full_name}",
        )

        await send_case_job(context, CASES_TIME, user_id)
        return PROGREV_MESSAGES
    else:
        return await show_subscriptions(update, context)


@error_handler
async def send_warning_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Предупреждение о неверном формате номера телефона."""
    user_id = update.effective_user.id

    # Обновление времени последней активности пользователя
    SessionManager.update_user_activity(context, user_id)

    logger.warning(
        f"Пользователь {user_id} отправил номер телефона в неверном формате"
    )

    await update.message.reply_text(
        "Пожалуйста, отправьте номер телефона в формате 79XXXXXXXXX или воспользуйтесь кнопкой 'Отправить контакт'"
    )
    return PHONE


@error_handler
async def get_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Обновление времени последней активности пользователя
    SessionManager.update_user_activity(context, user_id)

    logger.info(f"Получен номер телефона от пользователя {user_id}")

    if update.effective_message.contact:
        phone_number = f"{update.effective_message.contact.phone_number}"
    elif update.effective_message.text:
        phone_number = f"{update.effective_message.text}"

    await save_phone(user_id=user_id, phone_number=phone_number)
    context.user_data["phone"] = phone_number
    
    if update.effective_user.username:
        text = f'Пользователь @{update.effective_user.username} — {phone_number} — отправил номер телефона' 
    else:
        text = f'Пользователь {phone_number} — отправил номер телефона'
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=text,
    )

    # Удаляем предыдущие задачи, если они есть
    await remove_all_jobs(chat_id, context)

    # Отправляем "Спасибо"
    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text("Спасибо ❤"),
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    await send_case_job(context, timedelta(seconds=1), user_id, 1)

    await send_feedback_job(context, timedelta(seconds=7), chat_id, 1)

    # Отправляем ссылки на видео
    context.job_queue.run_once(
        send_video_links_job,
        timedelta(seconds=17),
        chat_id=chat_id,
        name=f"{user_id}-send_video_links",
    )
    # Отправляем инструкцию к видео
    context.job_queue.run_once(
        young_guide_job,
        timedelta(seconds=30),
        chat_id=user_id,
        name=f"{user_id}-{YOUNG_JOB_ID}",
    )

    # Отправляем Зиту
    await send_case_job(context, timedelta(seconds=40), user_id, 2)

    # Отправляем все фигня купи курс
    context.job_queue.run_once(
        young_guide_2_job,
        timedelta(seconds=50),
        chat_id=user_id,
        name=f"{user_id}-{YOUNG_JOB_ID}",
    )

    # Отправляем кнопку на магаз
    context.job_queue.run_once(
        already_try_job,
        timedelta(seconds=60),
        chat_id=user_id,
        name=f"{user_id}-{ALREADY_TRY_JOB_ID}",
    )

    # prod
    await send_case_job(context, CASES_TIME, user_id)
    # dev
    # await send_case_job(context, timedelta(seconds=80), user_id)

    return PROGREV_MESSAGES


@error_handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущий диалог и возвращает пользователя в начальное состояние"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} отменил текущий диалог")

    await update.message.reply_text(
        "Действие отменено. Используйте /start, чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


@error_handler
async def error_email(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Обработка ошибки при вводе email"""
    user_id = update.effective_user.id
    logger.error(f"Ошибка при вводе email для пользователя {user_id}")

    await update.message.reply_text(
        "Пожалуйста, введите ваш email в правильном формате",
    )


@error_handler
async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает email у пользователя"""
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запросил email")
    # Удаляем предыдущие задачи, если они есть
    await remove_all_jobs(user_id, context)
    
    query = update.callback_query
    pay_num = int(query.data.split("_")[2])
    if await get_email(user_id) or context.user_data.get("email"):
        await pay_massage_callback(update, context)
    else:
        context.user_data["pay_num"] = pay_num

        await context.bot.send_message(
            chat_id=user_id,
            text="*Пожалуйста\, введите ваш email\. На него придет чек после оплаты*",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
