import psycopg
from config import config

# Очищаем строку от SQLAlchemy-префиксов
raw_url = config.DATABASE_URL.replace("postgresql+psycopg://", "postgresql://").replace("postgresql+asyncpg://", "postgresql://")

print(f"Пробуем подключиться к:\n{raw_url.split('@')[-1] if '@' in raw_url else 'НЕВЕРНЫЙ ФОРМАТ URL'}\n")

try:
    with psycopg.connect(raw_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(" УСПЕШНОЕ ПОДКЛЮЧЕНИЕ К POSTGRESQL!")
            print(f"Версия сервера: {version[0]}")
except Exception as e:
    print(" РЕАЛЬНАЯ ПРИЧИНА ОШИБКИ:")
    print(e)