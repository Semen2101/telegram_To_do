from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, date
import textwrap
from zoneinfo import ZoneInfo
from json_manager import *
from KeyBoard import *

tasks = None

def init_tasks():
    global tasks
    raw = load_data()
    tasks = {int(k): v for k, v in raw.items()}
    if tasks is None:
        tasks = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.username or "пользователь" 
    message = textwrap.dedent(f"""\
        Привет, {user_name}!
        Вот все команды для работы с ботом (v3 relese auto delete message)):
        
        1. /add "ваша задача" — добавит задачу в список
        2. /list — покажет все ваши задачи с номерами
        3. /delete "номер" — удалит задачу по номеру
        4. /edit "номер" "новый текст" — изменит задачу
        5. /remind "номер" "дата" "время" — установит напоминание
           (формат: /remind 1 2006-12-08 03:15)
        6. /list_r — покажет все ваши напоминания
        7. /delete_r — удалит все выполненные напоминания
        8. /p — открыть меню команд
    """)
    await update.message.reply_text(message)
    await keyBoard(update, context)

async def add_task(update : Update, context : ContextTypes.DEFAULT_TYPE) :
    if tasks is None:
        init_tasks()
    user_id = update.message.from_user.id
    if user_id not in tasks :
        tasks[user_id] = {"tasks": [], "reminders": []}

    if not context.args :
        await send_self_destruct_message(update, context, "Введите задачу после команды /add")
    else :
        task_text = " ".join(context.args)
        tasks[user_id]["tasks"].append(task_text)
        save_data(tasks)
        print(tasks)

async def task_list(update : Update, context : ContextTypes.DEFAULT_TYPE) :
    if tasks is None:
        init_tasks()
    user_id = update.message.from_user.id
    if user_id not in tasks or not tasks[user_id]["tasks"] :
        tasks[user_id] = {"tasks": [], "reminders": []}
        await send_self_destruct_message(update, context, "У вас нету задач") 
    else :
        user_task = tasks[user_id]["tasks"]
        message_ = "\n".join(f"{i}. {task}" for i, task in enumerate(user_task, start=1))
        await send_self_destruct_message(update, context, message_)

async def delete(update : Update, context : ContextTypes.DEFAULT_TYPE) :
    if tasks is None:
        init_tasks()
    user_id = update.message.from_user.id
    if user_id not in tasks or not tasks[user_id]["tasks"] :
        tasks[user_id] = {"tasks": [], "reminders": []}
        await send_self_destruct_message(update, context, "У вас нету задач")
    else :
        if not context.args :
            await send_self_destruct_message(update, context, "введите номер задачи после команды /delete ")
        try :
            index = int(context.args[0]) -1
            if 0 <= index < len(tasks[user_id]["tasks"]):
                removed_task = tasks[user_id]["tasks"].pop(index)
                save_data(tasks)
                print(removed_task)
                await send_self_destruct_message(update, context, f"Задача '{removed_task}' удалена!")
            else :
                await send_self_destruct_message(update, context, "Задачи с таким номером не существует")
        except ValueError:
            await send_self_destruct_message(update, context, "Номер должен быть числом")

