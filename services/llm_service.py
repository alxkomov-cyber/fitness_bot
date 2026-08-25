import json
from datetime import datetime, timedelta
import pytz
from groq import AsyncGroq
from config import config

# Используем единый клиент Groq с вашим ключом GROQ_API_KEY
groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = """Ты персональный ассистент по учету тренировок. Твоя задача — преобразовать запрос пользователя в строгий JSON.

Текущая дата и время: {current_datetime} ({day_of_week})
Существующие в базе упражнения пользователя:
{existing_exercises}

ПРАВИЛА ИНТЕРПРЕТАЦИИ:
1. ОПРЕДЕЛИ НАМЕРЕНИЕ (intent):
   - "LOG_WORKOUT": если пользователь сообщает о выполненном упражнении/подходе.
   - "GET_STATS": если пользователь спрашивает статистику, результаты или прогресс.
   - "UNKNOWN": если запрос не по теме спорта.

2. НОРМАЛИЗАЦИЯ НАЗВАНИЙ УПРАЖНЕНИЙ:
   - Приводи названия к каноническому виду в именительном падеже с заглавной буквы ("Отжимания от пола", "Приседания", "Скручивания на пресс").
   - ВАЖНО: Разделяй модификации! "Отжимания от пола" ≠ "Наклонные отжимания" (от стола/скамьи) ≠ "Отжимания узким хватом".
   - Если упражнение уже есть в списке существующих — выбери в точности его каноническое имя.

3. ПАРСИНГ ДАТ:
   - Если дата не названа — ставь сегодняшнюю ({current_date}).
   - "Вчера" -> {yesterday_date}.
   - Для запросов статистики точно определи тип периода: 'day', 'current_week', 'last_week', 'current_month', 'last_month'.

ФОРМАТ JSON ДЛЯ "LOG_WORKOUT":
{{
  "intent": "LOG_WORKOUT",
  "date": "YYYY-MM-DD",
  "entries": [
    {{
      "exercise_name": "Каноническое название",
      "value": 40.0,
      "unit": "раз",
      "notes": "по 5 на каждую ногу"
    }}
  ]
}}

ФОРМАТ JSON ДЛЯ "GET_STATS":
{{
  "intent": "GET_STATS",
  "exercise_name": "Каноническое название",
  "period": "day",
  "target_date": "YYYY-MM-DD",
  "group_by": "days"
}}

Возвращай ТОЛЬКО чистый JSON без markdown-кавычек (без ```json).
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

    response = await groq_client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    return json.loads(content.strip())
