from datetime import datetime, date

def parse_date(date_str):
    """Преобразует строку даты в объект date"""
    if not date_str or date_str.lower() in ['нет', 'освобожден', 'осв', 'n/a', '-']:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
    except (ValueError, TypeError):
        return None

def check_status(date_value):
    """
    Проверяет статус даты (для планировщика).
    Returns: 'expired' (просрочено), 'warning' (скоро), 'ok' (действует)
    """
    if not date_value:
        return 'no_data'
    
    if isinstance(date_value, str):
        date_value = parse_date(date_value)
        if not date_value:
            return 'no_data'
    
    today = date.today()
    days = (date_value - today).days
    
    if days < 0:
        return 'expired'
    elif days <= 30:
        return 'warning'
    else:
        return 'ok'

def get_status_color(days_remaining):
    """
    Определяет статус и цвет по количеству дней.
    Returns: (emoji, status_text)
    """
    if days_remaining is None:
        return "⚪", "Нет данных"
    elif days_remaining < 0:
        return "🔴", f"Просрочено на {abs(days_remaining)} дн."
    elif days_remaining <= 30:
        return "🟡", f"Осталось {days_remaining} дн."
    else:
        return "🟢", f"Действует (осталось {days_remaining} дн.)"

def generate_profile_text(user):
    """
    Генерирует текст профиля с цветовой индикацией сроков.
    """
    if not user:
        return "❌ Пользователь не найден"
    
    fio = user.get('fio', 'Нет данных') or 'Нет данных'
    rank = user.get('rank', 'Нет') or 'Нет'
    qual_rank = user.get('qual_rank', 'Нет') or 'Нет'
    
    text = f"👤 {fio}\n"
    text += f"🎖 Звание: {rank}\n"
    text += f"🏅 Квалификация: {qual_rank}\n"
    
    today = date.today()
    
    # Отпуск (конец)
    vacation_end = parse_date(user.get('vacation_end'))
    if vacation_end:
        days = (vacation_end - today).days
        emoji, status = get_status_color(days)
        text += f"\n{emoji} Отпуск (конец):: {vacation_end.strftime('%d.%m.%Y')} ({status})"
    else:
        text += f"\n⚪ Отпуск (конец):: Нет данных"
    
    # ВЛК
    vlk_date = parse_date(user.get('vlk_date'))
    if vlk_date:
        days = (vlk_date - today).days
        emoji, status = get_status_color(days)
        text += f"\n{emoji} ВЛК: {vlk_date.strftime('%d.%m.%Y')} ({status})"
    else:
        text += f"\n⚪ ВЛК: Нет данных"
    
    # УМО
    umo_date = parse_date(user.get('umo_date'))
    if umo_date:
        days = (umo_date - today).days
        emoji, status = get_status_color(days)
        text += f"\n{emoji} УМО: {umo_date.strftime('%d.%m.%Y')} ({status})"
    else:
        text += f"\n⚪ УМО: Нет данных"
    
    # КБП-4 (Ил-76 МД-М)
    kbp_4_md_m = parse_date(user.get('kbp_4_md_m'))
    if kbp_4_md_m:
        days = (kbp_4_md_m - today).days
        emoji, status = get_status_color(days)
        text += f"\n{emoji} КБП-4 (Ил-76 МД-М):: {kbp_4_md_m.strftime('%d.%m.%Y')} ({status})"
    else:
        text += f"\n⚪ КБП-4 (Ил-76 МД-М):: Нет данных"
    
    # КБП-7 (Ил-76 МД-М)
    kbp_7_md_m = parse_date(user.get('kbp_7_md_m'))
    if kbp_7_md_m:
        days = (kbp_7_md_m - today).days
        emoji, status = get_status_color(days)
        text += f"\n{emoji} КБП-7 (Ил-76 МД-М):: {kbp_7_md_m.strftime('%d.%m.%Y')} ({status})"
    else:
        text += f"\n⚪ КБП-7 (Ил-76 МД-М):: Нет данных"
    
    # КБП-4 (Ил-76 МД-90А)
    kbp_4_md_90a = parse_date(user.get('kbp_4_md_90a'))
    if kbp_4_md_90a:
        days = (kbp_4_md_90a - today).days
        emoji, status = get_status_color(days)
        text += f"\n{emoji} КБП-4 (Ил-76 МД-90А):: {kbp_4_md_90a.strftime('%d.%m.%Y')} ({status})"
    else:
        text += f"\n⚪ КБП-4 (Ил-76 МД-90А):: Нет данных"
    
    # КБП-7 (Ил-76 МД-90А)
    kbp_7_md_90a = parse_date(user.get('kbp_7_md_90a'))
    if kbp_7_md_90a:
        days = (kbp_7_md_90a - today).days
        emoji, status = get_status_color(days)
        text += f"\n{emoji} КБП-7 (Ил-76 МД-90А):: {kbp_7_md_90a.strftime('%d.%m.%Y')} ({status})"
    else:
        text += f"\n⚪ КБП-7 (Ил-76 МД-90А):: Нет данных"
    
    # Прыжки с ПДС
    jumps_date_str = user.get('jumps_date')
    if jumps_date_str and jumps_date_str.lower() not in ['освобожден', 'осв', 'нет']:
        jumps_date = parse_date(jumps_date_str)
        if jumps_date:
            days = (jumps_date - today).days
            emoji, status = get_status_color(days)
            text += f"\n{emoji} Прыжки с ПДС:: {jumps_date.strftime('%d.%m.%Y')} ({status})"
        else:
            text += f"\n⚪ Прыжки с ПДС:: Нет данных"
    elif jumps_date_str and jumps_date_str.lower() in ['освобожден', 'осв']:
        text += f"\n⚪ Прыжки с ПДС:: Освобожден"
    else:
        text += f"\n⚪ Прыжки с ПДС:: Нет данных"
    
    return text

