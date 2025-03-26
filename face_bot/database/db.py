import aiosqlite

from face_bot.static.conversions import (
    REGISTERED_CONV,
    CONTACT_CONV,
    TRY_GUIDE_CONV,
    ENROLL_CONV,
    BUY_SUBSCRIPTION_CONV,
)

from face_bot.static.status import (
    START_ST,
    LEARN_HOW_ST,
    SENT_PHONE_ST,
    PRESSED_YES_ST,
    PRESSED_GOOD_ST,
    BOUGHT_ONE_ST,
    BOUGHT_ALL_ST,
)

DB_PATH = "users.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                id_tg INTEGER default 0,
                status INTEGER default 0, 
                case_num INTEGER default 1,       
                name TEXT,
                phone TEXT,
                subscriptions TEXT default NULL,
                email TEXT default NULL
            )
        """)
        await db.commit()


async def register(user_id, name):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT name FROM users WHERE id_tg = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                await db.execute(
                    """
                    INSERT INTO users (id_tg, status, name) 
                    VALUES (?, ?, ?)
                """,
                    (
                        user_id,
                        REGISTERED_CONV,
                        name,
                    ),
                )

            await db.commit()


async def get_current_case(user_id):
    current_case = 0

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT case_num FROM users WHERE id_tg = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

            current_case = row[0]

    return current_case


async def update_case(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT case_num FROM users WHERE id_tg = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

            await db.execute(
                """
                        UPDATE users
                        SET case_num = ?
                        WHERE id_tg = ?
                    """,
                (row[0] + 1, user_id),
            )

            await db.commit()


async def reset_case(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
                    UPDATE users
                    SET case_num = 1
                    WHERE id_tg = ?
                """,
            (user_id,),
        )

        await db.commit()


async def update_status(user_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
                    UPDATE users
                    SET status = ?
                    WHERE id_tg = ?
                """,
            (status, user_id),
        )

        await db.commit()


async def save_phone(user_id, phone_number):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
                    UPDATE users
                    SET status = ?, phone = ?
                    WHERE id_tg = ?
                """,
            (CONTACT_CONV, phone_number, user_id),
        )

        await db.commit()


async def get_subscriptions(user_id):
    """Получает покупки пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT subscriptions FROM users WHERE id_tg = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row[0]:
                lst_subs = list(map(int, row[0].split(",")))
                return lst_subs
            return []


async def get_phone_number_by_id(user_id):
    """Получает телефон пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT phone FROM users WHERE id_tg = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0]


async def save_subscription(subs, user_id):
    """Сохраняет покупку пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT subscriptions FROM users WHERE id_tg = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()

            new_row_subs = f"{row[0]},{subs}" if row[0] else subs
            await db.execute(
                """
                        UPDATE users
                        SET status = ?, subscriptions = ?
                        WHERE id_tg = ?
                    """,
                (BUY_SUBSCRIPTION_CONV, new_row_subs, user_id),
            )

            await db.commit()


async def save_name(user_id, name):
    """Сохраняет имя пользователя для консультации"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
                    UPDATE users
                    SET status = ?, name = ?
                    WHERE id_tg = ?
                """,
            (ENROLL_CONV, name, user_id),
        )

        await db.commit()


async def get_conversions():
    """Стата для конверсии"""
    db = await aiosqlite.connect(DB_PATH)

    number_users = []

    statuses = [
        START_ST,
        LEARN_HOW_ST,
        SENT_PHONE_ST,
        PRESSED_YES_ST,
        PRESSED_GOOD_ST,
        BOUGHT_ONE_ST,
        BOUGHT_ALL_ST,
    ]

    for status in statuses:
        total_users_with_status = await db.execute(
            """SELECT COUNT(*) FROM users WHERE status >= ?""", (status,)
        )

        total_users_with_status = await total_users_with_status.fetchone()
        total_users_with_status = total_users_with_status[0]

        number_users.append(total_users_with_status)

    return number_users


async def save_email(user_id, email):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
                    UPDATE users
                    SET email = ?
                    WHERE id_tg = ?
                """,
            (email, user_id),
        )

        await db.commit()


async def get_email(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT email FROM users WHERE id_tg = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0]
