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
        if not data:
            return {}
        # Преобразуем ключи из строк в int
        data = {int(k): v for k, v in data.items()}
        # Запускаем миграцию для всех пользователей
        data = migrate_user_data(data)
        # Проверяем и исправляем структуру
        testing(data)
        return data
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

def migrate_user_data(user_data):
    for user_id, user_dict in user_data.items():
        # 1. Переносим старые задачи в категорию "📁 Общее", если они есть
        if "tasks" in user_dict and isinstance(user_dict["tasks"], list):
            if "categories" not in user_dict:
                user_dict["categories"] = {}
            # Если категория "Общее" уже существует, добавляем задачи в неё, иначе создаём
            if "📁 Общее" not in user_dict["categories"]:
                user_dict["categories"]["📁 Общее"] = []
            user_dict["categories"]["📁 Общее"].extend(user_dict["tasks"])
            del user_dict["tasks"]

        # 2. Убеждаемся, что ключ "categories" существует (даже если пустой)
        if "categories" not in user_dict:
            user_dict["categories"] = {}

        # 3. Добавляем поле "category" в старые напоминания
        if "reminders" in user_dict:
            for reminder in user_dict["reminders"]:
                if "category" not in reminder:
                    reminder["category"] = "📁 Общее"
    return user_data