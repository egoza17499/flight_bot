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
        # Таблица для "полезной информации"
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS info_base (
                id SERIAL PRIMARY KEY,
                keyword TEXT,
                content TEXT
            )
        """)

# Функции CRUD
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
