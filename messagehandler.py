from Bot_manager import *
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

add_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text(["➕ Добавить"]), add_start),
        CommandHandler("add", add_start)
    ],
    states={
        WAITING_FOR_CATEGORY_SELECT: [CallbackQueryHandler(add_category_selection, pattern="^select_cat\\|")],
        WAITING_FOR_TASK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_text)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

delete_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text(["🗑 Удалить"]), delete_start),
        CommandHandler("delete", delete_start)  # по команде тоже запускаем новый диалог
    ],
    states={
        WAITING_FOR_DELETE_CATEGORY: [CallbackQueryHandler(delete_category_selection, pattern="^del_cat\\|")],
        WAITING_FOR_TASK_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_task_by_number)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

edit_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Text(["✏️ Изменить"]), edit_start),
        CommandHandler("edit", edit_start)
    ],
    states={
        WAITING_FOR_EDIT_CATEGORY: [CallbackQueryHandler(edit_category_selection, pattern="^edit_cat\\|")],
        WAITING_FOR_EDIT_TASK_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_task_num)],
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
        WAITING_FOR_REMIND_CATEGORY: [CallbackQueryHandler(remind_category_selection, pattern="^rem_cat\\|")],
        WAITING_FOR_REMIND_TASK_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_task_num)],
        WAITING_FOR_REMIND_CALENDAR: [CallbackQueryHandler(remind_calendar_handler, pattern="^remind_calendar\\|")]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

# Создание категории
create_category_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(["📁 Новая категория"]), create_category_start)],
    states={
        WAITING_FOR_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_category_finish)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

# Переименование категории
rename_category_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(["✏️ Переименовать категорию"]), rename_category_start)],
    states={
        WAITING_FOR_RENAME_CATEGORY: [CallbackQueryHandler(rename_category_selection, pattern="^rename_cat\\|")],
        WAITING_FOR_CATEGORY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, rename_category_finish)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

# Удаление категории
delete_category_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Text(["🗑 Удалить категорию"]), delete_category_start)],
    states={
        WAITING_FOR_DELETE_CATEGORY_CONFIRM: [CallbackQueryHandler(delete_category_selection, pattern="^delcat\\|")]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)