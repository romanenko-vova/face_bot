import os

import uuid
import requests

from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from face_bot.static.keys import GROUP_MESSAGE, FIRST_MSG

from face_bot.static.states import NAME, SUBSCRIPTIONS
from face_bot.static.callbacks import (
    MASSAGE_1,
    MASSAGE_2,
    MASSAGE_3,
    ENROLL,
    CONFIRMATION,
    WATCH_ANOTHER,
)
from face_bot.static.ids import GROUP_ID
from face_bot.static.keys import PAYMENT_ID, SUBSCRIPTION_TYPE, URL_TO_DELETE

from face_bot.static.texts import (
    SUBSCRIPTION_DESCRIPTION_MSG,
    DESCRIPTION_1_MSG,
    DESCRIPTION_2_MSG,
    DESCRIPTION_3_MSG,
    FEEDBACK_NAME_MSG,
    SEND_NAME_MSG,
    SEND_SUBS_GROUP_MSG,
    WATCH_ANOTHER_MSG,
)

from face_bot.utils.escape_text import escape_text

from face_bot.database.db import save_name, save_subscription

from face_bot.jobs.jobs import pay_confirmation_job, remove_job_if_exists
from face_bot.jobs.id_jobs import DONT_BUY_JOB_ID, CONFIRMATION_JOB_ID
from face_bot.jobs.times import CONFIRMATION_JOB_TIME

from yookassa import Configuration, Payment


async def show_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    subs_type = 0

    if PAYMENT_ID in context.user_data:
        try:
            id = context.user_data[PAYMENT_ID]
            if id != "-1":
                secret_key = os.getenv("SECRET_KEY")
                account_id = os.getenv("ACCOUNT_ID")

                response = requests.post(
                    f"https://api.yookassa.ru/v3/payments/{id}/cancel",
                    auth=(account_id, secret_key),
                )

                context.user_data[PAYMENT_ID] = "-1"

                print(response)
        except Exception as e:
            print(f"e - {e}")

    if SUBSCRIPTION_TYPE in context.user_data:
        subs_type = int(context.user_data[SUBSCRIPTION_TYPE])

    keyboard = []
    msg = SUBSCRIPTION_DESCRIPTION_MSG

    if subs_type != 1:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "«Экспресс-лифтинг всего лица» — 490р", callback_data=MASSAGE_1
                ),
            ]
        )
        msg += "\n1. Экспресс-лифтинг всего лица за 11 минут"
    if subs_type != 2:
        keyboard.append(
            [
                InlineKeyboardButton("«Гладкий лоб» — 1290р", callback_data=MASSAGE_2),
            ]
        )
        msg += "\n2. «Гладкий лоб» за 18 минут"
    if subs_type != 3:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "Комплекс «АНТИ-ОТЕК» — 1890р", callback_data=MASSAGE_3
                ),
            ]
        )
        msg += "\n3. Комплекс «АНТИ-ОТЕК» - 27 минут упражнений для тела и волшебных приемов для лица"

    await context.bot.send_message(
        chat_id=chat_id,
        text=escape_text(msg),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
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
    if int(query.data) == WATCH_ANOTHER:
        # await query.message.delete()
        context.user_data[SUBSCRIPTION_TYPE] = "-1"
        remove_job_if_exists(name=f"{chat_id}-{CONFIRMATION_JOB_ID}", context=context)

        return await show_subscriptions(update, context)

    elif int(query.data) == ENROLL:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Как Вас зовут?",
        )

        return NAME

    elif int(query.data) == MASSAGE_1:
        url, payment_id = await send_pay_request(
            amount=490, description="Поднимите мне веки"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url=url,
                ),
                InlineKeyboardButton(WATCH_ANOTHER_MSG, callback_data=WATCH_ANOTHER),
            ],
        ]

        """ save message with url to pay for deleting """
        context.user_data[URL_TO_DELETE] = url

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
        url, payment_id = await send_pay_request(amount=1290, description="Гладкий лоб")

        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url=url,
                ),
                InlineKeyboardButton(WATCH_ANOTHER_MSG, callback_data=WATCH_ANOTHER),
            ],
        ]

        """ save message with url to pay for deleting """
        context.user_data[URL_TO_DELETE] = url

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
        url, payment_id = await send_pay_request(
            amount=1890, description="Лицо без отеков"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Оплатить",
                    url=url,
                ),
                InlineKeyboardButton(WATCH_ANOTHER_MSG, callback_data=WATCH_ANOTHER),
            ],
        ]

        """ save message with url to pay for deleting """
        context.user_data[URL_TO_DELETE] = url

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

    elif int(query.data) == CONFIRMATION:
        payment_id = context.user_data[PAYMENT_ID]
        payment = Payment.find_one(payment_id)

        print(int(str(payment.amount.value).split(".")[0]))
        if payment.paid:
            subs_type = context.user_data[SUBSCRIPTION_TYPE]

            """delete job dont buy"""
            remove_job_if_exists(name=f"{user_id}-{DONT_BUY_JOB_ID}", context=context)

            """save in db conv_status and subscription"""
            await save_subscription(subs=subs_type, user_id=user_id)

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

            """send video"""
            if int(subs_type) == 1:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="отправляем 1-ое видео",
                )

                # with open("face_bot/video/movie_1st.mp4", "rb") as f:
                #     await context.bot.send_video(
                #         chat_id=chat_id,
                #         video=f,
                #         caption="Поднимите мне веки",
                #         parse_mode=ParseMode.MARKDOWN_V2,
                #     )

                return await show_subscriptions(update, context)

            elif int(subs_type) == 2:
                # with open("face_bot/video/movie_1st.mp4", "rb") as f:
                #     await context.bot.send_video(
                #         chat_id=chat_id,
                #         video=f,
                #         caption="Гладкий лоб",
                #         parse_mode=ParseMode.MARKDOWN_V2,
                #     )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="отправляем 2-ое видео",
                )

                return await show_subscriptions(update, context)

            elif int(subs_type) == 3:
                # with open("face_bot/video/movie_1st.mp4", "rb") as f:
                #     await context.bot.send_video(
                #         chat_id=chat_id,
                #         video=f,
                #         caption="Анти-отек",
                #         parse_mode=ParseMode.MARKDOWN_V2,
                #     )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="отправляем 3-е видео",
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

    return await show_subscriptions(update, context)


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
