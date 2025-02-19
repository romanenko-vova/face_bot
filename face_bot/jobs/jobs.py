from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
)

from telegram.constants import ParseMode
from face_bot.static.keys import PAYMENT_ID, SUBSCRIPTION_TYPE, FIRST_MSG
from face_bot.static.ids import GROUP_ID

from face_bot.utils.escape_text import escape_text

from face_bot.static.texts import (
    CASES_MESSAGES,
    EXPRESS_YOUNG_MESSAGE,
    DONT_BUY_MSG,
    SEND_SUBS_GROUP_MSG,
    SUBSCRIPTION_DESCRIPTION_MSG,
)
from face_bot.static.callbacks import (
    YES_TRY,
    NO_TRY,
    ENROLL,
    MASSAGE_1,
    MASSAGE_2,
    MASSAGE_3,
    MASSAGE_4,
)
from face_bot.jobs.id_jobs import CONFIRMATION_JOB_ID, SHOW_SHOP
from face_bot.static.keys import CURRENT_CASE

from face_bot.database.db import update_case, save_subscription

from yookassa import Payment

# async def show_cases_job(context: ContextTypes.DEFAULT_TYPE) -> int:
#     job = context.job

#     with open("face_bot/img/case_img.jpg", "rb") as f:
#         await context.bot.send_photo(
#             chat_id=job.chat_id,
#             photo=f,
#             caption=escape_text(CASE_MESSAGE),
#             parse_mode=ParseMode.MARKDOWN_V2,
#         )


