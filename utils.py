from datetime import datetime

def parse_date(date_str):
    """Парсинг даты из строки"""
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except:
        return None

def check_status(date_str):
    """Проверка статуса даты (просрочено/скоро истечет/нормально)"""
    if not date_str or date_str.lower() in ['нет', 'не пройдено', 'б/к', '']:
        return "expired", "Не пройдено"
    
    try:
        deadline = datetime.strptime(date_str, "%d.%m.%Y")
        now = datetime.now()
        delta = deadline - now
        
        if delta.days < 0:
            return "expired", f"Просрочено ({abs(delta.days)} дн. назад)"
        elif delta.days < 30:
            return "warning", f"Осталось {delta.days} дн."
        else:
            return "ok", f"Действует ({delta.days} дн.)"
    except:
        return "unknown", "Неизвестно"

def generate_profile_text(user):
    """Генерация текста профиля пользователя"""
    text = f"👤 <b>{user.get('fio', 'Не указано')}</b>\n\n"
    text += f"🎖 <b>Звание:</b> {user.get('rank', 'Не указано')}\n"
    text += f"📊 <b>Квалификация:</b> {user.get('qual_rank', 'Не указано')}\n\n"
    
    text += f"📅 <b>Отпуск:</b> {user.get('vacation_start', 'Не указано')} - {user.get('vacation_end', 'Не указано')}\n"
    text += f"🏥 <b>ВЛК:</b> {user.get('vlk_date', 'Не пройдено')}\n"
    text += f"📝 <b>УМО:</b> {user.get('umo_date', 'Не пройдено')}\n\n"
    
    text += f"✈️ <b>КБП:</b>\n"
    text += f"  • КБП-4 МД-М: {user.get('kbp_4_md_m', 'Не пройдено')}\n"
    text += f"  • КБП-7 МД-М: {user.get('kbp_7_md_m', 'Не пройдено')}\n"
    text += f"  • КБП-4 МД-90А: {user.get('kbp_4_md_90a', 'Не пройдено')}\n"
    text += f"  • КБП-7 МД-90А: {user.get('kbp_7_md_90a', 'Не пройдено')}\n\n"
    
    text += f"🪂 <b>Прыжки:</b> {user.get('jumps_date', 'Не указано')}\n"
    
    return text

def check_flight_ban(user):
    """Проверка запретов на полеты"""
    bans = []
    
    # Проверка ВЛК
    vlk = user.get('vlk_date')
    if vlk:
        try:
            vlk_date = datetime.strptime(vlk, "%d.%m.%Y")
            if (datetime.now() - vlk_date).days > 365:
                bans.append("🔴 ВЛК: просрочено")
        except:
            pass
    
    # Проверка УМО
    umo = user.get('umo_date')
    if umo and umo.lower() not in ['нет', 'не пройдено']:
        try:
            umo_date = datetime.strptime(umo, "%d.%m.%Y")
            if (datetime.now() - umo_date).days > 365:
                bans.append("🔴 УМО: просрочено")
        except:
            pass
    
    return bans

def extract_airport_info(query: str, result_text: str) -> str:
    """Извлекает информацию о городе и аэродроме"""
    info = ""
    query_lower = query.lower()
    
    airports_map = {
        "стригино": ("Нижний Новгород", "Аэропорт Стригино"),
        "чкаловский": ("Москва", "Аэродром Чкаловский"),
        "пулково": ("Санкт-Петербург", "Аэропорт Пулково"),
        "внуково": ("Москва", "Аэропорт Внуково"),
        "кольцово": ("Екатеринбург", "Аэропорт Кольцово"),
    }
    
    for key, (city, airport) in airports_map.items():
        if key in query_lower:
            info += f"🏙 <b>Город:</b> {city}\n"
            info += f"✈️ <b>Аэродром:</b> {airport}"
            break
    
    return info

