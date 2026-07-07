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
        if data:
            # Firebase возвращает ключи как строки, нужно преобразовать в int
            return {int(k): v for k, v in data.items()}
        return {}
    except Exception as e:
        print(f"Ошибка загрузки данных: {e}")
        return {}

def save_data(data):
    """Сохраняет все данные в корневой узел базы данных."""
    try:
        ref = db.reference('/')
        ref.set(data)
    except Exception as e:
        print(f"Ошибка сохранения данных: {e}")