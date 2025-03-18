import os

import uuid

from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

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
)

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import save_name, get_subscriptions

from face_bot.jobs.jobs import pay_confirmation_job, show_shop
from face_bot.jobs.id_jobs import CONFIRMATION_JOB_ID, SHOW_SHOP
from face_bot.jobs.times import CONFIRMATION_JOB_TIME, SHOW_SHOP_TIME

from yookassa import Configuration, Payment

from face_bot.utils.logger import logger
from face_bot.utils.error_handler import error_handler
from face_bot.utils.session_manager import SessionManager
from face_bot.static.config import NAME_REGEX, ADMINS, GROUP_ID


async def show_subscriptions(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id

    subs_type = await get_subscriptions(user_id)

    keyboard = []
    msg = SUBSCRIPTION_DESCRIPTION_MSG

    """Показывает список доступных подписок"""
    n = 1
    # Посмотреть 4й тип подписки
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

    query = update.callback_query

    if query:
        await query.answer()
        if query.data == "back":
            await query.edit_message_text(
                text=escape_text(msg),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=escape_text(msg),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    return SUBSCRIPTIONS

    # else:
    #     if (
    #         "already_entered" in context.user_data
    #         and context.user_data["already_entered"]
    #     ):
    #         await context.bot.send_message(
    #             chat_id=chat_id,
    #             text=escape_text(
    #                 "Благодарю Вас за проявленный интерес! Обязательно сообщу Вам, когда появятся новые уроки)"
    #             ),
    #             reply_markup=InlineKeyboardMarkup(keyboard),
    #             parse_mode=ParseMode.MARKDOWN_V2,
    #         )

    #         return SUBSCRIPTIONS

    #     else:
    #         context.user_data["already_entered"] = True

    #         await context.bot.send_message(
    #             chat_id=chat_id,
    #             text="Как Вас зовут?",
    #         )

    #         return NAME


async def subscriptions_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

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

    return SUBSCRIPTIONS


async def pay_massage_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    pay_num = int(query.data.split("_")[2])

    url, payment_id = await send_pay_request(
        amount=GOODS_INFO[pay_num]["price"],
        description=GOODS_INFO[pay_num]["check_title"],
    )
    context.user_data[PAYMENT_ID] = payment_id
    context.user_data[SUBSCRIPTION_TYPE] = "1"

    keyboard = [
        [
            InlineKeyboardButton("Оплатить", url=url),
        ],
        [InlineKeyboardButton("Назад", callback_data=f"backpay_{pay_num}")],
    ]

    await context.bot.send_message(
        chat_id=user_id,
        text=escape_text(GOODS_INFO[pay_num]["text_pay"]),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    "run a lot of jobs"
    for i in range(30):
        context.job_queue.run_once(
            pay_confirmation_job,
            CONFIRMATION_JOB_TIME * i,
            chat_id=user_id,
            name=f"{user_id}-{CONFIRMATION_JOB_ID}-{i}",
            data={
                PAYMENT_ID: context.user_data[PAYMENT_ID],
                SUBSCRIPTION_TYPE: context.user_data[SUBSCRIPTION_TYPE],
                FIRST_MSG: context.user_data[GROUP_MESSAGE][FIRST_MSG]
                if (GROUP_MESSAGE in context.user_data)
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


# async def subscriptions_callback2(
#     update: Update, context: ContextTypes.DEFAULT_TYPE
# ) -> int:
#     if int(query.data) == WATCH_ANOTHER:
#         return await show_subscriptions(update, context)

#     elif int(query.data) == ENROLL:
#         await context.bot.send_message(
#             chat_id=chat_id,
#             text="Как Вас зовут?",
#         )

#         return NAME

#     elif int(query.data) == PAY_MASSAGE_1:
#         url, payment_id = await send_pay_request(
#             amount=490, description="Поднимите мне веки"
#         )

#         context.user_data[PAYMENT_ID] = payment_id
#         context.user_data[SUBSCRIPTION_TYPE] = "1"

#         # context.user_data[URL_TO_DELETE] = url

#         "run a lot of jobs"
#         for i in range(30):
#             context.job_queue.run_once(
#                 pay_confirmation_job,
#                 CONFIRMATION_JOB_TIME * i,
#                 chat_id=chat_id,
#                 name=f"{chat_id}-{CONFIRMATION_JOB_ID}-{i}",
#                 data={
#                     PAYMENT_ID: context.user_data[PAYMENT_ID],
#                     SUBSCRIPTION_TYPE: context.user_data[SUBSCRIPTION_TYPE],
#                     FIRST_MSG: context.user_data[GROUP_MESSAGE][FIRST_MSG]
#                     if (GROUP_MESSAGE in context.user_data)
#                     else "",
#                     "user_name": update.effective_user.name,
#                     "chat_id": update.effective_chat.id,
#                     "user_id": update.effective_user.id,
#                 },
#             )

#         """show shop"""
#         context.job_queue.run_once(
#             show_shop,
#             SHOW_SHOP_TIME,
#             chat_id=chat_id,
#             name=f"{chat_id}-{SHOW_SHOP}",
#         )

#     elif int(query.data) == PAY_MASSAGE_2:
#         url, payment_id = await send_pay_request(
#             amount=1290, description="Гладкий лоб"
#         )

#         context.user_data[PAYMENT_ID] = payment_id
#         context.user_data[SUBSCRIPTION_TYPE] = "2"

#         keyboard = [
#             [
#                 InlineKeyboardButton("Оплатить", url=url),
#             ],
#         ]

#         await context.bot.send_message(
#             chat_id=chat_id,
#             text=escape_text("""
# Спасибо, что выбрали урок *«Гладкий лоб» за 18 минут*
# Стоимость: 1290 рублей
# Ссылка действительна в течение 10 минут"""),
#             reply_markup=InlineKeyboardMarkup(keyboard),
#             parse_mode=ParseMode.MARKDOWN_V2,
#         )

#         "run a lot of jobs"
#         for i in range(30):
#             context.job_queue.run_once(
#                 pay_confirmation_job,
#                 CONFIRMATION_JOB_TIME * i,
#                 chat_id=chat_id,
#                 name=f"{chat_id}-{CONFIRMATION_JOB_ID}-{i}",
#                 data={
#                     PAYMENT_ID: context.user_data[PAYMENT_ID],
#                     SUBSCRIPTION_TYPE: context.user_data[SUBSCRIPTION_TYPE],
#                     FIRST_MSG: context.user_data[GROUP_MESSAGE][FIRST_MSG]
#                     if (GROUP_MESSAGE in context.user_data)
#                     else "",
#                     "user_name": update.effective_user.name,
#                     "chat_id": update.effective_chat.id,
#                     "user_id": update.effective_user.id,
#                 },
#             )

#         """show shop"""
#         context.job_queue.run_once(
#             show_shop,
#             SHOW_SHOP_TIME,
#             chat_id=chat_id,
#             name=f"{chat_id}-{SHOW_SHOP}",
#         )

#     elif int(query.data) == PAY_MASSAGE_3:
#         url, payment_id = await send_pay_request(
#             amount=1890, description="АНТИ-ОТЕК"
#         )

#         context.user_data[PAYMENT_ID] = payment_id
#         context.user_data[SUBSCRIPTION_TYPE] = "3"

#         keyboard = [
#             [
#                 InlineKeyboardButton("Оплатить", url=url),
#             ],
#         ]

#         await context.bot.send_message(
#             chat_id=chat_id,
#             text=escape_text("""
# Спасибо, что выбрали урок *Комплекс «АНТИ-ОТЕК»* 
# Стоимость: 1890 рублей
# Ссылка действительна в течение 10 минут"""),
#             reply_markup=InlineKeyboardMarkup(keyboard),
#             parse_mode=ParseMode.MARKDOWN_V2,
#         )

#         "run a lot of jobs"
#         for i in range(30):
#             context.job_queue.run_once(
#                 pay_confirmation_job,
#                 CONFIRMATION_JOB_TIME * i,
#                 chat_id=chat_id,
#                 name=f"{chat_id}-{CONFIRMATION_JOB_ID}-{i}",
#                 data={
#                     PAYMENT_ID: context.user_data[PAYMENT_ID],
#                     SUBSCRIPTION_TYPE: context.user_data[SUBSCRIPTION_TYPE],
#                     FIRST_MSG: context.user_data[GROUP_MESSAGE][FIRST_MSG]
#                     if (GROUP_MESSAGE in context.user_data)
#                     else "",
#                     "user_name": update.effective_user.name,
#                     "chat_id": update.effective_chat.id,
#                     "user_id": update.effective_user.id,
#                 },
#             )

#         """show shop"""
#         context.job_queue.run_once(
#             show_shop,
#             SHOW_SHOP_TIME,
#             chat_id=chat_id,
#             name=f"{chat_id}-{SHOW_SHOP}",
#         )

#     elif int(query.data) == PAY_MASSAGE_4:
#         url, payment_id = await send_pay_request(
#             amount=1990, description="ЭКСПРЕСС-ОМОЛОЖЕНИЕ"
#         )

#         context.user_data[PAYMENT_ID] = payment_id
#         context.user_data[SUBSCRIPTION_TYPE] = "4"

#         keyboard = [
#             [
#                 InlineKeyboardButton("Оплатить", url=url),
#             ],
#         ]

#         await context.bot.send_message(
#             chat_id=chat_id,
#             text=escape_text("""
# Спасибо, что выбрали урок *Комплекс 3-в-1 «ЭКСПРЕСС-ОМОЛОЖЕНИЕ»*
# Стоимость: 1890 рублей
# Ссылка действительна в течение 10 минут"""),
#             reply_markup=InlineKeyboardMarkup(keyboard),
#             parse_mode=ParseMode.MARKDOWN_V2,
#         )

#         """run a lot of jobs"""
#         for i in range(30):
#             context.job_queue.run_once(
#                 pay_confirmation_job,
#                 CONFIRMATION_JOB_TIME * i,
#                 chat_id=chat_id,
#                 name=f"{chat_id}-{CONFIRMATION_JOB_ID}-{i}",
#                 data={
#                     PAYMENT_ID: context.user_data[PAYMENT_ID],
#                     SUBSCRIPTION_TYPE: context.user_data[SUBSCRIPTION_TYPE],
#                     FIRST_MSG: context.user_data[GROUP_MESSAGE][FIRST_MSG]
#                     if (GROUP_MESSAGE in context.user_data)
#                     else "",
#                     "user_name": update.effective_user.name,
#                     "chat_id": update.effective_chat.id,
#                     "user_id": update.effective_user.id,
#                 },
#             )

#         """show shop"""
#         context.job_queue.run_once(
#             show_shop,
#             SHOW_SHOP_TIME,
#             chat_id=chat_id,
#             name=f"{chat_id}-{SHOW_SHOP}",
#         )

#     return SUBSCRIPTIONS


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
):
    # TODO: add logging
    # TODO: add error handling
    # TODO: Сюда инфу для чеков
    try:
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
            },
            uuid.uuid4(),
        )

        confirmation_url = payment.confirmation.confirmation_url

        return confirmation_url, payment.id

    except Exception as e:
        print(e)
