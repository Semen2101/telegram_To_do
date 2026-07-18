from Bot_manager import *
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

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
        WAITING_FOR_TASK_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_text)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

edit_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text(["✏️ Изменить"]), edit_start),
        CommandHandler("edit", edit_start)  # если хочешь, чтобы /edit тоже запускал диалог
    ],
    states={
        WAITING_FOR_EDIT_NUM1: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_num)],
        WAITING_FOR_EDIT_TEXT1: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_text)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

remind_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text(["⏰ Напомнить"]), remind_start),
        CommandHandler("remind", remind_start)
    ],
    states={
        WAITING_FOR_REMIND_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_num)],
        WAITING_FOR_REMIND_CALENDAR: [CallbackQueryHandler(remind_calendar_handler, pattern="^remind_calendar\\|")]
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(cancel, pattern="^remind_cancel$")
    ]
)