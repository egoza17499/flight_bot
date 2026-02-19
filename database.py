import asyncpg
from config import DSN
from datetime import datetime

async def get_pool():
    return await asyncpg.create_pool(DSN)

async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                fio TEXT,
                rank TEXT,
                qual_rank TEXT,
                vacation_start DATE,
                vacation_end DATE,
                vlk_date DATE,
                umo_date DATE,
                kbp_4_md_m DATE,
                kbp_7_md_m DATE,
                kbp_4_md_90a DATE,
                kbp_7_md_90a DATE,
                jumps_date DATE,
                registered BOOLEAN DEFAULT FALSE
            )
        """)
        # Таблица для "полезной информации" (заглушка, так как вы сказали, что создадим позже)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS info_base (
                id SERIAL PRIMARY KEY,
                keyword TEXT,
                content TEXT
            )
        """)

# Функции CRUD
async def add_user(user_id, username):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING",
            user_id, username
        )

async def update_user_field(user_id, field, value):
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = f"UPDATE users SET {field} = $1 WHERE user_id = $2"
        await conn.execute(query, value, user_id)

async def set_registered(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET registered = TRUE WHERE user_id = $1", user_id)

async def get_user(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(row) if row else None

async def get_all_users():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users WHERE registered = TRUE")
        return [dict(row) for row in rows]

async def search_info(keyword):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT content FROM info_base WHERE keyword ILIKE $1", f"%{keyword}%")
        return [row['content'] for row in rows]