from datetime import date
import psycopg
from config import config

# Получаем чистую строку подключения для psycopg
def get_connection_url() -> str:
    url = config.DATABASE_URL
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgresql+psycopg://", "postgresql://")
    return url

def get_connection():
    return psycopg.connect(get_connection_url())

# 1. Создание таблиц при первом запуске
def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS exercises (
                    id SERIAL PRIMARY KEY,
                    canonical_name VARCHAR(128) UNIQUE NOT NULL,
                    default_unit VARCHAR(32) DEFAULT 'раз'
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workout_logs (
                    id SERIAL PRIMARY KEY,
                    log_date DATE NOT NULL,
                    exercise_id INTEGER REFERENCES exercises(id) ON DELETE CASCADE,
                    value DOUBLE PRECISION NOT NULL,
                    unit VARCHAR(32) DEFAULT 'раз',
                    notes VARCHAR(256),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

# 2. Получить список всех упражнений
def get_all_exercise_names() -> list[str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT canonical_name FROM exercises ORDER BY canonical_name;")
            rows = cur.fetchall()
            return [row[0] for row in rows]

# 3. Записать подход и получить суммарный итог за день
def save_workout_log(log_date: date, ex_name: str, value: float, unit: str, notes: str | None) -> float:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Получаем или создаем упражнение
            cur.execute(
                "INSERT INTO exercises (canonical_name, default_unit) VALUES (%s, %s) ON CONFLICT (canonical_name) DO NOTHING;",
                (ex_name, unit)
            )
            cur.execute("SELECT id FROM exercises WHERE canonical_name = %s;", (ex_name,))
            exercise_id = cur.fetchone()[0]

            # Сохраняем подход
            cur.execute(
                "INSERT INTO workout_logs (log_date, exercise_id, value, unit, notes) VALUES (%s, %s, %s, %s, %s);",
                (log_date, exercise_id, value, unit, notes)
            )

            # Считаем сумму за этот день
            cur.execute(
                "SELECT COALESCE(SUM(value), 0.0) FROM workout_logs WHERE exercise_id = %s AND log_date = %s;",
                (exercise_id, log_date)
            )
            daily_total = float(cur.fetchone()[0])
            conn.commit()
            return daily_total

# 4. Получить статистику за период
def get_workout_stats(start_date: date, end_date: date, exercise_name: str | None = None) -> list[tuple]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if exercise_name:
                query = """
                    SELECT l.log_date, e.canonical_name, SUM(l.value), l.unit
                    FROM workout_logs l
                    JOIN exercises e ON l.exercise_id = e.id
                    WHERE l.log_date >= %s AND l.log_date <= %s AND e.canonical_name = %s
                    GROUP BY l.log_date, e.canonical_name, l.unit
                    ORDER BY l.log_date;
                """
                cur.execute(query, (start_date, end_date, exercise_name))
            else:
                query = """
                    SELECT l.log_date, e.canonical_name, SUM(l.value), l.unit
                    FROM workout_logs l
                    JOIN exercises e ON l.exercise_id = e.id
                    WHERE l.log_date >= %s AND l.log_date <= %s
                    GROUP BY l.log_date, e.canonical_name, l.unit
                    ORDER BY l.log_date, e.canonical_name;
                """
                cur.execute(query, (start_date, end_date))
            return cur.fetchall()