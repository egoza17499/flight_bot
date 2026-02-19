from datetime import datetime, timedelta

def parse_date(date_val):
    """
    Преобразует значение в объект date.
    """
    if date_val is None:
        return None
    
    if isinstance(date_val, datetime):
        return date_val.date()
    
    if isinstance(date_val, str):
        # Проверяем на "освобожден"
        if date_val.lower() in ['освобожден', 'освобождён', 'осв']:
            return 'exempt'
        
        # Пытаемся распарсить дату
        try:
            return datetime.strptime(date_val, "%d.%m.%Y").date()
        except ValueError:
            return None
    
    if hasattr(date_val, 'strftime'):
        return date_val
    
    return None

def check_status(date_val, limit_months):
    """
    Проверяет статус даты относительно текущего времени.
    Возвращает: (цвет, сообщение)
    - green: действует (до limit_months)
    - yellow: осталось < 30 дней
    - red: просрочено
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
    
    # Считаем сколько дней прошло от даты
    days_passed = (today - date_val).days
    limit_days = limit_months * 30
    
    # Сколько дней осталось до истечения
    days_left = limit_days - days_passed
    
    if days_passed < 0:
        # Дата в будущем
        return 'green', f"Действует (осталось {limit_days} дн.)"
    elif days_left < 0:
        # Просрочено
        return 'red', f"Просрочено на {abs(days_left)} дн."
    elif days_left < 30:
        # Осталось мало времени
        return 'yellow', f"Осталось {days_left} дн."
    else:
        # Действует
        return 'green', f"Действует (осталось {days_left} дн.)"

def generate_profile_text(user_data):
    """Генерирует текст профиля с цветовой индикацией"""
    text = f"👤 <b>{user_data['fio']}</b>\n"
    text += f"🎖 <b>Звание:</b> {user_data['rank']}\n"
    text += f"🏅 <b>Квалификация:</b> {user_data['qual_rank']}\n\n"
    
    # Парсим все даты
    vacation_end = parse_date(user_data.get('vacation_end'))
    vlk_date = parse_date(user_data.get('vlk_date'))
    umo_date = parse_date(user_data.get('umo_date'))
    kbp_4_md_m = parse_date(user_data.get('kbp_4_md_m'))
    kbp_7_md_m = parse_date(user_data.get('kbp_7_md_m'))
    kbp_4_md_90a = parse_date(user_data.get('kbp_4_md_90a'))
    kbp_7_md_90a = parse_date(user_data.get('kbp_7_md_90a'))
    jumps = user_data.get('jumps_date')  # Может быть "освобожден"
    
    today = datetime.now().date()
    
    # Вычисляем предельную дату для УМО (ВЛК + 12 месяцев)
    vlk_expiry_date = None
    if vlk_date and vlk_date != 'exempt':
        vlk_expiry_date = vlk_date + timedelta(days=365)  # 12 месяцев
    
    # Функция для красивой строки
    def line(name, date_val, limit_m):
        # Проверяем на "освобожден"
        if isinstance(date_val, str) and date_val.lower() in ['освобожден', 'освобождён', 'осв']:
            return f"🔵 <b>{name}:</b> Освобожден\n"
        
        if date_val is None:
            return f"⚪ <b>{name}:</b> Нет данных\n"
        
        # Стандартная проверка
        status, msg = check_status(date_val, limit_m)
        color_map = {'green': '🟢', 'yellow': '🟡', 'red': '🔴', 'blue': '🔵'}
        date_str = date_val.strftime("%d.%m.%Y") if hasattr(date_val, 'strftime') else str(date_val)
        return f"{color_map.get(status, '⚪')} <b>{name}:</b> {date_str} ({msg})\n"
    
    # Функция для УМО (проверка относительно ВЛК + 12 месяцев)
    def umo_line(name, umo_date_val, vlk_expiry):
        if isinstance(umo_date_val, str) and umo_date_val.lower() in ['освобожден', 'освобождён', 'осв']:
            return f"🔵 <b>{name}:</b> Освобожден\n"
        
        if umo_date_val is None:
            return f"⚪ <b>{name}:</b> Не пройдено\n"
        
        if vlk_expiry is None:
            return f"⚪ <b>{name}:</b> Нет данных ВЛК\n"
        
        # Проверяем УМО относительно даты ВЛК + 12 месяцев
        days_until_vlk_expiry = (vlk_expiry - today).days
        umo_str = umo_date_val.strftime('%d.%m.%Y') if hasattr(umo_date_val, 'strftime') else str(umo_date_val)
        
        if days_until_vlk_expiry < 0:
            # ВЛК просрочена, значит УМО тоже просрочено
            return f"🔴 <b>{name}:</b> {umo_str} (Просрочено вместе с ВЛК)\n"
        elif days_until_vlk_expiry < 30:
            return f"🟡 <b>{name}:</b> {umo_str} (Осталось {days_until_vlk_expiry} дн.)\n"
        else:
            return f"🟢 <b>{name}:</b> {umo_str} (Действует, осталось {days_until_vlk_expiry} дн.)\n"

    # Отпуск (12 месяцев от даты окончания)
    text += line("Отпуск (конец):", vacation_end, 12)
    
    # ВЛК с учетом УМО
    if vlk_date is None:
        text += "⚪ <b>ВЛК:</b> Нет данных\n"
    elif vlk_date == 'exempt':
        text += "🔵 <b>ВЛК:</b> Освобожден\n"
    else:
        days_since_vlk = (today - vlk_date).days
        
        if days_since_vlk > 365:  # > 12 месяцев
            text += f"🔴 <b>ВЛК:</b> {vlk_date.strftime('%d.%m.%Y')} (Просрочена на {days_since_vlk - 365} дн.)\n"
        elif days_since_vlk > 180 and (umo_date is None or umo_date == 'exempt'):  # > 6 мес и нет УМО
            text += f"🔴 <b>ВЛК:</b> {vlk_date.strftime('%d.%m.%Y')} (ТРЕБУЕТСЯ УМО)\n"
        elif days_since_vlk > 180 and umo_date is not None and umo_date != 'exempt':  # > 6 мес но есть УМО
            remaining = 365 - days_since_vlk
            text += f"🟢 <b>ВЛК:</b> {vlk_date.strftime('%d.%m.%Y')} (Действует с УМО, осталось {remaining} дн.)\n"
        else:  # <= 6 месяцев
            remaining = 180 - days_since_vlk
            text += f"🟢 <b>ВЛК:</b> {vlk_date.strftime('%d.%m.%Y')} (Действует, осталось {remaining} дн.)\n"
    
    # УМО (действует только если ВЛК действительна, и до даты ВЛК + 12 месяцев)
    text += umo_line("УМО:", umo_date, vlk_expiry_date)
    
    # КБП проверки
    text += line("КБП-4 (Ил-76 МД-М):", kbp_4_md_m, 6)
    text += line("КБП-7 (Ил-76 МД-М):", kbp_7_md_m, 12)
    text += line("КБП-4 (Ил-76 МД-90А):", kbp_4_md_90a, 6)
    # Для КБП-7 МД-90А используем стандартную проверку (12 месяцев)
    text += line("КБП-7 (Ил-76 МД-90А):", kbp_7_md_90a, 12)
    
    # Прыжки (может быть "освобожден")
    if isinstance(jumps, str) and jumps.lower() in ['освобожден', 'освобождён', 'осв']:
        text += "🔵 <b>Прыжки с ПДС:</b> Освобожден\n"
    else:
        jumps_parsed = parse_date(jumps)
        text += line("Прыжки с ПДС:", jumps_parsed, 12)
    
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
        
        days_passed = (today - parsed).days
        return days_passed > months * 30

    # КБП проверки
    if is_expired(user_data.get('kbp_4_md_m'), 6):
        bans.append("🚫 Запрет полетов: КБП-4 (Ил-76 МД-М) просрочен")
    if is_expired(user_data.get('kbp_7_md_m'), 12):
        bans.append("🚫 Запрет полетов: КБП-7 (Ил-76 МД-М) просрочен")
    if is_expired(user_data.get('kbp_4_md_90a'), 6):
        bans.append("🚫 Запрет полетов: КБП-4 (Ил-76 МД-90А) просрочен")
    if is_expired(user_data.get('kbp_7_md_90a'), 12):
        bans.append("🚫 Запрет полетов: КБП-7 (Ил-76 МД-90А) просрочен")
        
    # ВЛК и УМО
    vlk = parse_date(user_data.get('vlk_date'))
    umo = parse_date(user_data.get('umo_date'))
    
    if vlk and vlk != 'exempt':
        days_since_vlk = (today - vlk).days
        
        if days_since_vlk > 365:  # > 12 месяцев
            bans.append("🚫 Запрет полетов: ВЛК просрочена (>12 мес)")
        elif days_since_vlk > 180 and (umo is None or umo == 'exempt'):  # > 6 мес и нет УМО
            bans.append("🚫 Запрет полетов: ВЛК > 6 мес без УМО")
             
    if is_expired(user_data.get('vacation_end'), 12):
        bans.append("🚫 Запрет полетов: Отпуск (>12 мес)")
        
    # Прыжки - проверяем только если не освобожден
    jumps = user_data.get('jumps_date')
    if jumps and not (isinstance(jumps, str) and jumps.lower() in ['освобожден', 'освобождён', 'осв']):
        if is_expired(jumps, 12):
            bans.append("🚫 Запрет полетов: Прыжки (>12 мес)")
        
    return bans
