import os
from dotenv import load_dotenv

import uuid

from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from face_bot.static.keys import GROUP_MESSAGE, FIRST_MSG

from face_bot.static.states import NAME, SUBSCRIPTIONS
from face_bot.static.callbacks import (
    MASSAGE_1,
    MASSAGE_2,
    MASSAGE_3,
    MASSAGE_4,
    ENROLL,
    WATCH_ANOTHER,
    PAY_MASSAGE_1,
    PAY_MASSAGE_2,
    PAY_MASSAGE_3,
    PAY_MASSAGE_4,
)

from face_bot.static.keys import PAYMENT_ID, SUBSCRIPTION_TYPE

from face_bot.static.texts import (
    SUBSCRIPTION_DESCRIPTION_MSG,
    DESCRIPTION_1_MSG,
    DESCRIPTION_2_MSG,
    DESCRIPTION_3_MSG,
    DESCRIPTION_4_MSG,
    FEEDBACK_NAME_MSG,
    SEND_NAME_MSG,
    WATCH_ANOTHER_MSG,
    GOODS_INFO,
    YOU_BOUGHT_ALL,
    ABOUT_CLUB_MSG,
)

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import (
    save_name,
    get_subscriptions,
    get_phone_number_by_id,
    save_email,
    get_email
)

from face_bot.jobs.jobs import pay_confirmation_job, show_shop, send_case_job, remove_all_jobs
from face_bot.jobs.id_jobs import CONFIRMATION_JOB_ID, SHOW_SHOP
from face_bot.jobs.times import CONFIRMATION_JOB_TIME, SHOW_SHOP_TIME, CASES_TIME

from yookassa import Configuration, Payment

from face_bot.utils.logger import logger, log_user_action, log_payment, log_error
from face_bot.utils.error_handler import error_handler
from face_bot.utils.session_manager import SessionManager
from face_bot.static.config import NAME_REGEX, ADMINS, GROUP_ID

load_dotenv()