async def send_case_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    with open(f"face_bot/img/case_{job.data[CURRENT_CASE]}.jpg", "rb") as f:
        await context.bot.send_photo(
            chat_id=job.chat_id,
            photo=f,
            caption=escape_text(CASES_MESSAGES[job.data[CURRENT_CASE]]),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    await update_case(job.chat_id)


async def young_guide_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    keyboard = [
        [
            KeyboardButton("🛒 Магазин"),
        ]
    ]

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=EXPRESS_YOUNG_MESSAGE,
        reply_markup=ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def already_try_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    keyboard = [
        [
            InlineKeyboardButton(
                "Да",
                callback_data=YES_TRY,
            ),
        ],
        [
            InlineKeyboardButton(
                "Нет",
                callback_data=NO_TRY,
            ),
        ],
    ]

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=escape_text("Успела попробовать что-нибудь из видео?"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def dont_buy_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    keyboard = [
        [
            InlineKeyboardButton(
                "Записаться",
                callback_data=ENROLL,
            ),
        ],
    ]

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=escape_text(DONT_BUY_MSG),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def pay_confirmation_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job

    payment_id = job.data[PAYMENT_ID]
    payment = Payment.find_one(payment_id)

    user_name = job.data["user_name"]
    chat_id = job.data["chat_id"]
    user_id = job.data["user_id"]
    first_message = job.data[FIRST_MSG]

    if payment.paid:
        await context.bot.send_message(
            chat_id=chat_id,
            text=escape_text("Спасибо за покупку!"),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        subs_type = job.data[SUBSCRIPTION_TYPE]

        """delete all jobs"""
        for i in range(30):
            remove_job_if_exists(
                name=f"{chat_id}-{CONFIRMATION_JOB_ID}-{i}", context=context
            )

        """TODO remove showing shop"""
        remove_job_if_exists(name=f"{chat_id}-{SHOW_SHOP}", context=context)

        """save in db conv_status and subscription"""
        await save_subscription(subs=subs_type, user_id=user_id)

        """send to group"""
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=SEND_SUBS_GROUP_MSG,
        )

        if "@" in user_name:
            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"{user_name} - {subs_type}",
            )
        else:
            await context.bot.forwardMessage(
                chat_id=GROUP_ID,
                from_chat_id=chat_id,
                message_id=first_message,
            )

            await context.bot.send_message(
                chat_id=GROUP_ID,
                text=f"тип подписки - {subs_type}",
            )

        """send video"""
        if int(subs_type) == 1 or int(subs_type) == 4:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "YouTube",
                        url="https://youtu.be/ndkQQETkINQ",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "Google Disk",
                        url="https://drive.google.com/file/d/1-kjFU-4O-UAysVpNz3VYhJ_CDl9e8zkc",
                    ),
                ],
            ]

            await context.bot.send_message(
                chat_id=chat_id,
                text=escape_text(
                    "Смотрите урок *«Экспресс-лифтинг всего лица за 11 минут»* на удобной для Вас площадке"
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN_V2,
            )

        if int(subs_type) == 2 or int(subs_type) == 4:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "YouTube",
                        url="https://youtu.be/Xy1nhTEPO9c",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "Google Disk",
                        url="https://drive.google.com/file/d/1SO0IS6CG8TMLL8MW1ZMgYBBV7NwFyu7C",
                    ),
                ],
            ]

            await context.bot.send_message(
                chat_id=chat_id,
                text=escape_text(
                    "Смотрите урок *«Гладкий лоб» за 18 минут* на удобной для Вас площадке"
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN_V2,
            )

        if int(subs_type) == 3 or int(subs_type) == 4:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "YouTube",
                        url="https://youtu.be/FrUcOn9dCIs",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "Google Disk",
                        url="https://drive.google.com/file/d/1mibR5gzt-pdz7b1RdDS6et4u_eYbDcDE",
                    ),
                ],
            ]

            await context.bot.send_message(
                chat_id=chat_id,
                text=escape_text(
                    "Смотрите урок *Комплекс «АНТИ-ОТЕК» - 27 минут упражнений для тела и волшебных приемов для лица* на удобной для Вас площадке"
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN_V2,
            )

        """send shop"""
        keyboard = []
        msg = SUBSCRIPTION_DESCRIPTION_MSG

        if int(subs_type) != 1 and int(subs_type) != 4:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "«Экспресс-лифтинг всего лица» — 490р", callback_data=MASSAGE_1
                    ),
                ]
            )
            msg += "\n1. Экспресс-лифтинг всего лица за 11 минут"
        if int(subs_type) != 2 and int(subs_type) != 4:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "«Гладкий лоб» — 1290р", callback_data=MASSAGE_2
                    ),
                ]
            )
            msg += "\n2. «Гладкий лоб» за 18 минут"
        if int(subs_type) != 3 and int(subs_type) != 4:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "Комплекс «АНТИ-ОТЕК» — 1890р", callback_data=MASSAGE_3
                    ),
                ]
            )
            msg += "\n3. Комплекс «АНТИ-ОТЕК» - 27 минут упражнений для тела и волшебных приемов для лица"
        if int(subs_type) != 4:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "Комплекс «3 в 1» — 1990р", callback_data=MASSAGE_4
                    ),
                ]
            )
            msg += "\n4. Комплекс «3 в 1»"

            await context.bot.send_message(
                chat_id=job.chat_id,
                text=escape_text(msg),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN_V2,
            )


async def show_shop(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    keyboard = []
    msg = SUBSCRIPTION_DESCRIPTION_MSG

    keyboard.append(
        [
            InlineKeyboardButton(
                "«Экспресс-лифтинг всего лица» — 490р", callback_data=MASSAGE_1
            ),
        ]
    )
    msg += "\n1. Экспресс-лифтинг всего лица за 11 минут"

    keyboard.append(
        [
            InlineKeyboardButton("«Гладкий лоб» — 1290р", callback_data=MASSAGE_2),
        ]
    )
    msg += "\n2. «Гладкий лоб» за 18 минут"

    keyboard.append(
        [
            InlineKeyboardButton(
                "Комплекс «АНТИ-ОТЕК» — 1890р", callback_data=MASSAGE_3
            ),
        ]
    )
    msg += "\n3. Комплекс «АНТИ-ОТЕК» - 27 минут упражнений для тела и волшебных приемов для лица"

    keyboard.append(
        [
            InlineKeyboardButton("Комплекс «3 в 1» — 1990р", callback_data=MASSAGE_4),
        ]
    )
    msg += "\n4. Комплекс «3 в 1»"

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=escape_text(msg),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True
