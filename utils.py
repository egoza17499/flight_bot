from datetime import datetime, timedelta

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        return None

def check_status(date_val, limit_months):
    """
    Возвращает: 'green' (ok), 'yellow' (<30 дней), 'red' (просрочено)
    """
    if not date_val:
        return 'red', "Нет данных"
    
    today = datetime.now().date()
    delta = date_val - today
    days_left = delta.days
    
    limit_days = limit_months * 30 # Приблизительно
    
    if days_left < 0:
        return 'red', f"Просрочено на {abs(days_left)} дн."
    elif days_left < 30:
        return 'yellow', f"Осталось {days_left} дн."
    else:
        return 'green', f"Действует ({days_left} дн.)"

def generate_profile_text(user_data):
    text = f"👤 <b>{user_data['fio']}</b>\n"
    text += f"🎖 <b>Звание:</b> {user_data['rank']}\n"
    text += f"🏅 <b>Квалификация:</b> {user_data['qual_rank']}\n\n"
    
    # Функция для красивой строки
    def line(name, date_str, limit_m):
        date_val = parse_date(date_str) if date_str else None
        status, msg = check_status(date_val, limit_m)
        color_map = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}
        return f"{color_map[status]} <b>{name}:</b> {date_str or 'Нет'} ({msg})\n"

    text += line("Отпуск (конец)", user_data['vacation_end'], 12)
    text += line("ВЛК", user_data['vlk_date'], 6) # Базовая проверка 6 мес
    
    # Логика УМО
    vlk_date = parse_date(user_data['vlk_date'])
    umo_date = parse_date(user_data['umo_date'])
    umo_status = "🟢 УМО пройдено"
    if vlk_date and (datetime.now().date() - vlk_date).days > 180: # > 6 мес
        if not umo_date:
            umo_status = "🔴 ТРЕБУЕТСЯ УМО"
        else:
            umo_status = f"🟢 УМО: {user_data['umo_date']}"
    text += f"{umo_status}\n"

    text += line("КБП-4 (Ил-76 МД-М)", user_data['kbp_4_md_m'], 6)
    text += line("КБП-7 (Ил-76 МД-М)", user_data['kbp_7_md_m'], 12)
    text += line("КБП-4 (Ил-76 МД-90А)", user_data['kbp_4_md_90a'], 6)
    text += line("КБП-7 (Ил-76 МД-90А)", user_data['kbp_7_md_90a'], 12)
    text += line("Прыжки с ПДС", user_data['jumps_date'], 12)
    
    return text

def check_flight_ban(user_data):
    """Проверяет запреты и возвращает список причин"""
    bans = []
    today = datetime.now().date()
    
    # Вспомогательная функция
    def is_expired(date_str, months):
        if not date_str: return False
        d = parse_date(date_str)
        return (today - d).days > months * 30

    if is_expired(user_data['kbp_4_md_m'], 6):
        bans.append("🚫 Запрет полетов: КБП-4 (Ил-76 МД-М) просрочен")
    if is_expired(user_data['kbp_7_md_m'], 12):
        bans.append("🚫 Запрет полетов: КБП-7 (Ил-76 МД-М) просрочен")
    if is_expired(user_data['kbp_4_md_90a'], 6):
        bans.append("🚫 Запрет полетов: КБП-4 (Ил-76 МД-90А) просрочен")
    if is_expired(user_data['kbp_7_md_90a'], 12):
        bans.append("🚫 Запрет полетов: КБП-7 (Ил-76 МД-90А) просрочен")
        
    # ВЛК и УМО
    vlk = parse_date(user_data['vlk_date'])
    umo = parse_date(user_data['umo_date'])
    if vlk:
        days_since_vlk = (today - vlk).days
        if days_since_vlk > 365: # 12 месяцев
             bans.append("🚫 Запрет полетов: ВЛК просрочена (>12 мес)")
        elif days_since_vlk > 180 and not umo: # > 6 мес и нет УМО
             bans.append("🚫 Запрет полетов: ВЛК > 6 мес без УМО")
             
    if is_expired(user_data['vacation_end'], 12):
        bans.append("🚫 Запрет полетов: Отпуск (>12 мес)")
        
    if is_expired(user_data['jumps_date'], 12):
        bans.append("🚫 Запрет полетов: Прыжки (>12 мес)")
        
    return bans