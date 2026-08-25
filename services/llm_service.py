import json
import re
from datetime import datetime, timedelta
import pytz
from groq import AsyncGroq
from config import config

groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = """Ты персональный ассистент по учету тренировок. Твоя задача — вернуть строго валидный JSON-объект.

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

СТРУКТУРА JSON ДЛЯ "LOG_WORKOUT":
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

СТРУКТУРА JSON ДЛЯ "GET_STATS":
{{
  "intent": "GET_STATS",
  "exercise_name": "Каноническое название",
  "period": "day",
  "target_date": "YYYY-MM-DD",
  "group_by": "days"
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

    response = await groq_client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content or ""

    # 1. Удаляем блок размышлений <think>...</think>, если модель его сгенерировала
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

    # 2. Очищаем от возможных Markdown-оберток (```json)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    # 3. Извлекаем чистый JSON от первой { до последней }
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if match:
        content = match.group(0)

    return json.loads(content)
