import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from telegram.ext import Application, CommandHandler
import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

token = os.environ.get("TOKEN")

# Импортируем функции бота
from Bot_manager import (
    start, add_task, task_list, delete, edit, remind, show_remind, send_reminder, init_tasks, tasks
)

import os
if not os.path.exists("firebase-key.json") and os.environ.get("FIREBASE_KEY_JSON"):
    with open("firebase-key.json", "w") as f:
        f.write(os.environ["FIREBASE_KEY_JSON"])

from json_manager import load_data

# Запускаем Flask в фоновом потоке
web_thread = threading.Thread(target=run_web)
web_thread.daemon = True
web_thread.start()
print("Web server started on port 10000")

# Создаём и запускаем бота
application = Application.builder().token(token).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_task))
application.add_handler(CommandHandler("list", task_list))
application.add_handler(CommandHandler("delete", delete))
application.add_handler(CommandHandler("edit", edit))
application.add_handler(CommandHandler("remind", remind))
application.add_handler(CommandHandler("list_r", show_remind))

# Восстановление напоминаний
from Bot_manager import init_tasks
init_tasks()
from Bot_manager import tasks

if tasks is None:
    tasks = {}

for user_id, data in tasks.items():
    if not isinstance(data, dict):
        continue
    for rem in data.get("reminders", []):
        if rem.get("completed", False):
            continue
        if rem.get("task_index") >= len(data["tasks"]):
            continue
        dt = datetime.fromisoformat(rem["datetime_str"])
        if dt <= datetime.now(ZoneInfo("Europe/Berlin")):
            continue
        task_text = data["tasks"][rem["task_index"]]
        application.job_queue.run_once(
            callback=send_reminder,
            when=dt,
            data={
                "chat_id": rem["chat_id"],
                "task_text": task_text,
                "task_index": rem["task_index"],
                "datetime_str": rem["datetime_str"]
            }
        )

application.run_polling()