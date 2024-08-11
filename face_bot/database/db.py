import aiosqlite

from face_bot.static.conversions import REGISTERED_CONV, CONTACT_CONV, TRY_GUIDE_CONV

DB_PATH = "users.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                id_tg INTEGER default 0,
                status INTEGER default 0,        
                name TEXT,
                phone TEXT,
                subscriptions TEXT
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


async def get_conversions():
    db = await aiosqlite.connect(DB_PATH)

    number_users = []
    # TODO Add statuses

    statuses = [REGISTERED_CONV, CONTACT_CONV, TRY_GUIDE_CONV]

    for status in statuses:
        total_users_with_status = await db.execute(
            """SELECT COUNT(*) FROM users WHERE status >= ?""", (status,)
        )

        total_users_with_status = await total_users_with_status.fetchone()
        total_users_with_status = total_users_with_status[0]

        number_users.append(total_users_with_status)

    return number_users
