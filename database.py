import asyncpg
from config import DSN, ADMIN_ID
from datetime import datetime

async def get_pool():
    """Получить пул подключений к базе данных"""
    return await asyncpg.create_pool(DSN)

async def init_db():
    """Инициализация базы данных - создание таблиц"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Таблица пользователей
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
        
        # Таблица для "полезной информации" (аэродромы, телефоны)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS info_base (
                id SERIAL PRIMARY KEY,
                keyword TEXT,
                content TEXT
            )
        """)
        
        # Таблица администраторов
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE,
                added_by BIGINT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Добавляем главного админа при первом запуске (защищен от удаления)
        await conn.execute(
            "INSERT INTO admins (user_id, added_by) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING",
            ADMIN_ID, 0  # 0 означает системного админа (главного)
        )

# ========== ФУНКЦИИ ПОЛЬЗОВАТЕЛЕЙ ==========

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
        # Список полей с датами (кроме jumps_date)
        date_fields = [
            'vacation_start', 'vacation_end', 'vlk_date', 'umo_date',
            'kbp_4_md_m', 'kbp_7_md_m', 'kbp_4_md_90a', 'kbp_7_md_90a'
        ]
        
        # Если поле - дата, преобразуем строку в объект date
        if field in date_fields and value:
            try:
                value = datetime.strptime(value, "%d.%m.%Y").date()
            except (ValueError, TypeError):
                value = None
        
        # Для jumps_date - проверяем на "освобожден"
        if field == 'jumps_date' and value:
            if isinstance(value, str) and value.lower() in ['освобожден', 'освобождён', 'осв']:
                value = 'освобожден'
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

async def delete_user(user_id):
    """Удалить пользователя из базы"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)

# ========== ФУНКЦИИ ИНФОРМАЦИИ (АЭРОДРОМЫ) ==========

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

# ========== ФУНКЦИИ УПРАВЛЕНИЯ АДМИНАМИ ==========

async def is_admin(user_id):
    """Проверяет является ли пользователь админом"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT user_id FROM admins WHERE user_id = $1", user_id)
        return row is not None

async def is_super_admin(user_id):
    """
    Проверяет является ли пользователь главным админом.
    Главный админ защищен от удаления.
    """
    return user_id == ADMIN_ID

async def add_admin(target_user_id, added_by_user_id):
    """
    Добавить админа.
    
    Args:
        target_user_id: ID пользователя которого добавляем
        added_by_user_id: ID админа который добавляет
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # Нельзя добавить самого себя
    if target_user_id == added_by_user_id:
        return False, "❌ Нельзя добавить самого себя"
    
    # Проверяем не является ли уже админом
    if await is_admin(target_user_id):
        return False, f"❌ Пользователь {target_user_id} уже является админом"
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO admins (user_id, added_by) VALUES ($1, $2)",
            target_user_id, added_by_user_id
        )
    
    return True, f"✅ Пользователь {target_user_id} добавлен в администраторы"

async def remove_admin(target_user_id, removed_by_user_id):
    """
    Удалить админа.
    
    Args:
        target_user_id: ID пользователя которого удаляем
        removed_by_user_id: ID админа который удаляет
    
    Returns:
        tuple: (success: bool, message: str)
    """
    # 🔒 ЗАЩИТА: Нельзя удалить главного админа
    if target_user_id == ADMIN_ID:
        return False, "🚫 Нельзя удалить главного администратора!"
    
    # 🔒 ЗАЩИТА: Нельзя удалить самого себя
    if target_user_id == removed_by_user_id:
        return False, "❌ Нельзя удалить самого себя. Попросите другого админа."
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Проверяем существует ли админ
        row = await conn.fetchrow("SELECT user_id FROM admins WHERE user_id = $1", target_user_id)
        if not row:
            return False, f"❌ Пользователь {target_user_id} не является админом"
        
        await conn.execute("DELETE FROM admins WHERE user_id = $1", target_user_id)
    
    return True, f"✅ Пользователь {target_user_id} удален из администраторов"

async def get_all_admins():
    """
    Получить список всех админов.
    
    Returns:
        list: Список словарей с информацией об админах
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id, added_by, added_at FROM admins ORDER BY added_at")
        return [dict(row) for row in rows]

async def get_admin_info(user_id):
    """
    Получить информацию об конкретном админе.
    
    Args:
        user_id: ID админа
    
    Returns:
        dict or None: Информация об админе или None
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, added_by, added_at FROM admins WHERE user_id = $1",
            user_id
        )
        return dict(row) if row else None

async def get_admin_count():
    """Получить количество админов"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) as count FROM admins")
        return row['count'] if row else 0
