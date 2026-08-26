from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from db.database import get_all_exercise_names, save_workout_log, get_workout_stats
from services.stt_service import transcribe_voice
from services.llm_service import parse_user_request
from services.analytics import get_period_dates, get_current_date

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 **Привет! Я твой персональный фитнес-трекер.**\n\n"
        "🎙 Надиктовывай голосовыми или пиши текстом, например:\n"
        "• *«Отжался от пола 40 раз и присел 30 раз»*\n"
        "• *«Запиши, что вчера сделал скручивания на пресс 50 раз»*\n"
        "• *«Сколько я отжался на прошлой неделе?»*\n"
        "• *«Статистика за вчера и сегодня»*",
        parse_mode="Markdown"
    )

@router.message(F.voice | F.text)
async def process_user_input(message: Message):
    wait_msg = await message.answer("🔄 Обрабатываю...")
    
    # 1. Распознавание речи / текста
    if message.voice:
        try:
            file = await message.bot.get_file(message.voice.file_id)
            file_bytes = await message.bot.download_file(file.file_path)
            raw_text = await transcribe_voice(file_bytes.read())
        except Exception as e:
            await wait_msg.edit_text(f"❌ Ошибка распознавания аудио: {e}")
            return
    else:
        raw_text = message.text

    # 2. LLM обработка (Qwen)
    exercises = get_all_exercise_names()
    try:
        data = await parse_user_request(raw_text, exercises)
    except Exception as e:
        await wait_msg.edit_text(f"❌ Ошибка анализа запроса: {e}")
        return

    intent = data.get("intent")

    # 3. Запись тренировки
    if intent == "LOG_WORKOUT":
        log_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        response_lines = []

        for entry in data.get("entries", []):
            ex_name = entry["exercise_name"]
            val = float(entry["value"])
            unit = entry.get("unit", "раз")
            notes = entry.get("notes")

            daily_total = save_workout_log(log_date, ex_name, val, unit, notes)

            note_str = f" ({notes})" if notes else ""
            response_lines.append(
                f"• **{ex_name}**: +{val:g} {unit}{note_str}\n"
                f"  📊 *Всего за день:* **{daily_total:g} {unit}**"
            )

        date_str = "Сегодня" if log_date == get_current_date() else log_date.strftime("%d.%m.%Y")
        reply = f"✅ **Записано!** 📅 *{date_str}*\n\n" + "\n\n".join(response_lines)
        await wait_msg.edit_text(reply, parse_mode="Markdown")

    # 4. Запрос статистики
    elif intent == "GET_STATS":
        period = data.get("period", "day")
        
        target_d = datetime.strptime(data["target_date"], "%Y-%m-%d").date() if data.get("target_date") else None
        custom_s = datetime.strptime(data["start_date"], "%Y-%m-%d").date() if data.get("start_date") else None
        custom_e = datetime.strptime(data["end_date"], "%Y-%m-%d").date() if data.get("end_date") else None
        
        start_d, end_d, title = get_period_dates(period, target_d, custom_s, custom_e)
        ex_name = data.get("exercise_name")

        results = get_workout_stats(start_d, end_d, ex_name)

        if not results:
            await wait_msg.edit_text(f"🔍 За период **{title}** записей не найдено.", parse_mode="Markdown")
            return

        reply = f"📊 **Статистика: {ex_name or 'Все упражнения'}**\n🗓 *Период:* {title}\n\n"
        reply += "```text\n"
        reply += f"{'Дата':<10} | {'Упражнение':<18} | {'Кол-во'}\n"
        reply += "-" * 38 + "\n"
        
        total_sum = 0
        for r_date, r_name, r_val, r_unit in results:
            total_sum += r_val
            name_cut = (r_name[:16] + "..") if len(r_name) > 18 else r_name
            reply += f"{r_date.strftime('%d.%m'):<10} | {name_cut:<18} | {r_val:g} {r_unit}\n"
        
        reply += "-" * 38 + "\n"
        reply += f"ИТОГО: {total_sum:g}\n"
        reply += "```"

        await wait_msg.edit_text(reply, parse_mode="Markdown")
    else:
        await wait_msg.edit_text("🤖 Я не понял запрос. Надиктуйте упражнение или спросите статистику.")