def check_flight_ban(user):
    """
    Проверяет запреты на полеты.
    """
    bans = []
    today = date.today()
    
    vlk_date = parse_date(user.get('vlk_date'))
    if vlk_date and vlk_date < today:
        days = (today - vlk_date).days
        bans.append(f"🔴 ВЛК просрочена на {days} дн.")
    
    kbp_4_md_m = parse_date(user.get('kbp_4_md_m'))
    if kbp_4_md_m and kbp_4_md_m < today:
        days = (today - kbp_4_md_m).days
        bans.append(f"🔴 КБП-4 (МД-М) просрочен на {days} дн.")
    
    kbp_4_md_90a = parse_date(user.get('kbp_4_md_90a'))
    if kbp_4_md_90a and kbp_4_md_90a < today:
        days = (today - kbp_4_md_90a).days
        bans.append(f"🔴 КБП-4 (МД-90А) просрочен на {days} дн.")
    
    jumps_date_str = user.get('jumps_date')
    if jumps_date_str and jumps_date_str.lower() not in ['освобожден', 'осв', 'нет']:
        jumps_date = parse_date(jumps_date_str)
        if jumps_date and jumps_date < today:
            days = (today - jumps_date).days
            bans.append(f"🔴 Прыжки с ПДС просрочены на {days} дн.")
    
    return bans

def get_user_status_with_colors(user):
    """
    Возвращает краткий статус пользователя с цветами.
    """
    today = date.today()
    status_parts = []
    
    vlk_date = parse_date(user.get('vlk_date'))
    if vlk_date:
        days = (vlk_date - today).days
        if days < 0:
            status_parts.append("🔴 ВЛК")
        elif days <= 30:
            status_parts.append("🟡 ВЛК")
        else:
            status_parts.append("🟢 ВЛК")
    
    kbp_4_md_m = parse_date(user.get('kbp_4_md_m'))
    if kbp_4_md_m:
        days = (kbp_4_md_m - today).days
        if days < 0:
            status_parts.append("🔴 КБП-4")
        elif days <= 30:
            status_parts.append("🟡 КБП-4")
        else:
            status_parts.append("🟢 КБП-4")
    
    jumps_date_str = user.get('jumps_date')
    if jumps_date_str and jumps_date_str.lower() not in ['освобожден', 'осв', 'нет']:
        jumps_date = parse_date(jumps_date_str)
        if jumps_date:
            days = (jumps_date - today).days
            if days < 0:
                status_parts.append("🔴 ПДС")
            elif days <= 30:
                status_parts.append("🟡 ПДС")
            else:
                status_parts.append("🟢 ПДС")
    
    return " | ".join(status_parts) if status_parts else "⚪ Нет данных"
