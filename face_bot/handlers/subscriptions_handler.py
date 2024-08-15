import os

import uuid

from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from face_bot.static.keys import (
    GROUP_MESSAGE,
    FIRST_MSG,
)

from face_bot.static.states import NAME, SUBSCRIPTIONS
from face_bot.static.callbacks import (
    MASSAGE_1,
    MASSAGE_2,
    MASSAGE_3,
    MASSAGE_4,
    ENROLL,
    PAY,
    CONFIRMATION,
)
from face_bot.static.ids import GROUP_ID
from face_bot.static.keys import PAYMENT_ID, SUBSCRIPTION_TYPE

from face_bot.static.texts import (
    SUBSCRIPTION_DESCRIPTION_MSG,
    DESCRIPTION_1_MSG,
    DESCRIPTION_2_MSG,
    DESCRIPTION_3_MSG,
    DESCRIPTION_4_MSG,
    FEEDBACK_NAME_MSG,
    SEND_NAME_MSG,
    SEND_SUBS_GROUP_MSG,
)

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import save_name, save_subscription

from face_bot.jobs.jobs import dont_buy_job, pay_confirmation_job, remove_job_if_exists
from face_bot.jobs.id_jobs import DONT_BUY_JOB_ID, CONFIRMATION_JOB_ID
from face_bot.jobs.times import DONT_BUY_JOB_TIME, CONFIRMATION_JOB_TIME

from yookassa import Configuration, Payment


async def show_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    keyboard = [
        [
            InlineKeyboardButton("Массаж глаз — 490р", callback_data=MASSAGE_1),
        ],
        [
            InlineKeyboardButton("Массаж щек — 590р", callback_data=MASSAGE_2),
        ],
        [
            InlineKeyboardButton("Массаж лба — 790р", callback_data=MASSAGE_3),
        ],
        [
            InlineKeyboardButton("Массаж всего лица — 1490р", callback_data=MASSAGE_4),
        ],
    ]

    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text(SUBSCRIPTION_DESCRIPTION_MSG),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    """
    create job in 1 hour & kill if buy
    """
    context.job_queue.run_once(
        dont_buy_job,
        DONT_BUY_JOB_TIME,
        chat_id=user_id,
        name=f"{user_id}-{DONT_BUY_JOB_ID}",
    )

    return SUBSCRIPTIONS


async def subscriptions_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    await context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.effective_message.message_id,
    )

    if int(query.data) == ENROLL:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Как Вас зовут?",
        )

        return NAME

    elif int(query.data) == MASSAGE_1:
        url, payment_id = await send_pay_request(amount=490, description="Массаж глаз")

        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url=url,
                ),
            ],
        ]

        context.user_data[PAYMENT_ID] = payment_id
        context.user_data[SUBSCRIPTION_TYPE] = "1"

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(DESCRIPTION_1_MSG),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        context.job_queue.run_once(
            pay_confirmation_job,
            CONFIRMATION_JOB_TIME,
            chat_id=chat_id,
            name=f"{chat_id}-{CONFIRMATION_JOB_ID}",
        )

        return SUBSCRIPTIONS

    elif int(query.data) == MASSAGE_2:
        url, payment_id = await send_pay_request(amount=590, description="Массаж щек")

        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url=url,
                ),
            ],
        ]

        context.user_data[PAYMENT_ID] = payment_id
        context.user_data[SUBSCRIPTION_TYPE] = "2"

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(DESCRIPTION_2_MSG),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        context.job_queue.run_once(
            pay_confirmation_job,
            CONFIRMATION_JOB_TIME,
            chat_id=chat_id,
            name=f"{chat_id}-{CONFIRMATION_JOB_ID}",
        )

        return SUBSCRIPTIONS

    elif int(query.data) == MASSAGE_3:
        url, payment_id = await send_pay_request(amount=790, description="Массаж лба")

        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url=url,
                ),
            ],
        ]

        context.user_data[PAYMENT_ID] = payment_id
        context.user_data[SUBSCRIPTION_TYPE] = "3"

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(DESCRIPTION_3_MSG),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        context.job_queue.run_once(
            pay_confirmation_job,
            CONFIRMATION_JOB_TIME,
            chat_id=chat_id,
            name=f"{chat_id}-{CONFIRMATION_JOB_ID}",
        )

        return SUBSCRIPTIONS

    elif int(query.data) == MASSAGE_4:
        url, payment_id = await send_pay_request(
            amount=790, description="Массаж всего лица"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url=url,
                ),
            ],
        ]

        context.user_data[PAYMENT_ID] = payment_id
        context.user_data[SUBSCRIPTION_TYPE] = "4"

        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text(DESCRIPTION_4_MSG),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        context.job_queue.run_once(
            pay_confirmation_job,
            CONFIRMATION_JOB_TIME,
            chat_id=chat_id,
            name=f"{chat_id}-{CONFIRMATION_JOB_ID}",
        )

        return SUBSCRIPTIONS

    elif int(query.data) == CONFIRMATION:
        payment_id = context.user_data[PAYMENT_ID]
        payment = Payment.find_one(payment_id)

        print(int(str(payment.amount.value).split(".")[0]))
        if payment.paid:
            print("PAID")

            subs_type = context.user_data[SUBSCRIPTION_TYPE]

            """delete job dont buy"""
            remove_job_if_exists(name=f"{user_id}-{DONT_BUY_JOB_ID}", context=context)

            """save in db conv_status and subscription"""
            save_subscription(subs=subs_type, user_id=user_id)

            """send video"""
            keyboard = [
                [
                    InlineKeyboardButton(
                        "Смотреть",
                        url="https://www.notion.so/51287ed9579b405da2640f30dd4669cb?pvs=21",
                    ),
                ],
            ]
            await context.bot.send_message(
                chat_id=chat_id,
                text="Вы можете посмотреть видео-массаж по ссылке",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

            """send to group"""
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=SEND_SUBS_GROUP_MSG,
            )

            if "@" in update.effective_user.name:
                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"{update.effective_user.name} - {subs_type}",
                )

            else:
                await context.bot.forwardMessage(
                    chat_id=GROUP_ID,
                    from_chat_id=chat_id,
                    message_id=context.user_data[GROUP_MESSAGE][FIRST_MSG],
                )

                await context.bot.send_message(
                    chat_id=GROUP_ID,
                    text=f"тип подписки - {subs_type}",
                )

            """TODO send job with not full"""

        else:
            keyboard = [
                [InlineKeyboardButton("Проверить еще раз", callback_data=CONFIRMATION)],
            ]

            await context.bot.send_message(
                chat_id=chat_id,
                text="Оплата еще не прошла",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )


async def send_warning_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text(
            "*Неверный формат имени.* Имя *не может* содержать __цифры и иные специальные символы__"
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    name = update.effective_message.text

    """send user name to the group"""
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=escape_text(SEND_NAME_MSG),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    if "@" in update.effective_user.name:
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"{update.effective_user.name} - {name}",
        )

    else:
        await context.bot.forwardMessage(
            chat_id=GROUP_ID,
            from_chat_id=chat_id,
            message_id=context.user_data[GROUP_MESSAGE][FIRST_MSG],
        )

        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=name,
        )

    await save_name(user_id=user_id, name=name)

    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text(FEEDBACK_NAME_MSG),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    """TODO set up periodic jobs"""


async def send_pay_request(
    amount: int,
    description: str,
):
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
