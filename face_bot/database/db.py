import aiosqlite


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