async def edit(update : Update, context : ContextTypes.DEFAULT_TYPE) :
    if tasks is None:
        init_tasks()
    user_id = update.message.from_user.id
    if user_id not in tasks or not tasks[user_id]["tasks"] :
        tasks[user_id] = {"tasks": [], "reminders": []}
        await send_self_destruct_message(update, context, "У вас нету задач")
    else :
        if not context.args :
            await send_self_destruct_message(update, context, "Укажите номер задачи и новый текст после команды /edit ")
        try :
            index = int(context.args[0]) - 1
            if 0 <= index < len(tasks[user_id]["tasks"]) and len(context.args) >= 2:
                old = tasks[user_id]["tasks"][index]
                new_text = " ".join(context.args[1:])
                tasks[user_id]["tasks"][index] = new_text
                save_data(tasks)
                await send_self_destruct_message(update, context, f"Задача '{old}' изменена на '{new_text}'.")
            else :
                await send_self_destruct_message(update, context, "Введите новый текст задачи после команды /edit")    
        except ValueError :
            await send_self_destruct_message(update, context, "Номер должен быть числом")

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    if tasks is None:
        init_tasks()
    user_id = update.message.from_user.id
    if user_id not in tasks or not tasks[user_id]["tasks"] :
        tasks[user_id] = {"tasks": [], "reminders": []}
        await send_self_destruct_message(update, context, "У вас нету задач")
    else :
        if not context.args or len(context.args) != 3:
            await send_self_destruct_message(update, context, "/remind НОМЕР ГГГГ-ММ-ДД ЧЧ:ММ, просьба соблюдать строгий синтаксис в дате тире во времени двоеточие")
        try:
            index = int(context.args[0]) - 1
            if 0 <= index < len(tasks[user_id]["tasks"]):
                
                data = context.args[1] + " " + context.args[2]
                naive_dt = datetime.strptime(data, "%Y-%m-%d %H:%M")
                data_time = naive_dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
                
                task_text = tasks[user_id]["tasks"][index]
                
                print("DEBUG: выполняется run_once...")
                print("DEBUG data_time:", data_time)
                print("DEBUG now (local):", datetime.now(ZoneInfo("Europe/Berlin")))
                
                if data_time <= datetime.now(ZoneInfo("Europe/Berlin")):
                        await send_self_destruct_message(update, context, "Это время уже прошло. Напоминание не установлено.")
                        return
                
                context.job_queue.run_once(
                callback=send_reminder,
                when=data_time,
                data={
                    "chat_id": update.message.chat_id,
                    "task_text": task_text,
                    "task_index": index,
                    "datetime_str": data_time.isoformat()
                }
                )
                print("DEBUG: run_once выполнена успешно")

                reminder_data = {
                    "task_index": index,
                    "datetime_str": data_time.isoformat(),
                    "chat_id": update.message.chat_id,
                    "completed": False
                }
                if "reminders" not in tasks[user_id]:
                    tasks[user_id]["reminders"] = []

                tasks[user_id]["reminders"].append(reminder_data)
                save_data(tasks)

                await send_self_destruct_message(update, context, f"Напоминание установлено на {data}")
            else:
                await send_self_destruct_message(update, context, "такой задачи нету")
        except ValueError:
            await send_self_destruct_message(update, context, "Неверный формат даты/времени. Используйте /remind НОМЕР ГГГГ-ММ-ДД ЧЧ:ММ")
        except Exception as e:
            import traceback
            print("!!! ОШИБКА в remind:")
            traceback.print_exc()
            await send_self_destruct_message(update, context, f"Произошла внутренняя ошибка: {e}")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    if tasks is None:
        init_tasks()    
    print("=== CALLBACK CALLED ===")
    try:
        job_data = context.job.data
        chat_id = job_data['chat_id']
        task_text = job_data['task_text']
        sent_message = await context.bot.send_message(chat_id=chat_id, text=f"Напоминание: {task_text}")
        context.job_queue.run_once(
            delete_message_callback,
            when=600,  # 10 минут
            data={"chat_id": sent_message.chat_id, "message_id": sent_message.message_id})

        reminders = tasks[chat_id]["reminders"]
        for rem in reminders :
            if rem["task_index"] == job_data["task_index"] and rem["datetime_str"] == job_data["datetime_str"] :
                rem["completed"] = True
                break
        save_data(tasks)
    except Exception as e :
        print(f"ОШИБКА в send_reminder: {e}")

async def show_remind(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    if tasks is None:
        init_tasks()
    user_id = update.message.from_user.id

    if user_id not in tasks:
        tasks[user_id] = {"tasks": [], "reminders": []}
        await send_self_destruct_message(update, context, "У вас нет активных напоминаний.")
        return

    user_data = tasks[user_id]
    reminders = user_data.get("reminders", [])
    tasks_list = user_data.get("tasks", [])

    if not reminders:
        await send_self_destruct_message(update, context, "У вас нет активных напоминаний.")
        return
    
    message_lines = ["📋 Ваши напоминания:"]
    for i, remind in enumerate(reminders, start=1):
        task_index = remind.get("task_index")
        # Проверяем, существует ли задача с таким индексом
        if task_index is not None and 0 <= task_index < len(tasks_list):
            task_text = tasks_list[task_index]
        else:
            task_text = "(задача удалена)"

        # Преобразуем дату в читаемый формат (если datetime_str есть)
        datetime_str = remind.get("datetime_str", "")
        try:
            # Парсим ISO строку и форматируем под нужный вид
            dt = datetime.fromisoformat(datetime_str)
            formatted_date = dt.strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError):
            formatted_date = datetime_str  # если не удалось распарсить, выводим как есть

        completed = remind.get("completed", False)
        status = "✅" if completed else "❌"

        # Собираем строку
        line = f'{i}. "{task_text}" В: {formatted_date} completed: {completed} {status}'
        message_lines.append(line)

    await send_self_destruct_message(update, context, "\n".join(message_lines))