def get_persistent_menu(is_admin=False):
    """Постоянное закреплённое меню внизу"""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = [
        [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="📚 Полезная информация")],
    ]
    if is_admin:
        kb.append([KeyboardButton(text="🛡 Функции админа")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, persistent=True)

def check_deadline_status(date_str, field_name=""):
    """Проверяет статус срока"""
    if not date_str or date_str.lower() in ['нет', 'не пройдено', 'б/к', '']:
        return "red", f"{field_name}: не пройдено"
    
    try:
        deadline = datetime.strptime(date_str, "%d.%m.%Y")
        now = datetime.now()
        delta = deadline - now
        
        if delta.days < 0:
            return "red", f"{field_name}: просрочено ({abs(delta.days)} дн. назад)"
        elif delta.days < 30:
            return "yellow", f"{field_name}: осталось {delta.days} дн."
        else:
            return "green", "OK"
    except:
        return "green", "OK"

def get_user_status_with_colors(user):
    """Формирует текст статуса пользователя с цветовой индикацией (как на скриншоте 2)"""
    status_parts = []
    
    # Проверка отпуска
    vacation_end = user.get('vacation_end')
    if vacation_end and vacation_end.lower() not in ['нет', 'не указано', '']:
        try:
            vacation_date = datetime.strptime(vacation_end, "%d.%m.%Y")
            now = datetime.now()
            delta = vacation_date - now
            
            if delta.days < 0:
                status_parts.append(f"🔴 Отпуск (конец): {vacation_end} (Просрочен на {abs(delta.days)} дн.)")
            elif delta.days < 30:
                status_parts.append(f"🟡 Отпуск (конец): {vacation_end} (Осталось {delta.days} дн.)")
            else:
                status_parts.append(f"🟢 Отпуск (конец): {vacation_end} (Действует (осталось {delta.days} дн.))")
        except:
            pass
    
    # Проверка ВЛК
    vlk = user.get('vlk_date')
    if vlk and vlk.lower() not in ['нет', 'не пройдено', '']:
        try:
            vlk_date = datetime.strptime(vlk, "%d.%m.%Y")
            now = datetime.now()
            delta = vlk_date - now
            
            if delta.days < 0:
                status_parts.append(f"🔴 ВЛК: {vlk} (Просрочена на {abs(delta.days)} дн.)")
            elif delta.days < 30:
                status_parts.append(f"🟡 ВЛК: {vlk} (Осталось {delta.days} дн.)")
            else:
                status_parts.append(f"🟢 ВЛК: {vlk} (Действует (осталось {delta.days} дн.))")
        except:
            pass
    
    # Проверка УМО
    umo = user.get('umo_date')
    if umo and umo.lower() not in ['нет', 'не пройдено', '']:
        try:
            umo_date = datetime.strptime(umo, "%d.%m.%Y")
            now = datetime.now()
            delta = umo_date - now
            
            if delta.days < 0:
                status_parts.append(f"🔴 УМО: {umo} (Просрочено на {abs(delta.days)} дн.)")
            elif delta.days < 30:
                status_parts.append(f"🟡 УМО: {umo} (Осталось {delta.days} дн.)")
            else:
                status_parts.append(f"🟢 УМО: {umo} (Действует (осталось {delta.days} дн.))")
        except:
            pass
    
    # Проверка КБП-4 МД-М
    kbp_4_md_m = user.get('kbp_4_md_m')
    if kbp_4_md_m and kbp_4_md_m.lower() not in ['нет', 'не пройдено', '']:
        try:
            kbp_date = datetime.strptime(kbp_4_md_m, "%d.%m.%Y")
            now = datetime.now()
            delta = kbp_date - now
            
            if delta.days < 0:
                status_parts.append(f"🔴 КБП-4 (Ил-76 МД-М): {kbp_4_md_m} (Просрочено на {abs(delta.days)} дн.)")
            elif delta.days < 30:
                status_parts.append(f"🟡 КБП-4 (Ил-76 МД-М): {kbp_4_md_m} (Осталось {delta.days} дн.)")
            else:
                status_parts.append(f"🟢 КБП-4 (Ил-76 МД-М): {kbp_4_md_m} (Действует (осталось {delta.days} дн.))")
        except:
            pass
    
    # Проверка КБП-7 МД-М
    kbp_7_md_m = user.get('kbp_7_md_m')
    if kbp_7_md_m and kbp_7_md_m.lower() not in ['нет', 'не пройдено', '']:
        try:
            kbp_date = datetime.strptime(kbp_7_md_m, "%d.%m.%Y")
            now = datetime.now()
            delta = kbp_date - now
            
            if delta.days < 0:
                status_parts.append(f"🔴 КБП-7 (Ил-76 МД-М): {kbp_7_md_m} (Просрочено на {abs(delta.days)} дн.)")
            elif delta.days < 30:
                status_parts.append(f"🟡 КБП-7 (Ил-76 МД-М): {kbp_7_md_m} (Осталось {delta.days} дн.)")
            else:
                status_parts.append(f"🟢 КБП-7 (Ил-76 МД-М): {kbp_7_md_m} (Действует (осталось {delta.days} дн.))")
        except:
            pass
    
    # Проверка КБП-4 МД-90А
    kbp_4_md_90a = user.get('kbp_4_md_90a')
    if kbp_4_md_90a and kbp_4_md_90a.lower() not in ['нет', 'не пройдено', '']:
        try:
            kbp_date = datetime.strptime(kbp_4_md_90a, "%d.%m.%Y")
            now = datetime.now()
            delta = kbp_date - now
            
            if delta.days < 0:
                status_parts.append(f"🔴 КБП-4 (Ил-76 МД-90А): {kbp_4_md_90a} (Просрочено на {abs(delta.days)} дн.)")
            elif delta.days < 30:
                status_parts.append(f"🟡 КБП-4 (Ил-76 МД-90А): {kbp_4_md_90a} (Осталось {delta.days} дн.)")
            else:
                status_parts.append(f"🟢 КБП-4 (Ил-76 МД-90А): {kbp_4_md_90a} (Действует (осталось {delta.days} дн.))")
        except:
            pass
    
    # Проверка КБП-7 МД-90А
    kbp_7_md_90a = user.get('kbp_7_md_90a')
    if kbp_7_md_90a and kbp_7_md_90a.lower() not in ['нет', 'не пройдено', '']:
        try:
            kbp_date = datetime.strptime(kbp_7_md_90a, "%d.%m.%Y")
            now = datetime.now()
            delta = kbp_date - now
            
            if delta.days < 0:
                status_parts.append(f"🔴 КБП-7 (Ил-76 МД-90А): {kbp_7_md_90a} (Просрочено на {abs(delta.days)} дн.)")
            elif delta.days < 30:
                status_parts.append(f"🟡 КБП-7 (Ил-76 МД-90А): {kbp_7_md_90a} (Осталось {delta.days} дн.)")
            else:
                status_parts.append(f"🟢 КБП-7 (Ил-76 МД-90А): {kbp_7_md_90a} (Действует (осталось {delta.days} дн.))")
        except:
            pass
    
    # Проверка прыжков
    jumps = user.get('jumps_date')
    if jumps and jumps.lower() not in ['нет', 'не пройдено', '']:
        try:
            jumps_date = datetime.strptime(jumps, "%d.%m.%Y")
            now = datetime.now()
            delta = jumps_date - now
            
            if delta.days < 0:
                status_parts.append(f"🔴 Прыжки с ПДС: {jumps} (Просрочено на {abs(delta.days)} дн.)")
            elif delta.days < 30:
                status_parts.append(f"🟡 Прыжки с ПДС: {jumps} (Осталось {delta.days} дн.)")
            else:
                status_parts.append(f"🟢 Прыжки с ПДС: {jumps} (Действует (осталось {delta.days} дн.))")
        except:
            pass
    
    # Возвращаем все статусы
    if status_parts:
        return "\n".join(status_parts)
    else:
        return "🟢 <b>Всё в порядке</b>"

# Маппинг полей
FIELD_MAP = {
    "fio": "fio",
    "rank": "rank",
    "qual_rank": "qual_rank",
    "vacation": "vacation",
    "vlk_date": "vlk_date",
    "umo_date": "umo_date",
    "kbp_4_md_m": "kbp_4_md_m",
    "kbp_7_md_m": "kbp_7_md_m",
    "kbp_4_md_90a": "kbp_4_md_90a",
    "kbp_7_md_90a": "kbp_7_md_90a",
    "jumps_date": "jumps_date"
}

FIELD_NAMES = {
    "fio": "ФИО",
    "rank": "Звание",
    "qual_rank": "Квалификационный разряд",
    "vacation": "Отпуск (ДД.ММ.ГГГГ - ДД.ММ.ГГГГ)",
    "vlk_date": "ВЛК (ДД.ММ.ГГГГ)",
    "umo_date": "УМО (ДД.ММ.ГГГГ или 'нет')",
    "kbp_4_md_m": "КБП-4 Ил-76 МД-М",
    "kbp_7_md_m": "КБП-7 Ил-76 МД-М",
    "kbp_4_md_90a": "КБП-4 Ил-76 МД-90А",
    "kbp_7_md_90a": "КБП-7 Ил-76 МД-90А",
    "jumps_date": "Прыжки (ДД.ММ.ГГГГ или 'освобожден')"
}
