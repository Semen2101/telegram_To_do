from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime

async def keyBoard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button_layout = [
    [KeyboardButton("➕ Добавить"), KeyboardButton("📋 Список"), KeyboardButton("🗑 Удалить"), KeyboardButton("✏️ Изменить")],
    [KeyboardButton("⏰ Напомнить"), KeyboardButton("📌 Список напоминаний"), KeyboardButton("🧹 Очистить выполненные"), KeyboardButton("Скрыть меню")]]
    
    key_board = ReplyKeyboardMarkup(
        keyboard=button_layout,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await update.message.reply_text("Меню:", reply_markup=key_board)

async def hide_keyBoard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Меню скрыто. Вернуть: /p", reply_markup=ReplyKeyboardRemove())

