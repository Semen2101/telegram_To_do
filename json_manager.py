import os
import json
import firebase_admin
from firebase_admin import credentials, db

# Инициализируем Firebase один раз
if not firebase_admin._apps:
    # Берём путь к файлу с ключами из переменной окружения
    cred_path = os.environ.get("FIREBASE_CRED_PATH", "firebase-key.json")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.environ.get("FIREBASE_DB_URL")
    })

def load_data():
    """Загружает все данные из корневого узла базы данных."""
    try:
        ref = db.reference('/')
        data = ref.get()
        for user_id, value in data.items():
            if isinstance(value, list):
                data[user_id] = {"tasks": value, "reminders": []}
        if data:
            # Firebase возвращает ключи как строки, нужно преобразовать в int
            return {int(k): v for k, v in data.items()}
        testing(data)
        return {}
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return {}

def save_data(data):
    testing(data)
    """Сохраняет все данные в корневой узел базы данных."""
    try:
        ref = db.reference('/')
        ref.set(data)
    except Exception as e:
        print(f"Ошибка сохранения данных: {e}")

def testing(data):
    for user_id, user_data in data.items():
        # Если данные — список (старый формат), преобразуем в словарь
        if isinstance(user_data, list):
            data[user_id] = {"tasks": user_data, "reminders": []}
        # Если данные — словарь, проверяем наличие ключей
        elif isinstance(user_data, dict):
            # setdefault создаст ключ с пустым списком, если его нет
            user_data.setdefault("tasks", [])
            user_data.setdefault("reminders", [])
        # На всякий случай: если данные другого типа, создаём пустую структуру
        else:
            data[user_id] = {"tasks": [], "reminders": []}