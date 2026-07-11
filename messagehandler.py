from Bot_manager import *
from telegram.ext import Application, CommandHandler, MessageHandler, filters

add_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text(["➕ Добавить"]), add_start),
        CommandHandler("add", add_start)
    ],
    states={
        WAITING_FOR_TASK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_text)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

delete_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text(["🗑 Удалить"]), delete_start),
        CommandHandler("delete", delete)
    ],
    states={
        WAITING_FOR_TASK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_start)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)