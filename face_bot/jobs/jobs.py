from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
)

from datetime import timedelta
from telegram.constants import ParseMode
from face_bot.static.keys import PAYMENT_ID, SUBSCRIPTION_TYPE, FIRST_MSG
from face_bot.static.config import GROUP_ID

from face_bot.utils.escape_text import escape_text

from face_bot.static.texts import (
    CASES_MESSAGES,
    EXPRESS_YOUNG_MESSAGE,
    DONT_BUY_MSG,
    SEND_SUBS_GROUP_MSG,
    SUBSCRIPTION_DESCRIPTION_MSG,
    BEFORE_AFTER_RESULTS,
    SUCCESS_STORY,
    GIFT_MESSAGE,
    EXPRESS_YOUNG_MESSAGE_2
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
from face_bot.jobs.id_jobs import CONFIRMATION_JOB_ID, SHOW_SHOP, CASE_JOB_ID
from face_bot.static.keys import CURRENT_CASE

from face_bot.database.db import update_case, save_subscription, get_current_case

from yookassa import Payment

import logging
from datetime import datetime

from face_bot.static.texts import FEEDBACK_TEXTS, BEFORE_AFTER_RESULTS_MSG

logger = logging.getLogger(__name__)


async def case_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job
    cur_case = await get_current_case(job.chat_id)
    case = job.data[CURRENT_CASE]
    if case:
        if case < cur_case:
            return
    else:
        case = cur_case
    with open(f"face_bot/img/case_{case}.jpg", "rb") as f:
        await context.bot.send_photo(
            chat_id=job.chat_id,
            photo=f,
            caption=escape_text(CASES_MESSAGES[case]),
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    await update_case(job.chat_id)

async def send_case_job(context: ContextTypes.DEFAULT_TYPE, time: datetime, chat_id: int, case = None):
    if not case:
        case = 0
    print('Я чет щас запустил', case)
    context.job_queue.run_once(
        case_job,
        time,
        chat_id=chat_id,
        name=f"{chat_id}-{CASE_JOB_ID}-{case}",
        data={CURRENT_CASE: case},
    )
    
async def send_feedback_job(context: ContextTypes.DEFAULT_TYPE, time: datetime, chat_id: int, number:int):
    context.job_queue.run_once(
        feedback_job,
        time,
        chat_id=chat_id,
        data={"number": number},
    )
    

async def feedback_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job
    number_feedback = job.data["number"]
    # Отправляем отзыв клиента
    try:
        with open(
            f"face_bot/img/feedback_{number_feedback}.jpg", "rb"
        ) as photo:
            await context.bot.send_photo(
                chat_id=job.chat_id,
                photo=photo,
                caption=escape_text(f"{FEEDBACK_TEXTS[number_feedback]}"),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
    except Exception as e:
        logger.error(f"Не удалось отправить отзыв (feedback_{number_feedback}): {str(e)}")

async def young_guide_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=EXPRESS_YOUNG_MESSAGE,
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )
    
async def young_guide_2_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    keyboard = [
        [
            KeyboardButton("🛒 Магазин"),
        ]
    ]

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=EXPRESS_YOUNG_MESSAGE_2,
        reply_markup=ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
    )
    
async def send_video_links_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.chat_id
    
    # Отправляем ссылки на видео
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
        text=escape_text(GIFT_MESSAGE),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def already_try_job(context: ContextTypes.DEFAULT_TYPE) -> int:
    job = context.job

    keyboard = [
        [
            InlineKeyboardButton(
                "Да, конечно 😊",
                callback_data=YES_TRY,
            ),
        ],
        [
            InlineKeyboardButton(
                "Пока нет, но собираюсь 🤔",
                callback_data=NO_TRY,
            ),
        ],
    ]

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=escape_text("*Готовы вдохнуть в свое лицо молодость?* ✨🌱💫"),
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
                        "«Экспресс-лифтинг всего лица» — 490р",
                        callback_data=MASSAGE_1,
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

    
    await context.job_queue.run_once(
        send_feedback_job,
        when=timedelta(seconds=10),
        data={"number": 5},
    )

    # Отправляем истории успеха и примеры результатов
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=escape_text(SUCCESS_STORY),
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    # Отправляем галерею результатов
    try:
        
        with open("face_bot/img/before_after_1.jpg", "rb") as photo:
            await context.bot.send_photo(
                chat_id=job.chat_id,
                photo=photo,
                caption=escape_text(BEFORE_AFTER_RESULTS_MSG),
                parse_mode=ParseMode.MARKDOWN_V2,
            )
    except Exception as e:
        # Если файлы не найдены, просто отправляем текст о результатах
        logger.error(f"Не удалось отправить фото: {e}")

    keyboard = [
        [KeyboardButton("🛒 Магазин")],
    ]

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=escape_text(
            "*Готовы начать свою трансформацию?*\nНажмите на кнопку «Магазин», чтобы выбрать курс, который подходит именно вам."
        ),
        reply_markup=ReplyKeyboardMarkup(
            keyboard, resize_keyboard=True, one_time_keyboard=True
        ),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def remove_job_if_exists(
    name: str, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        print('Я чет щас удалю', job)
        job.schedule_removal()
    return True

async def remove_all_jobs(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    for case in range(0, 7):
        await remove_job_if_exists(name=f"{chat_id}-{CASE_JOB_ID}-{case}", context=context) 
    