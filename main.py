import os
import sys

# Создаём firebase-key.json из переменной окружения, если его нет (для Render)
if not os.path.exists("firebase-key.json") and os.environ.get("FIREBASE_KEY_JSON"):
    with open("firebase-key.json", "w") as f:
        f.write(os.environ["FIREBASE_KEY_JSON"])

import asyncio
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
load_dotenv()  # ← переменные окружения загружены
from flask import Flask
import threading
from datetime import datetime
from zoneinfo import ZoneInfo
from KeyBoard import *
from messagehandler import *

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

token = os.environ.get("TOKEN")

# Импортируем функции бота ПОСЛЕ загрузки .env
from Bot_manager import *

# Инициализируем данные из Firebase
init_tasks()

# Запускаем Flask в фоновом потоке
web_thread = threading.Thread(target=run_web)
web_thread.daemon = True
web_thread.start()
print("Web server started on port 10000")

# Создаём и запускаем бота
application = Application.builder().token(token).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(add_conv_handler)
application.add_handler(CommandHandler("list", task_list))
application.add_handler(MessageHandler(filters.Text(["📋 Список"]), task_list))
application.add_handler(delete_conv_handler)
application.add_handler(edit_conv_handler)
application.add_handler(remind_conv_handler)
application.add_handler(CommandHandler("list_r", show_remind))
application.add_handler(MessageHandler(filters.Text(["📌 Список напоминаний"]), show_remind))
application.add_handler(CommandHandler("delete_r", delete_complete_remind))
application.add_handler(MessageHandler(filters.Text(["🧹 Очистить выполненные"]), delete_complete_remind))
application.add_handler(CommandHandler("p", keyBoard))
application.add_handler(MessageHandler(filters.Text(["Скрыть меню"]), hide_keyBoard))
application.add_handler(create_category_conv)
application.add_handler(rename_category_conv)
application.add_handler(delete_cat_handler)   # было delete_category_conv
application.add_handler(CommandHandler("del_remind", delete_remind_start))
application.add_handler(CallbackQueryHandler(delete_remind_callback, pattern="^delrem\\|"))
application.add_handler(MessageHandler(filters.Text(["🗑 Удалить напоминание"]), delete_remind_start))


# Восстановление напоминаний
if tasks is None:
    tasks = {}

for user_id, data in tasks.items():
    if not isinstance(data, dict):
        continue
    for rem in data.get("reminders", []):
        if rem.get("completed", False):
            continue
        cat_name = rem.get("category", "📁 Общее")
        task_index = rem.get("task_index")
        if (cat_name not in data.get("categories", {}) or
            task_index >= len(data["categories"][cat_name])):
            continue
        dt = datetime.fromisoformat(rem["datetime_str"])
        if dt <= datetime.now(ZoneInfo("Europe/Berlin")):
            continue
        task_text = data["categories"][cat_name][task_index]
        application.job_queue.run_once(
            callback=send_reminder,
            when=dt,
            data={
                "chat_id": rem["chat_id"],
                "task_text": task_text,
                "task_index": task_index,
                "category": cat_name,
                "datetime_str": rem["datetime_str"]
            }
        )

application.run_polling()