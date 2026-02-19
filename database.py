import asyncpg
from config import DSN
from datetime import datetime

async def get_pool():
    """Получить пул подключений к базе данных"""
    return await asyncpg.create_pool(DSN)

async def init_db():
    """Инициализация базы данных - создание таблиц"""
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
                jumps_date TEXT,
                registered BOOLEAN DEFAULT FALSE
            )
        """)
        # Таблица для "полезной информации" (аэродромы, телефоны и т.д.)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS info_base (
                id SERIAL PRIMARY KEY,
                keyword TEXT,
                content TEXT
            )
        """)

async def add_user(user_id, username):
    """Добавить нового пользователя или обновить username"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (user_id, username) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET username = $2",
            user_id, username
        )

async def update_user_field(user_id, field, value):
    """
    Обновить поле пользователя.
    Автоматически преобразует строки дат в объекты date.
    Поддерживает значение 'освобожден' для jumps_date.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Список полей с датами (кроме jumps_date - там может быть "освобожден")
        date_fields = [
            'vacation_start', 'vacation_end', 'vlk_date', 'umo_date',
            'kbp_4_md_m', 'kbp_7_md_m', 'kbp_4_md_90a', 'kbp_7_md_90a'
        ]
        
        # Если поле - дата, преобразуем строку в объект date
        if field in date_fields and value:
            try:
                value = datetime.strptime(value, "%d.%m.%Y").date()
            except (ValueError, TypeError):
                # Если не удалось распарсить, оставляем None
                value = None
        
        # Для jumps_date - проверяем на "освобожден"
        if field == 'jumps_date' and value:
            if isinstance(value, str) and value.lower() in ['освобожден', 'освобождён', 'осв']:
                value = 'освобожден'  # Сохраняем как текст
            else:
                try:
                    value = datetime.strptime(value, "%d.%m.%Y").date()
                except (ValueError, TypeError):
                    value = None
        
        query = f"UPDATE users SET {field} = $1 WHERE user_id = $2"
        await conn.execute(query, value, user_id)

async def set_registered(user_id):
    """Отметить пользователя как зарегистрированного"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET registered = TRUE WHERE user_id = $1", user_id)

async def get_user(user_id):
    """Получить данные пользователя по user_id"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return dict(row) if row else None

async def get_all_users():
    """Получить всех зарегистрированных пользователей"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users WHERE registered = TRUE")
        return [dict(row) for row in rows]

async def search_info(keyword):
    """Поиск информации по ключевому слову"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT content FROM info_base WHERE keyword ILIKE $1", f"%{keyword}%")
        return [row['content'] for row in rows]

async def add_info(keyword, content):
    """Добавить информацию в базу (для админа)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("INSERT INTO info_base (keyword, content) VALUES ($1, $2)", keyword, content)

async def delete_user(user_id):
    """Удалить пользователя из базы"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)

async def delete_info(keyword):
    """Удалить информацию из базы по ключевому слову"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM info_base WHERE keyword = $1", keyword)

async def get_all_info():
    """Получить всю информацию из базы (для админа)"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT keyword, content FROM info_base")
        return [dict(row) for row in rows]