async def show_subscriptions(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    log_user_action(user_id, "show_subscriptions")

    subs_type = await get_subscriptions(user_id)
    log_user_action(user_id, "get_subscriptions", subs_type=subs_type)
        

    keyboard = []
    msg = SUBSCRIPTION_DESCRIPTION_MSG

    """Показывает список доступных подписок"""
    if 4 in subs_type or subs_type == [1, 2, 3]:
        await context.bot.send_message(
            chat_id=user_id,
            text=YOU_BOUGHT_ALL,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )
        return SUBSCRIPTIONS
    n = 1
    for num, info in GOODS_INFO.items():
        if num not in subs_type:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        info["name"],
                        callback_data=info["callback_data"],
                    ),
                ]
            )
            msg += f"\n{n}. {info['description']}"
            n += 1
    msg += "\n\n" + ABOUT_CLUB_MSG

    query = update.callback_query

    if query:
        await query.answer()
        if query.data == "back":
            await query.edit_message_text(
                text=escape_text(msg),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
            return SUBSCRIPTIONS

    if not subs_type:
        shop_keyboard = ReplyKeyboardMarkup(
            [
                [KeyboardButton("🛒 Магазин")],
            ],
            resize_keyboard=True
        )
        message = await context.bot.send_message(
            chat_id=user_id,
            text="Загружаю товары...",
            reply_markup=shop_keyboard,
        )
       
    await context.bot.send_message(
        chat_id=user_id,
        text=escape_text(msg),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    await send_case_job(context, CASES_TIME, user_id)
    return SUBSCRIPTIONS


async def subscriptions_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    user_id = update.effective_user.id
    log_user_action(user_id, "subscriptions_callback", callback_data=query.data)

    await query.answer()

    # Удаляем предыдущие задачи, если они есть
    await remove_all_jobs(user_id, context)
    
    num_massage = int(query.data.split("_")[1])
    text = GOODS_INFO[num_massage]["text"]
    keyboard = [
        [
            InlineKeyboardButton(
                "Купить", callback_data=f"PAY_MASSAGE_{num_massage}"
            )
        ],
        [InlineKeyboardButton("Назад", callback_data="back")],
    ]

    await query.edit_message_text(
        text=escape_text(text),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    await send_case_job(context, CASES_TIME, user_id)
    return SUBSCRIPTIONS


async def pay_massage_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user_id = update.effective_user.id
    if not update.callback_query:
        email = update.effective_message.text
        pay_num = context.user_data["pay_num"]
        await save_email(user_id, email)
    else:
        query = update.callback_query
        pay_num = int(query.data.split("_")[2])
        
    log_user_action(user_id, "pay_massage_callback", subscription_type=pay_num)

    try:
        url, payment_id = await send_pay_request(
            amount=GOODS_INFO[pay_num]["price"],
            description=GOODS_INFO[pay_num]["check_title"],
            context=context,
        )
        log_payment(user_id, payment_id, GOODS_INFO[pay_num]["price"], "created")
        
        context.user_data["payment_id"] = payment_id
        context.user_data["subscription_bought"] = pay_num

        keyboard = [
            [
                InlineKeyboardButton("Оплатить", url=url),
            ],
            [InlineKeyboardButton("Назад", callback_data="back")],
        ]

        await context.bot.send_message(
            chat_id=user_id,
            text=escape_text(GOODS_INFO[pay_num]["text_pay"]),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        "run a lot of jobs"
        for i in range(30):
            print(f"run job {i}" + f"{user_id}-{CONFIRMATION_JOB_ID}-{i}")
            context.job_queue.run_once(
                pay_confirmation_job,
                CONFIRMATION_JOB_TIME * i,
                chat_id=user_id,
                name=f"{user_id}-{CONFIRMATION_JOB_ID}-{i}",
                data={
                    "payment_id": context.user_data["payment_id"],
                    "subscription_bought": context.user_data[
                        "subscription_bought"
                    ],
                    "1st_msg": context.user_data["group_msg"]["1st_msg"]
                    if ("group_msg" in context.user_data)
                    else "",
                    "user_name": update.effective_user.name,
                    "chat_id": update.effective_chat.id,
                    "user_id": update.effective_user.id,
                },
            )

            """show shop"""
            context.job_queue.run_once(
                show_shop,
                SHOW_SHOP_TIME,
                chat_id=user_id,
                name=f"{user_id}-{SHOW_SHOP}",
            )

        return SUBSCRIPTIONS

    except Exception as e:
        log_error(e, user_id, subscription_type=pay_num)
        raise


@error_handler
async def send_warning_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Warning about wrong name format."""
    user_id = update.effective_user.id

    # Обновление времени последней активности пользователя
    SessionManager.update_user_activity(context, user_id)

    logger.warning(f"Пользователь {user_id} отправил имя в неверном формате")

    await update.message.reply_text(
        "Пожалуйста, введите корректное имя. Используйте только буквы, дефис, апостроф и пробелы. Длина имени от 2 до 50 символов."
    )
    return NAME


@error_handler
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get name from user and save it."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    name = update.message.text

    # Обновление времени последней активности пользователя
    SessionManager.update_user_activity(context, user_id)

    logger.info(f"Получено имя от пользователя {user_id}: {name}")

    # Сохраняем имя в контексте
    context.user_data["name"] = name

    # """send user name to the group"""
    # await context.bot.send_message(
    #     chat_id=GROUP_ID,
    #     text=escape_text(SEND_NAME_MSG),
    #     parse_mode=ParseMode.MARKDOWN_V2,
    # )

    # if "@" in update.effective_user.name:
    #     await context.bot.send_message(
    #         chat_id=GROUP_ID,
    #         text=f"{update.effective_user.name} - {name}",
    #     )

    # else:
    #     await context.bot.forwardMessage(
    #         chat_id=GROUP_ID,
    #         from_chat_id=chat_id,
    #         message_id=context.user_data[GROUP_MESSAGE][FIRST_MSG],
    #     )

    #     await context.bot.send_message(
    #         chat_id=GROUP_ID,
    #         text=name,
    #     )

    await save_name(user_id=user_id, name=name)

    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text(FEEDBACK_NAME_MSG),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    return await show_subscriptions(update, context)


async def send_pay_request(
    amount: int,
    description: str,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = context.user_data["user_id"]
    log_user_action(user_id, "send_pay_request", amount=amount, description=description)
    if context.user_data.get("email"):
        email = context.user_data["email"]
    else:
        email = await get_email(user_id)
    try:
        if os.getenv("DEV") == 'True':
            Configuration.account_id = os.getenv("ACCOUNT_ID_DEV")
            Configuration.secret_key = os.getenv("SECRET_KEY_DEV")
        else:
            Configuration.account_id = os.getenv("ACCOUNT_ID")
            Configuration.secret_key = os.getenv("SECRET_KEY")
        payment = Payment.create(
            {
                "amount": {
                    "value": f"{amount}.00",
                    "currency": "RUB",
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://t.me/beautyfacegym_bot",
                },
                "capture": True,
                "description": description,
                "receipt": {
                    "customer": {"email": f"{email}"},
                    "items": [
                        {
                            "description": description,
                            "quantity": 1.000,
                            "amount": {
                                "value": f"{amount}.00",
                                "currency": "RUB",
                            },
                            "vat_code": 1,
                            "payment_subject": "commodity",
                            "payment_mode": "full_payment",
                        }
                    ],
                },
            },
            str(uuid.uuid4()),
        )
        
        confirmation_url = payment.confirmation.confirmation_url

        log_payment(user_id, payment.id, amount, "created", payment_url=confirmation_url)
        return confirmation_url, payment.id

    except Exception as e:
        log_error(e, user_id, amount=amount, description=description)
        raise
