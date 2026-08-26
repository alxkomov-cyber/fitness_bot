from datetime import date, timedelta, datetime
import pytz
from config import config

def get_current_date() -> date:
    tz = pytz.timezone(config.TIMEZONE)
    return datetime.now(tz).date()

def get_period_dates(
    period: str,
    target_date: date | None = None,
    custom_start: date | None = None,
    custom_end: date | None = None
) -> tuple[date, date, str]:
    """Возвращает (start_date, end_date, заголовок_периода)."""
    today = get_current_date()
    
    if period == "custom" and custom_start and custom_end:
        return custom_start, custom_end, f"{custom_start.strftime('%d.%m')} – {custom_end.strftime('%d.%m')}"
    
    elif period == "day":
        d = target_date or today
        date_title = "Сегодня" if d == today else ("Вчера" if d == today - timedelta(days=1) else d.strftime("%d.%m.%Y"))
        return d, d, date_title
    
    elif period == "current_week":
        start = today - timedelta(days=today.weekday())
        return start, today, f"Текущая неделя ({start.strftime('%d.%m')} – {today.strftime('%d.%m')})"
    
    elif period == "last_week":
        end = today - timedelta(days=today.weekday() + 1)
        start = end - timedelta(days=6)
        return start, end, f"Прошлая неделя ({start.strftime('%d.%m')} – {end.strftime('%d.%m')})"
    
    elif period == "current_month":
        start = today.replace(day=1)
        return start, today, f"{today.strftime('%B %Y')} (Текущий месяц)"
    
    elif period == "last_month":
        first_of_this_month = today.replace(day=1)
        last_day_prev_month = first_of_this_month - timedelta(days=1)
        start = last_day_prev_month.replace(day=1)
        return start, last_day_prev_month, f"{start.strftime('%B %Y')} (Прошлый месяц)"
    
    return today, today, "Сегодня"
