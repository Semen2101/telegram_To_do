from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, date
import textwrap
from zoneinfo import ZoneInfo
from json_manager import *
from KeyBoard import *

tasks = None
bot_messages = {}  # {user_id: [message_id, ...]}

def init_tasks():
    global tasks
    raw = load_data()
    tasks = {int(k): v for k, v in raw.items()}
    if tasks is None:
        tasks = {}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

async def send_self_destruct_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    """Отправляет сообщение и запоминает его ID для удаления при следующем вводе пользователя."""
    sent_message = await update.message.reply_text(text, reply_markup=reply_markup)
    user_id = update.message.from_user.id
    if user_id not in bot_messages:
        bot_messages[user_id] = []
    bot_messages[user_id].append(sent_message.message_id)
    return sent_message

async def clear_previous_bot_messages(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет все накопленные ответы бота для указанного пользователя."""
    if user_id in bot_messages:
        for msg_id in bot_messages[user_id]:
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=msg_id)
            except Exception as e:
                print(f"Не удалось удалить сообщение {msg_id}: {e}")
        bot_messages[user_id] = []

async def delete_user_message(update: Update):
    """Удаляет все сообщения пользователя, кроме /start и /p."""
    if update.message and update.message.text:
        if update.message.text.startswith('/start') or update.message.text == '/p':
            return  # не удаляем приветствие и меню
        try:
            await update.message.delete()
        except Exception as e:
            print(f"Не удалось удалить сообщение пользователя: {e}")

# ==================== СТАРТ И КЛАВИАТУРА ====================

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

# ==================== РАБОТА С ЗАДАЧАМИ (СТАРЫЕ ВЕРСИИ УДАЛЕНЫ) ====================

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await clear_previous_bot_messages(user_id, context)
    await delete_user_message(update)

    # Получаем текущую категорию (по умолчанию "📁 Общее")
    category = context.user_data.get("current_category", "📁 Общее")
    # Убеждаемся, что категория существует
    if user_id not in tasks:
        tasks[user_id] = {"categories": {}, "reminders": []}
    if "categories" not in tasks[user_id]:
        tasks[user_id]["categories"] = {}
    if category not in tasks[user_id]["categories"]:
        tasks[user_id]["categories"][category] = []
    
    if not context.args:
        await send_self_destruct_message(update, context, "Введите задачу после команды /add")
    else:
        task_text = " ".join(context.args)
        tasks[user_id]["categories"][category].append(task_text)
        save_data(tasks)
        print(tasks)

async def task_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await clear_previous_bot_messages(user_id, context)
    await delete_user_message(update)

    if tasks is None:
        init_tasks()
    if user_id not in tasks or not tasks[user_id].get("categories"):
        tasks[user_id] = {"categories": {}, "reminders": []}
        await send_self_destruct_message(update, context, "У вас нету задач")
    else:
        categories = tasks[user_id]["categories"]
        lines = []
        for category, tasks_list in categories.items():
            if not tasks_list:
                continue
            lines.append(f"📂 {category}:")
            for i, task in enumerate(tasks_list, start=1):
                lines.append(f"  {i}. {task}")
        if not lines:
            await send_self_destruct_message(update, context, "У вас нету задач")
        else:
            await send_self_destruct_message(update, context, "\n".join(lines))

# async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # Эта функция больше не используется, оставлена для совместимости, но теперь работает с категориями
#     user_id = update.message.from_user.id
#     await clear_previous_bot_messages(user_id, context)
#     await delete_user_message(update)

#     if tasks is None:
#         init_tasks()
#     if user_id not in tasks or not tasks[user_id].get("categories"):
#         tasks[user_id] = {"categories": {}, "reminders": []}
#         await send_self_destruct_message(update, context, "У вас нету задач")
#     else:
#         if not context.args:
#             await send_self_destruct_message(update, context, "введите номер задачи после команды /delete ")
#         else:
#             try:
#                 index = int(context.args[0]) - 1
#                 # Ищем задачу по всем категориям? Нет, для старых вызовов используем категорию по умолчанию
#                 cat_name = "📁 Общее"
#                 if cat_name in tasks[user_id]["categories"] and 0 <= index < len(tasks[user_id]["categories"][cat_name]):
#                     removed_task = tasks[user_id]["categories"][cat_name].pop(index)
#                     save_data(tasks)
#                     await send_self_destruct_message(update, context, f"Задача '{removed_task}' удалена!")
#                 else:
#                     await send_self_destruct_message(update, context, "Задачи с таким номером не существует")
#             except ValueError:
#                 await send_self_destruct_message(update, context, "Номер должен быть числом")

# async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # Эта функция больше не используется, оставлена для совместимости, но теперь работает с категориями
#     user_id = update.message.from_user.id
#     await clear_previous_bot_messages(user_id, context)
#     await delete_user_message(update)

#     if tasks is None:
#         init_tasks()
#     if user_id not in tasks or not tasks[user_id].get("categories"):
#         tasks[user_id] = {"categories": {}, "reminders": []}
#         await send_self_destruct_message(update, context, "У вас нету задач")
#     else:
#         if not context.args:
#             await send_self_destruct_message(update, context, "Укажите номер задачи и новый текст после команды /edit ")
#         else:
#             try:
#                 index = int(context.args[0]) - 1
#                 cat_name = "📁 Общее"
#                 if cat_name in tasks[user_id]["categories"] and 0 <= index < len(tasks[user_id]["categories"][cat_name]) and len(context.args) >= 2:
#                     old = tasks[user_id]["categories"][cat_name][index]
#                     new_text = " ".join(context.args[1:])
#                     tasks[user_id]["categories"][cat_name][index] = new_text
#                     save_data(tasks)
#                     await send_self_destruct_message(update, context, f"Задача '{old}' изменена на '{new_text}'.")
#                 else:
#                     await send_self_destruct_message(update, context, "Введите новый текст задачи после команды /edit")    
#             except ValueError:
#                 await send_self_destruct_message(update, context, "Номер должен быть числом")

# ==================== НАПОМИНАНИЯ ====================

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if tasks is None:
        init_tasks()
    user_id = update.message.from_user.id
    cat_name = context.user_data.get("remind_category", "📁 Общее")
    if user_id not in tasks or not tasks[user_id].get("categories", {}).get(cat_name):
        await send_self_destruct_message(update, context, "У вас нет задач в этой категории.")
        return
    if not context.args or len(context.args) != 3:
        await send_self_destruct_message(update, context, "/remind НОМЕР ГГГГ-ММ-ДД ЧЧ:ММ")
        return
    try:
        index = int(context.args[0]) - 1
        if 0 <= index < len(tasks[user_id]["categories"][cat_name]):
            data = context.args[1] + " " + context.args[2]
            naive_dt = datetime.strptime(data, "%Y-%m-%d %H:%M")
            data_time = naive_dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))
            task_text = tasks[user_id]["categories"][cat_name][index]
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
                    "category": cat_name,
                    "datetime_str": data_time.isoformat()
                }
            )
            reminder_data = {
                "task_index": index,
                "category": cat_name,
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
        await send_self_destruct_message(update, context, "Неверный формат даты/времени.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        await send_self_destruct_message(update, context, f"Ошибка: {e}")

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    if tasks is None:
        init_tasks()
    print("=== CALLBACK CALLED ===")
    try:
        job_data = context.job.data
        chat_id = job_data['chat_id']
        task_text = job_data['task_text']
        await context.bot.send_message(chat_id=chat_id, text=f"Напоминание: {task_text}")
        # Помечаем выполненным, учитывая категорию
        reminders = tasks[chat_id]["reminders"]
        for rem in reminders:
            if (rem["task_index"] == job_data["task_index"] and
                rem["datetime_str"] == job_data["datetime_str"] and
                rem.get("category", "📁 Общее") == job_data.get("category", "📁 Общее")):
                rem["completed"] = True
                break
        save_data(tasks)
    except Exception as e:
        print(f"ОШИБКА в send_reminder: {e}")

async def show_remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await clear_previous_bot_messages(user_id, context)
    await delete_user_message(update)

    if tasks is None:
        init_tasks()
    if user_id not in tasks:
        tasks[user_id] = {"categories": {}, "reminders": []}
        await send_self_destruct_message(update, context, "У вас нет активных напоминаний.")
        return

    reminders = tasks[user_id].get("reminders", [])
    if not reminders:
        await send_self_destruct_message(update, context, "У вас нет активных напоминаний.")
        return

    lines = ["📋 Ваши напоминания:"]
    for i, rem in enumerate(reminders, start=1):
        cat_name = rem.get("category", "📁 Общее")
        task_index = rem.get("task_index")
        task_text = "❓"
        if cat_name in tasks[user_id].get("categories", {}):
            cat_tasks = tasks[user_id]["categories"][cat_name]
            if 0 <= task_index < len(cat_tasks):
                task_text = cat_tasks[task_index]

        dt_str = rem.get("datetime_str", "")
        try:
            dt = datetime.fromisoformat(dt_str)
            formatted = dt.strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError):
            formatted = dt_str

        status = "✅" if rem.get("completed", False) else "❌"
        lines.append(f'{i}. [{cat_name}] "{task_text}" — {formatted} {status}')
    await send_self_destruct_message(update, context, "\n".join(lines))

async def delete_complete_remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await clear_previous_bot_messages(user_id, context)
    await delete_user_message(update)

    if tasks is None:
        init_tasks()
    if user_id not in tasks:
        tasks[user_id] = {"categories": {}, "reminders": []}
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

# ==================== ДИАЛОГИ ====================

WAITING_FOR_TASK_TEXT = 1
WAITING_FOR_CATEGORY_SELECT = 8

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cats = tasks[user_id].get("categories", {})
    if not cats:
        await send_self_destruct_message(update, context, "У вас пока нет категорий. Создайте новую кнопкой 📁 Новая категория.")
        return ConversationHandler.END
    keyboard = []
    for cat_name in cats.keys():
        keyboard.append([InlineKeyboardButton(cat_name, callback_data=f"select_cat|{cat_name}")])
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
    await update.message.reply_text("Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_FOR_CATEGORY_SELECT

# async def add_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()
#     data = query.data
#     if data == "cancel":
#         await query.edit_message_text("Добавление отменено.")
#         return ConversationHandler.END
#     # Извлекаем название категории
#     cat_name = data.split("|")[1]
#     # Сохраняем выбранную категорию
#     context.user_data["current_category"] = cat_name
#     await query.edit_message_text("Введите текст задачи (или /cancel для отмены):")
#     return WAITING_FOR_TASK_TEXT

async def add_task_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_text = update.message.text
    context.args = update.message.text.split()
    await add_task(update, context)
    await send_self_destruct_message(update, context, f"Задача '{task_text}' добавлена!")
    return ConversationHandler.END

# -------------------- УДАЛЕНИЕ --------------------

WAITING_FOR_TASK_NUM = 2
WAITING_FOR_DELETE_CATEGORY = 9

async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cats = tasks[user_id].get("categories", {})
    if not cats:
        await send_self_destruct_message(update, context, "У вас пока нет категорий.")
        return ConversationHandler.END
    keyboard = []
    for cat_name in cats.keys():
        keyboard.append([InlineKeyboardButton(cat_name, callback_data=f"del_cat|{cat_name}")])
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
    await update.message.reply_text("Выберите категорию для удаления задачи:", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_FOR_DELETE_CATEGORY

async def delete_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel":
        await query.edit_message_text("Удаление отменено.")
        return ConversationHandler.END
    cat_name = data.split("|")[1]
    context.user_data["delete_category"] = cat_name
    user_id = query.message.chat.id
    tasks_list = tasks[user_id]["categories"].get(cat_name, [])
    if not tasks_list:
        await query.edit_message_text(f"В категории '{cat_name}' нет задач.")
        return ConversationHandler.END
    lines = "\n".join(f"{i}. {task}" for i, task in enumerate(tasks_list, start=1))
    await query.edit_message_text(f"Задачи в '{cat_name}':\n{lines}\n\nВведите номер задачи для удаления (или /cancel):")
    return WAITING_FOR_TASK_NUM

async def delete_task_by_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await clear_previous_bot_messages(user_id, context)
    await delete_user_message(update)

    cat_name = context.user_data.get("delete_category")
    if not cat_name:
        await send_self_destruct_message(update, context, "Ошибка: не выбрана категория.")
        return ConversationHandler.END
    try:
        index = int(update.message.text) - 1
        if 0 <= index < len(tasks[user_id]["categories"][cat_name]):
            removed_task = tasks[user_id]["categories"][cat_name].pop(index)
            save_data(tasks)
            await send_self_destruct_message(update, context, f"Задача '{removed_task}' удалена!")
        else:
            await send_self_destruct_message(update, context, "Задачи с таким номером не существует.")
    except ValueError:
        await send_self_destruct_message(update, context, "Номер должен быть числом.")
    return ConversationHandler.END

# -------------------- РЕДАКТИРОВАНИЕ --------------------

WAITING_FOR_EDIT_CATEGORY = 11
WAITING_FOR_EDIT_TASK_NUM = 12
WAITING_FOR_EDIT_TEXT1 = 4

async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cats = tasks[user_id].get("categories", {})
    if not cats:
        await send_self_destruct_message(update, context, "У вас пока нет категорий.")
        return ConversationHandler.END
    keyboard = []
    for cat_name in cats.keys():
        keyboard.append([InlineKeyboardButton(cat_name, callback_data=f"edit_cat|{cat_name}")])
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
    await update.message.reply_text("Выберите категорию для редактирования задачи:", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_FOR_EDIT_CATEGORY

async def edit_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel":
        await query.edit_message_text("Редактирование отменено.")
        return ConversationHandler.END
    cat_name = data.split("|")[1]
    context.user_data["edit_category"] = cat_name
    user_id = query.message.chat.id
    tasks_list = tasks[user_id]["categories"].get(cat_name, [])
    if not tasks_list:
        await query.edit_message_text(f"В категории '{cat_name}' нет задач.")
        return ConversationHandler.END
    lines = "\n".join(f"{i}. {task}" for i, task in enumerate(tasks_list, start=1))
    await query.edit_message_text(f"Задачи в '{cat_name}':\n{lines}\n\nВведите номер задачи для редактирования (или /cancel):")
    return WAITING_FOR_EDIT_TASK_NUM

async def edit_task_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await clear_previous_bot_messages(user_id, context)
    await delete_user_message(update)

    cat_name = context.user_data.get("edit_category")
    if not cat_name:
        await send_self_destruct_message(update, context, "Ошибка: не выбрана категория.")
        return ConversationHandler.END
    try:
        index = int(update.message.text) - 1
        if 0 <= index < len(tasks[user_id]["categories"][cat_name]):
            context.user_data["edit_index"] = index
            await send_self_destruct_message(update, context, "Введите новый текст задачи:")
            return WAITING_FOR_EDIT_TEXT1
        else:
            await send_self_destruct_message(update, context, "Задачи с таким номером не существует.")
            return None
    except ValueError:
        await send_self_destruct_message(update, context, "Номер должен быть числом.")
        return None

async def edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cat_name = context.user_data.get("edit_category")
    index = context.user_data.get("edit_index")
    if not cat_name or index is None:
        await send_self_destruct_message(update, context, "Ошибка: потеряны данные редактирования.")
        return ConversationHandler.END
    new_text = update.message.text
    old_text = tasks[user_id]["categories"][cat_name][index]
    tasks[user_id]["categories"][cat_name][index] = new_text
    save_data(tasks)
    await send_self_destruct_message(update, context, f"Задача '{old_text}' изменена на '{new_text}'.")
    context.user_data.clear()
    return ConversationHandler.END

# -------------------- НАПОМИНАНИЕ --------------------

WAITING_FOR_REMIND_CATEGORY = 13
WAITING_FOR_REMIND_TASK_NUM = 14
WAITING_FOR_REMIND_CALENDAR = 7

async def remind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cats = tasks[user_id].get("categories", {})
    if not cats:
        await send_self_destruct_message(update, context, "У вас пока нет категорий.")
        return ConversationHandler.END
    keyboard = []
    for cat_name in cats.keys():
        keyboard.append([InlineKeyboardButton(cat_name, callback_data=f"rem_cat|{cat_name}")])
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
    await update.message.reply_text("Выберите категорию для напоминания:", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_FOR_REMIND_CATEGORY

async def remind_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel":
        await query.edit_message_text("Напоминание отменено.")
        return ConversationHandler.END
    cat_name = data.split("|")[1]
    context.user_data["remind_category"] = cat_name
    user_id = query.message.chat.id
    tasks_list = tasks[user_id]["categories"].get(cat_name, [])
    if not tasks_list:
        await query.edit_message_text(f"В категории '{cat_name}' нет задач.")
        return ConversationHandler.END
    lines = "\n".join(f"{i}. {task}" for i, task in enumerate(tasks_list, start=1))
    await query.edit_message_text(f"Задачи в '{cat_name}':\n{lines}\n\nВведите номер задачи (или /cancel):")
    return WAITING_FOR_REMIND_TASK_NUM

async def remind_task_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await clear_previous_bot_messages(user_id, context)
    await delete_user_message(update)

    cat_name = context.user_data.get("remind_category")
    if not cat_name:
        await send_self_destruct_message(update, context, "Ошибка: не выбрана категория.")
        return ConversationHandler.END
    try:
        index = int(update.message.text) - 1
        if 0 <= index < len(tasks[user_id]["categories"][cat_name]):
            context.user_data["remind_index"] = index
            context.user_data["original_update"] = update
            year = datetime.now().year
            btn = InlineKeyboardButton(str(year), callback_data=f"remind_calendar|year|{year}|None|None|None|None")
            btn1 = InlineKeyboardButton(str(year+1), callback_data=f"remind_calendar|year|{year+1}|None|None|None|None")
            btn2 = InlineKeyboardButton(str(year+2), callback_data=f"remind_calendar|year|{year+2}|None|None|None|None")
            btn_cancel = InlineKeyboardButton("Отмена", callback_data="remind_cancel")
            buttons_rows = [[btn, btn1, btn2], [btn_cancel]]
            await update.message.reply_text("Выберите год:", reply_markup=InlineKeyboardMarkup(buttons_rows))
            return WAITING_FOR_REMIND_CALENDAR
        else:
            await send_self_destruct_message(update, context, "Такой задачи не существует. Попробуйте снова (или /cancel).")
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
        context.user_data["remind_day"] = day
        context.user_data["remind_year"] = year
        context.user_data["remind_month"] = month

        keyboard = []
        row = []
        for hour in range(24):
            callback = f"remind_calendar|hour|{year}|{month}|{day}|{hour}|None"
            row.append(InlineKeyboardButton(str(hour), callback_data=callback))
            if len(row) == 6:
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
            context.user_data.clear()
            return ConversationHandler.END

        task_index = context.user_data["remind_index"] + 1
        datetime_str = dt.strftime("%Y-%m-%d %H:%M")
        date_part, time_part = datetime_str.split()
        context.args = [str(task_index), date_part, time_part]

        orig_update = context.user_data.get("original_update")
        if orig_update:
            await query.delete_message()
            await remind(orig_update, context)
        else:
            await query.edit_message_text("Ошибка: не удалось восстановить сессию.")
            context.user_data.clear()
            return ConversationHandler.END    

        context.user_data.clear()
        return ConversationHandler.END

    elif step == "nav_month":
        year = int(parts[2])
        month = int(parts[3])
        action = parts[4]

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

        keyboard = build_calendar_keyboard(year, month)
        await query.edit_message_text("Выберите день:", reply_markup=keyboard)
        return None

import calendar

def build_calendar_keyboard(year, month):
    first_weekday, days_in_month = calendar.monthrange(year, month)
    keyboard = []
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    header_row = [InlineKeyboardButton(day, callback_data="ignore") for day in week_days]
    keyboard.append(header_row)
    
    row = []
    for _ in range(first_weekday):
        row.append(InlineKeyboardButton(" ", callback_data="ignore"))
    
    for day in range(1, days_in_month + 1):
        callback = f"remind_calendar|day|{year}|{month}|{day}|None|None"
        row.append(InlineKeyboardButton(str(day), callback_data=callback))
        if len(row) == 7:
            keyboard.append(row)
            row = []
    if row:
        while len(row) < 7:
            row.append(InlineKeyboardButton(" ", callback_data="ignore"))
        keyboard.append(row)
    
    nav_row = [
        InlineKeyboardButton("<", callback_data=f"remind_calendar|nav_month|{year}|{month}|prev"),
        InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="ignore"),
        InlineKeyboardButton(">", callback_data=f"remind_calendar|nav_month|{year}|{month}|next")
    ]
    keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="remind_cancel")])
    return InlineKeyboardMarkup(keyboard)

# -------------------- УПРАВЛЕНИЕ КАТЕГОРИЯМИ --------------------

WAITING_FOR_CATEGORY_NAME = 15
WAITING_FOR_RENAME_CATEGORY = 16
WAITING_FOR_DELETE_CATEGORY_CONFIRM = 17

async def create_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_self_destruct_message(update, context, "Введите название новой категории (или /cancel для отмены):")
    return WAITING_FOR_CATEGORY_NAME

async def create_category_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await clear_previous_bot_messages(user_id, context)
    await delete_user_message(update)

    cat_name = update.message.text.strip()
    if not cat_name:
        await send_self_destruct_message(update, context, "Название не может быть пустым. Попробуйте снова:")
        return None
    if user_id not in tasks:
        tasks[user_id] = {"categories": {}, "reminders": []}
    if "categories" not in tasks[user_id]:
        tasks[user_id]["categories"] = {}
    if cat_name in tasks[user_id]["categories"]:
        await send_self_destruct_message(update, context, f"Категория '{cat_name}' уже существует. Попробуйте другое название:")
        return None
    tasks[user_id]["categories"][cat_name] = []
    save_data(tasks)
    context.user_data["current_category"] = cat_name
    await send_self_destruct_message(update, context, f"Категория '{cat_name}' создана и выбрана.")
    return ConversationHandler.END

async def rename_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cats = tasks[user_id].get("categories", {})
    if not cats:
        await send_self_destruct_message(update, context, "У вас пока нет категорий.")
        return ConversationHandler.END
    keyboard = []
    for cat_name in cats.keys():
        keyboard.append([InlineKeyboardButton(cat_name, callback_data=f"rename_cat|{cat_name}")])
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
    await update.message.reply_text("Выберите категорию для переименования:", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_FOR_RENAME_CATEGORY

async def rename_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel":
        await query.edit_message_text("Переименование отменено.")
        return ConversationHandler.END
    old_name = data.split("|")[1]
    context.user_data["rename_old_name"] = old_name
    await query.edit_message_text(f"Введите новое название для категории '{old_name}' (или /cancel):")
    return WAITING_FOR_CATEGORY_NAME

async def rename_category_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await clear_previous_bot_messages(user_id, context)
    await delete_user_message(update)

    old_name = context.user_data.get("rename_old_name")
    if not old_name:
        await send_self_destruct_message(update, context, "Ошибка: не выбрана категория.")
        return ConversationHandler.END
    new_name = update.message.text.strip()
    if not new_name:
        await send_self_destruct_message(update, context, "Название не может быть пустым.")
        return None
    if new_name in tasks[user_id]["categories"]:
        await send_self_destruct_message(update, context, f"Категория '{new_name}' уже существует.")
        return None
    tasks[user_id]["categories"][new_name] = tasks[user_id]["categories"].pop(old_name)
    if "reminders" in tasks[user_id]:
        for rem in tasks[user_id]["reminders"]:
            if rem.get("category") == old_name:
                rem["category"] = new_name
    save_data(tasks)
    await send_self_destruct_message(update, context, f"Категория '{old_name}' переименована в '{new_name}'.")
    context.user_data.clear()
    return ConversationHandler.END

async def delete_category_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cats = tasks[user_id].get("categories", {})
    if not cats:
        await send_self_destruct_message(update, context, "У вас пока нет категорий.")
        return ConversationHandler.END
    keyboard = []
    for cat_name in cats.keys():
        keyboard.append([InlineKeyboardButton(cat_name, callback_data=f"delcat|{cat_name}")])
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
    await update.message.reply_text("Выберите категорию для удаления (задачи будут потеряны!):", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_FOR_DELETE_CATEGORY_CONFIRM

async def delete_category_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel":
        await query.edit_message_text("Удаление отменено.")
        return ConversationHandler.END
    cat_name = data.split("|")[1]
    user_id = query.message.chat.id
    if cat_name not in tasks[user_id].get("categories", {}):
        await query.edit_message_text("Категория не найдена.")
        return ConversationHandler.END
    del tasks[user_id]["categories"][cat_name]
    if "reminders" in tasks[user_id]:
        tasks[user_id]["reminders"] = [r for r in tasks[user_id]["reminders"] if r.get("category") != cat_name]
    save_data(tasks)
    await query.edit_message_text(f"Категория '{cat_name}' удалена.")
    return ConversationHandler.END

# -------------------- УДАЛЕНИЕ ОДНОГО НАПОМИНАНИЯ --------------------

async def delete_remind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список напоминаний с кнопками для удаления."""
    if tasks is None:
        init_tasks()
    user_id = update.message.from_user.id
    await clear_previous_bot_messages(user_id, context)
    await delete_user_message(update)

    reminders = tasks[user_id].get("reminders", [])
    if not reminders:
        await send_self_destruct_message(update, context, "У вас нет напоминаний.")
        return

    keyboard = []
    for i, rem in enumerate(reminders):
        cat = rem.get("category", "📁 Общее")
        task_text = "❓"
        if cat in tasks[user_id].get("categories", {}):
            cat_tasks = tasks[user_id]["categories"][cat]
            idx = rem.get("task_index", 0)
            if 0 <= idx < len(cat_tasks):
                task_text = cat_tasks[idx]
        btn_text = f"{i+1}. {task_text}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"delrem|{i}")])
    keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
    await update.message.reply_text("Выберите напоминание для удаления:", reply_markup=InlineKeyboardMarkup(keyboard))

async def delete_remind_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "cancel":
        await query.edit_message_text("Отменено.")
        return ConversationHandler.END
    index = int(data.split("|")[1])
    user_id = query.message.chat.id
    reminders = tasks[user_id].get("reminders", [])
    if 0 <= index < len(reminders):
        removed = reminders.pop(index)
        save_data(tasks)
        await query.edit_message_text(f"Напоминание удалено.")
    else:
        await query.edit_message_text("Неверный номер.")

# -------------------- ОТМЕНА --------------------

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_self_destruct_message(update, context, "отменено.")
    return ConversationHandler.END

async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Отменено.")
    return ConversationHandler.END