async def delete_complete_remind(update: Update, context: ContextTypes.DEFAULT_TYPE) :
    if tasks is None:
        init_tasks()
    user_id = update.message.from_user.id
    if user_id not in tasks:
        tasks[user_id] = {"tasks": [], "reminders": []}
        await send_self_destruct_message(update, context, "У вас нет напоминаний.")
        return
    
    old_count = len(tasks[user_id]["reminders"])
    tasks[user_id]["reminders"] = [
        rem for rem in tasks[user_id]["reminders"]
        if not rem.get("completed")
    ]
    deleted_count = old_count - len(tasks[user_id]["reminders"])
    
    if deleted_count > 0:
        save_data(tasks)
        await send_self_destruct_message(update, context, f"Удалено выполненных напоминаний: {deleted_count}")
    else:
        await send_self_destruct_message(update, context, "Нет выполненных напоминаний для удаления.")


######################################################################################################################################################
######################################################################################################################################################
######################################################################################################################################################

WAITING_FOR_TASK_TEXT = 1

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_self_destruct_message(update, context, "Введите текст задачи (или /cancel для отмены):")
    return WAITING_FOR_TASK_TEXT

async def add_task_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_text = update.message.text
    context.args = update.message.text.split()
    await add_task(update, context)
    await send_self_destruct_message(update, context, f"Задача '{task_text}' добавлена!")
    return ConversationHandler.END

######################################################################################################################################################

WAITING_FOR_TASK_NUM = 2

async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_self_destruct_message(update, context, "Введите номер задачи (или /cancel для отмены):")
    return WAITING_FOR_TASK_NUM

async def delete_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    delete_num = update.message.text
    context.args = [update.message.text]
    await delete(update, context)
    return ConversationHandler.END

######################################################################################################################################################

WAITING_FOR_EDIT_NUM1 = 3
WAITING_FOR_EDIT_TEXT1 = 4

async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_self_destruct_message(update, context, "Введите номер задачи для редактирования (или /cancel для отмены):")
    return WAITING_FOR_EDIT_NUM1

async def edit_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        index = int(update.message.text) - 1
        if user_id in tasks and 0 <= index < len(tasks[user_id]["tasks"]):
            # Сохраняем номер для следующего шага
            context.user_data['edit_index'] = index
            await send_self_destruct_message(update, context, "Введите новый текст задачи:")
            return WAITING_FOR_EDIT_TEXT1
        else:
            await send_self_destruct_message(update, context, "Неверный номер. Попробуйте снова (или /cancel):")
            return None  # остаёмся в том же состоянии
    except ValueError:
        await send_self_destruct_message(update, context, "Это не число. Введите номер задачи:")
        return None

async def edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    index = context.user_data.get('edit_index')
    if index is None:
        await send_self_destruct_message(update, context, "Ошибка: не найден номер задачи. Диалог отменён.")
        return ConversationHandler.END
    
    # Эмулируем команду /edit <номер> <новый текст>
    context.args = [str(index + 1), new_text]
    
    # Вызываем старую функцию edit
    await edit(update, context)
    
    # Очищаем временные данные
    context.user_data.clear()
    return ConversationHandler.END

######################################################################################################################################################

WAITING_FOR_REMIND_NUM = 5
WAITING_FOR_REMIND_DATETIME = 6
WAITING_FOR_REMIND_CALENDAR = 7

async def remind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in tasks or not tasks[user_id].get("tasks"):
        await send_self_destruct_message(update, context, "У вас нет задач для напоминания.")
        return ConversationHandler.END

    task_list = "\n".join(
        f"{i}. {task}" for i, task in enumerate(tasks[user_id]["tasks"], start=1)
    )
    await send_self_destruct_message(update, context, 
        f"Ваши задачи:\n{task_list}\n\nВведите номер задачи (или /cancel для отмены):"
    )
    return WAITING_FOR_REMIND_NUM

