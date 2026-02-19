from datetime import datetime, timedelta

def parse_date(date_val):
    """
    Преобразует значение в объект date.
    Принимает: строку 'ДД.ММ.ГГГГ', объект date, или None
    """
    if date_val is None:
        return None
    
    # Если уже объект date
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, timedelta):
        return None
    
    # Если строка "освобожден"
    if isinstance(date_val, str) and date_val.lower() in ['освобожден', 'освобождён', 'осв']:
        return 'exempt'  # Специальное значение
    
    # Если строка даты
    if isinstance(date_val, str):
        try:
            return datetime.strptime(date_val, "%d.%m.%Y").date()
        except ValueError:
            return None
    
    # Если объект date из базы
    if hasattr(date_val, 'strftime'):
        return date_val
    
    return None

def check_status(date_val, limit_months):
    """
    Возвращает: 'green' (ok), 'yellow' (<30 дней), 'red' (просрочено)
    """
    if date_val == 'exempt':
        return 'blue', "Освобожден"
    
    if not date_val:
        return 'red', "Нет данных"
    
    today = datetime.now().date()
    
    # Если date_val - это строка (из базы)
    if isinstance(date_val, str):
        try:
            date_val = datetime.strptime(date_val, "%d.%m.%Y").date()
        except ValueError:
            return 'red', "Некорректная дата"
    
    delta = date_val - today
    days_left = delta.days
    
    limit_days = limit_months * 30  # Приблизительно
    
    if days_left < 0:
        return 'red', f"Просрочено на {abs(days_left)} дн."
    elif days_left < 30:
        return 'yellow', f"Осталось {days_left} дн."
    else:
        return 'green', f"Действует ({days_left} дн.)"

def generate_profile_text(user_data):
    """Генерирует текст профиля с цветовой индикацией"""
    text = f"👤 <b>{user_data['fio']}</b>\n"
    text += f"🎖 <b>Звание:</b> {user_data['rank']}\n"
    text += f"🏅 <b>Квалификация:</b> {user_data['qual_rank']}\n\n"
    
    # Функция для красивой строки
    def line(name, date_val, limit_m):
        # Проверяем на "освобожден"
        if isinstance(date_val, str) and date_val.lower() in ['освобожден', 'освобождён', 'осв']:
            return f"🔵 <b>{name}:</b> Освобожден\n"
        
        # Парсим дату
        parsed = parse_date(date_val)
        
        if parsed is None or parsed == 'exempt':
            if date_val and isinstance(date_val, str) and date_val.lower() in ['освобожден', 'освобождён', 'осв']:
                return f"🔵 <b>{name}:</b> Освобожден\n"
            return f"⚪ <b>{name}:</b> Нет данных\n"
        
        status, msg = check_status(parsed, limit_m)
        color_map = {'green': '🟢', 'yellow': '🟡', 'red': '🔴', 'blue': '🔵'}
        date_str = parsed.strftime("%d.%m.%Y") if hasattr(parsed, 'strftime') else str(parsed)
        return f"{color_map.get(status, '⚪')} <b>{name}:</b> {date_str} ({msg})\n"

    # Отпуск
    vacation_end = user_data.get('vacation_end')
    if vacation_end and hasattr(vacation_end, 'strftime'):
        vacation_end = vacation_end.strftime("%d.%m.%Y")
    text += line("Отпуск (конец)", vacation_end, 12)
    
    # ВЛК
    vlk_date = user_data.get('vlk_date')
    if vlk_date and hasattr(vlk_date, 'strftime'):
        vlk_date = vlk_date.strftime("%d.%m.%Y")
    text += line("ВЛК", vlk_date, 6)
    
    # Логика УМО
    vlk_parsed = parse_date(user_data.get('vlk_date'))
    umo_date = user_data.get('umo_date')
    if umo_date and hasattr(umo_date, 'strftime'):
        umo_str = umo_date.strftime("%d.%m.%Y")
    elif umo_date:
        umo_str = str(umo_date)
    else:
        umo_str = None
    
    umo_status = "🟢 УМО пройдено"
    if vlk_parsed and vlk_parsed != 'exempt' and (datetime.now().date() - vlk_parsed).days > 180:  # > 6 мес
        if not umo_date or umo_date == 'none':
            umo_status = "🔴 ТРЕБУЕТСЯ УМО"
        else:
            umo_status = f"🟢 УМО: {umo_str}"
    text += f"{umo_status}\n"

    # КБП проверки
    kbp_4_md_m = user_data.get('kbp_4_md_m')
    if kbp_4_md_m and hasattr(kbp_4_md_m, 'strftime'):
        kbp_4_md_m = kbp_4_md_m.strftime("%d.%m.%Y")
    text += line("КБП-4 (Ил-76 МД-М)", kbp_4_md_m, 6)
    
    kbp_7_md_m = user_data.get('kbp_7_md_m')
    if kbp_7_md_m and hasattr(kbp_7_md_m, 'strftime'):
        kbp_7_md_m = kbp_7_md_m.strftime("%d.%m.%Y")
    text += line("КБП-7 (Ил-76 МД-М)", kbp_7_md_m, 12)
    
    kbp_4_md_90a = user_data.get('kbp_4_md_90a')
    if kbp_4_md_90a and hasattr(kbp_4_md_90a, 'strftime'):
        kbp_4_md_90a = kbp_4_md_90a.strftime("%d.%m.%Y")
    text += line("КБП-4 (Ил-76 МД-90А)", kbp_4_md_90a, 6)
    
    kbp_7_md_90a = user_data.get('kbp_7_md_90a')
    if kbp_7_md_90a and hasattr(kbp_7_md_90a, 'strftime'):
        kbp_7_md_90a = kbp_7_md_90a.strftime("%d.%m.%Y")
    text += line("КБП-7 (Ил-76 МД-90А)", kbp_7_md_90a, 12)
    
    # Прыжки (может быть "освобожден")
    jumps = user_data.get('jumps_date')
    if jumps and hasattr(jumps, 'strftime'):
        jumps = jumps.strftime("%d.%m.%Y")
    text += line("Прыжки с ПДС", jumps, 12)
    
    return text

def check_flight_ban(user_data):
    """Проверяет запреты и возвращает список причин"""
    bans = []
    today = datetime.now().date()
    
    # Вспомогательная функция
    def is_expired(date_val, months):
        # Если освобожден - не считается просрочкой
        if isinstance(date_val, str) and date_val.lower() in ['освобожден', 'освобождён', 'осв']:
            return False
        
        if not date_val:
            return False
        
        # Парсим дату
        parsed = parse_date(date_val)
        if not parsed or parsed == 'exempt':
            return False
        
        return (today - parsed).days > months * 30

    # КБП проверки
    if is_expired(user_data.get('kbp_4_md_m'), 6):
        bans.append("🚫 Запрет полетов: КБП-4 (Ил-76 МД-М) просрочен")
    if is_expired
