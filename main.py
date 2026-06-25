import asyncio
from flask import Flask
import threading
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

token = os.getenv("TOKEN")
tasks = {}

async def start(update : Update, context : ContextTypes.DEFAULT_TYPE) :
    await update.message.reply_text("Привет! Я мопс!")
  
async def add_task(update : Update, context : ContextTypes.DEFAULT_TYPE) :
    user_id = update.message.from_user.id
    if user_id not in tasks :
        tasks[user_id] = []

    if not context.args :
        await update.message.reply_text("Введите задачу после команды /add")
    else :
        task_text = " ".join(context.args)
        tasks[user_id].append(task_text)
        print(tasks)
        await update.message.reply_text(f"Задача добавлена: {task_text}")

async def task_list(update : Update, context : ContextTypes.DEFAULT_TYPE) :
    user_id = update.message.from_user.id
    if user_id not in tasks or not tasks[user_id] :
        tasks[user_id] = []
        await update.message.reply_text("У вас нету задач") 
    else :
        user_task = tasks[user_id]
        message_ = "\n".join(f"{i}. {task}" for i, task in enumerate(user_task, start=1))
        await update.message.reply_text(message_)

async def delete(update : Update, context : ContextTypes.DEFAULT_TYPE) :
    user_id = update.message.from_user.id
    if user_id not in tasks or not tasks[user_id] :
        tasks[user_id] = []
        await update.message.reply_text("У вас нету задач")
    else :
        if not context.args :
            await update.message.reply_text("введите номер задачи после команды /delete ")
        try :
            index = int(context.args[0]) -1
            if 0 <= index < len(tasks[user_id]):
                removed_task = tasks[user_id].pop(index)
                print(removed_task)
                await update.message.reply_text(f"Задача '{removed_task}' удалена.")
            else :
                await update.message.reply_text("Задачи с таким номером не существует")
        except ValueError:
            await update.message.reply_text("Номер должен быть числом")

async def edit(update : Update, context : ContextTypes.DEFAULT_TYPE) :
    user_id = update.message.from_user.id
    if user_id not in tasks or not tasks[user_id] :
        tasks[user_id] = []
        await update.message.reply_text("У вас нету задач")
    else :
        if not context.args :
            await update.message.reply_text("Укажите номер задачи и новый текст после команды /edit ")
        try :
            index = int(context.args[0]) - 1
            if 0 <= index < len(tasks[user_id]) and len(context.args) >= 2:
                old = tasks[user_id][index]
                new_text = " ".join(context.args[1:])
                tasks[user_id][index] = new_text
                await update.message.reply_text(f"Задача '{old}' изменена на '{new_text}'.")
            else :
                await update.message.reply_text("Введите новый текст задачи после команды /edit")    
        except ValueError :
            await update.message.reply_text("Номер должен быть числом")

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    user_id = update.message.from_user.id
    if user_id not in tasks or not tasks[user_id] :
        tasks[user_id] = []
        await update.message.reply_text("У вас нету задач")
    else :
        if not context.args or len(context.args) != 3:
            await update.message.reply_text("/remind НОМЕР ГГГГ-ММ-ДД ЧЧ:ММ, просьба соблюдать строгий синтаксис в дате тире во времени двоеточие")
        try :
            index = int(context.args[0]) - 1
            if 0 <= index < len(tasks[user_id]):
                data = context.args[1] + " " + context.args[2]
                data_time = datetime.strptime(data , "%Y-%m-%d %H:%M")
                task_text = tasks[user_id][index]
                context.job_queue.run_once(
                    callback=send_reminder,
                    when=data_time,
                    data={'chat_id': update.message.chat_id, 'task_text': task_text}
                )
                await update.message.reply_text(f"Напоминание установлено на {data}")
            else :
                await update.message.reply_text("такой задачи нету ")
            
        except ValueError :
            await update.message.reply_text("Используйте только числа /remind НОМЕР ГГГГ-ММ-ДД ЧЧ:ММ")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data['chat_id']
    task_text = job_data['task_text']
    await context.bot.send_message(chat_id=chat_id, text=f"Напоминание: {task_text}")

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

web_thread = threading.Thread(target=run_web)
web_thread.daemon = True
web_thread.start()

application = Application.builder().token(token).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_task))
application.add_handler(CommandHandler("list", task_list))
application.add_handler(CommandHandler("delete", delete))
application.add_handler(CommandHandler("edit", edit))
application.add_handler(CommandHandler("remind", remind))

application.run_polling()
