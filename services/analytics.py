from datetime import date, timedelta
import calendar
import pytz
from config import config

def get_current_date() -> date:
    tz = pytz.timezone(config.TIMEZONE)
    return datetime.now(tz).date()

from datetime import datetime

def get_period_dates(period: str, target_date: date | None = None) -> tuple[date, date, str]:
    """Возвращает (start_date, end_date, human_readable_title) с учетом правил Пн-Вс и календарных месяцев."""
    today = get_current_date()
    
    if period == "day":
        d = target_date or today
        return d, d, d.strftime("%d.%m.%Y")
    
    elif period == "current_week":
        # Пн текущей недели до сегодня
        start = today - timedelta(days=today.weekday())
        return start, today, f"Текущая неделя ({start.strftime('%d.%m')} – {today.strftime('%d.%m')})"
    
    elif period == "last_week":
        # Строго полный Пн-Вс прошлой недели
        end = today - timedelta(days=today.weekday() + 1)
        start = end - timedelta(days=6)
        return start, end, f"Прошлая неделя ({start.strftime('%d.%m')} – {end.strftime('%d.%m')})"
    
    elif period == "current_month":
        # С 1-го числа текущего месяца по сегодня
        start = today.replace(day=1)
        return start, today, f"{today.strftime('%B %Y')} (Текущий месяц)"
    
    elif period == "last_month":
        # Полный предыдущий календарный месяц
        first_of_this_month = today.replace(day=1)
        last_day_prev_month = first_of_this_month - timedelta(days=1)
        start = last_day_prev_month.replace(day=1)
        return start, last_day_prev_month, f"{start.strftime('%B %Y')} (Прошлый месяц)"
    
    return today, today, "Сегодня"