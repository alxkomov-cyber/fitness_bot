import json
import re
from datetime import datetime, timedelta
import pytz
from groq import AsyncGroq
from config import config

groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = """Ты персональный ассистент по учету тренировок. Твоя задача — вернуть строго JSON-объект без лишнего текста.

Текущая дата и время: {current_datetime} ({day_of_week})
Существующие в базе упражнения пользователя:
{existing_exercises}

ПРАВИЛА:
1. ОПРЕДЕЛИ НАМЕРЕНИЕ (intent):
   - "LOG_WORKOUT": запись выполненного упражнения/подхода.
   - "GET_STATS": запрос статистики или прогресса.
   - "UNKNOWN": если запрос не относится к спорту.

2. НОРМАЛИЗАЦИЯ УПРАЖНЕНИЙ:
   - Приводи названия к каноническому виду ("Отжимания от пола", "Приседания", "Скручивания на пресс").
   - Разделяй модификации: "Отжимания от пола" ≠ "Наклонные отжимания" ≠ "Отжимания узким хватом".

3. ПАРСИНГ ДАТ:
   - Сегодня: {current_date}
   - Вчера: {yesterday_date}

ФОРМАТ JSON ДЛЯ "LOG_WORKOUT":
{{
  "intent": "LOG_WORKOUT",
  "date": "YYYY-MM-DD",
  "entries": [
    {{
      "exercise_name": "Каноническое название",
      "value": 40.0,
      "unit": "раз",
      "notes": null
    }}
  ]
}}

ФОРМАТ JSON ДЛЯ "GET_STATS":
{{
  "intent": "GET_STATS",
  "exercise_name": "Каноническое название" (или null если за все),
  "period": "day" | "current_week" | "last_week" | "current_month" | "last_month" | "custom",
  "target_date": "YYYY-MM-DD" (если period='day', иначе null),
  "start_date": "YYYY-MM-DD" (если period='custom', например для "вчера и сегодня" -> {yesterday_date}),
  "end_date": "YYYY-MM-DD" (если period='custom', например для "вчера и сегодня" -> {current_date})
}}
"""

async def parse_user_request(text: str, existing_exercises: list[str]) -> dict:
    tz = pytz.timezone(config.TIMEZONE)
    now = datetime.now(tz)
    yesterday = now.date() - timedelta(days=1)
    
    prompt = SYSTEM_PROMPT.format(
        current_datetime=now.strftime("%Y-%m-%d %H:%M"),
        day_of_week=now.strftime("%A"),
        current_date=now.strftime("%Y-%m-%d"),
        yesterday_date=yesterday.strftime("%Y-%m-%d"),
        existing_exercises=", ".join(existing_exercises) if existing_exercises else "База пуста"
    )

    # Не передаем response_format json_object, чтобы Groq не падал с 400 ошибкой
    response = await groq_client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content or ""

    # Удаляем блок размышлений <think>...</think>
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

    # Очищаем Markdown
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    # Извлекаем JSON по скобкам {}
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if match:
        content = match.group(0)

    return json.loads(content)