async def remind_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        index = int(update.message.text) - 1
        if 0 <= index < len(tasks[user_id]["tasks"]):
            context.user_data["original_update"] = update
            # ЗАДАЧА СУЩЕСТВУЕТ
            context.user_data["remind_index"] = index
            # СЮДА ПОТОМ ДОБАВИМ КЛАВИАТУРУ
            year = datetime.now().year
            btn = InlineKeyboardButton(f"{year}", callback_data=f"remind_calendar|year|{year}|None|None|None|None")
            btn1 = InlineKeyboardButton(f"{year+1}", callback_data=f"remind_calendar|year|{year+1}|None|None|None|None")
            btn2 = InlineKeyboardButton(f"{year+2}", callback_data=f"remind_calendar|year|{year+2}|None|None|None|None")
            btn_cancel = InlineKeyboardButton("Отмена", callback_data="remind_cancel")
            buttons_rows = [
                [btn, btn1, btn2], [btn_cancel]
            ]

            await send_self_destruct_message(update, context, "Выберите год:", reply_markup=InlineKeyboardMarkup(buttons_rows))

            return WAITING_FOR_REMIND_CALENDAR
        else:
            # НЕВЕРНЫЙ НОМЕР
            await send_self_destruct_message(update, context, "Такой задачи не существует. Введите номер существующей задачи (или /cancel).")
            return None
    except ValueError:
        await send_self_destruct_message(update, context, "Введите номер задачи числом (или /cancel).")
        return None
    
async def remind_calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "ignore":
        await query.answer()
        return None

    if data == "remind_cancel":
        orig_update = context.user_data.get("original_update")
        if orig_update:
            await cancel(orig_update, context)
        else:
            await query.edit_message_text("Напоминание отменено.")
            context.job_queue.run_once(
                delete_message_callback,
                when=10,  # 10 секунд, чтобы успеть прочитать
                data={"chat_id": query.message.chat_id, "message_id": query.message.message_id}
            )
        return ConversationHandler.END

    parts = data.split("|")
    step = parts[1]
    year = parts[2]
    month = parts[3]
    day = parts[4]
    hour = parts[5]
    minute = parts[6]

    if step == "year":
        months = [("Январь",1),("Февраль",2),("Март",3),("Апрель",4),("Май",5),("Июнь",6),("Июль",7),("Август",8),("Сентябрь",9),("Октябрь",10),("Ноябрь",11),("Декабрь",12)]
        btn_cancel = InlineKeyboardButton("Отмена", callback_data="remind_cancel")
        btn_row_m = [[],[],[],[btn_cancel]] 

        for m in months:
            num = m[1]
            callback = f"remind_calendar|month|{year}|{num}|None|None|None"
            if m[1] <= 4:
                btn = InlineKeyboardButton(m[0], callback_data=callback)
                btn_row_m[0].append(btn)
            elif m[1] <= 8:
                btn = InlineKeyboardButton(m[0], callback_data=callback)
                btn_row_m[1].append(btn)
            elif m[1] <= 12:
                btn = InlineKeyboardButton(m[0], callback_data=callback)
                btn_row_m[2].append(btn)

        await query.edit_message_text("Выберите месяц:", reply_markup=InlineKeyboardMarkup(btn_row_m))

    elif step == "month":
        year = int(parts[2])
        month = int(parts[3])
        keyboard = build_calendar_keyboard(year, month)
        await query.edit_message_text("Выберите день:", reply_markup=keyboard)
        return None

    elif step == "day":
        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])
        # Сохраняем день в context.user_data, чтобы использовать позже
        context.user_data["remind_day"] = day
        context.user_data["remind_year"] = year
        context.user_data["remind_month"] = month

        # Создаём клавиатуру часов (0-23)
        keyboard = []
        row = []
        for hour in range(24):
            callback = f"remind_calendar|hour|{year}|{month}|{day}|{hour}|None"
            row.append(InlineKeyboardButton(str(hour), callback_data=callback))
            if len(row) == 6:  # по 6 кнопок в ряд
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("Отмена", callback_data="remind_cancel")])
        await query.edit_message_text("Выберите час:", reply_markup=InlineKeyboardMarkup(keyboard))
        return None

    elif step == "hour":
        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])
        hour = int(parts[5])
        context.user_data["remind_hour"] = hour

        # Минуты с шагом 15
        minutes = [0, 15, 30, 45]
        keyboard = []
        for minute in minutes:
            callback = f"remind_calendar|minute|{year}|{month}|{day}|{hour}|{minute}"
            keyboard.append([InlineKeyboardButton(str(minute), callback_data=callback)])
        keyboard.append([InlineKeyboardButton("Отмена", callback_data="remind_cancel")])
        await query.edit_message_text("Выберите минуты:", reply_markup=InlineKeyboardMarkup(keyboard))
        return None

    elif step == "minute":
        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])
        hour = int(parts[5])
        minute = int(parts[6])

        dt = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("Europe/Berlin"))

        if dt <= datetime.now(ZoneInfo("Europe/Berlin")):
            await query.edit_message_text("Это время уже прошло. Напоминание не установлено.")
            context.job_queue.run_once(
                delete_message_callback,
                when=10,
                data={"chat_id": query.message.chat_id, "message_id": query.message.message_id})
            
            context.user_data.clear()
            return ConversationHandler.END

        # Номер задачи из context.user_data
        task_index = context.user_data["remind_index"] + 1
        datetime_str = dt.strftime("%Y-%m-%d %H:%M")
        date_part, time_part = datetime_str.split()  # разделяем на дату и время
        context.args = [str(task_index), date_part, time_part]

        orig_update = context.user_data.get("original_update")
        if orig_update:
            await query.delete_message()
            await remind(orig_update, context)
        else:
            await query.edit_message_text("Ошибка: не удалось восстановить сессию.")
            context.job_queue.run_once(
                delete_message_callback,
                when=10,
                data={"chat_id": query.message.chat_id, "message_id": query.message.message_id}
            )

        # Очищаем временные данные
        context.user_data.clear()
        return ConversationHandler.END
    
    elif step == "nav_month":
        year = int(parts[2])
        month = int(parts[3])
        action = parts[4]  # "prev" или "next"

        if action == "prev":
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        elif action == "next":
            month += 1
            if month == 13:
                month = 1
                year += 1

        # Показать календарь для новых year, month
        keyboard = build_calendar_keyboard(year, month)
        await query.edit_message_text("Выберите день:", reply_markup=keyboard)
        return None    

import calendar

def build_calendar_keyboard(year, month):
    # Получаем первый день недели (0=Пн, 6=Вс) и число дней
    first_weekday, days_in_month = calendar.monthrange(year, month)
    
    keyboard = []
    
    # Заголовки дней недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    header_row = [InlineKeyboardButton(day, callback_data="ignore") for day in week_days]
    keyboard.append(header_row)
    
    # Строка текущей недели
    row = []
    # Пустые кнопки до первого дня
    for _ in range(first_weekday):
        row.append(InlineKeyboardButton(" ", callback_data="ignore"))
    
    # Дни месяца
    for day in range(1, days_in_month + 1):
        callback = f"remind_calendar|day|{year}|{month}|{day}|None|None"
        row.append(InlineKeyboardButton(str(day), callback_data=callback))
        if len(row) == 7:
            keyboard.append(row)
            row = []
    
    # Заполняем оставшиеся ячейки пустыми кнопками
    if row:
        while len(row) < 7:
            row.append(InlineKeyboardButton(" ", callback_data="ignore"))
        keyboard.append(row)
    
    # Строка навигации
    nav_row = [
        InlineKeyboardButton("<", callback_data=f"remind_calendar|nav_month|{year}|{month}|prev"),
        InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="ignore"),
        InlineKeyboardButton(">", callback_data=f"remind_calendar|nav_month|{year}|{month}|next")
    ]
    keyboard.append(nav_row)
    
    # Кнопка "Отмена"
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="remind_cancel")])
    
    return InlineKeyboardMarkup(keyboard)

######################################################################################################################################################

async def send_self_destruct_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, delete_after: int = 600, reply_markup=None):
    sent_message = await update.message.reply_text(text, reply_markup=reply_markup)
    context.job_queue.run_once(
        delete_message_callback,
        when=delete_after,
        data={"chat_id": sent_message.chat_id, "message_id": sent_message.message_id}
    )
    return sent_message 

async def delete_message_callback(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    try:
        await context.bot.delete_message(chat_id=job_data["chat_id"], message_id=job_data["message_id"])
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")

######################################################################################################################################################
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_self_destruct_message(update, context, "отменено.")
    return ConversationHandler.END
