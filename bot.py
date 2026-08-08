"""
Main Application Entrypoint.
Initializes python-telegram-bot Application, registers handlers, persistent keyboards, DB and Scheduler.
"""

import logging
import sys
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from config import BOT_TOKEN
import database as db
import scheduler
from handlers.common import (
    start_command,
    help_command,
    language_command,
    language_button_callback,
    role_command,
    role_button_callback,
    navigation_callback_handler,
    register_bot_commands,
    global_error_handler,
    cancel_wizard_callback
)
from handlers.private import (
    todo_command,
    todos_command,
    mytasks_command,
    membertasks_command,
    private_done_button_callback,
    prompt_add_task_options,
    prompt_complete_assigned_task,
    add_task_type_callback,
    deadline_preset_callback,
    calendar_callback_handler,
    handle_task_creation_text_input
)
from handlers.group import (
    assign_command,
    grouptasks_command,
    complete_command
)
from handlers.report import (
    report_command,
    report_type_callback,
    report_generate_callback
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def post_init_setup(application) -> None:
    """Run post-initialization tasks such as setting bot command menus."""
    await register_bot_commands(application)


async def wizard_text_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Pass text messages to interactive task creation wizard if active."""
    await handle_task_creation_text_input(update, context)


def main() -> None:
    """Initialize and run the Telegram Bot."""
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN environment variable missing. Exiting.")
        sys.exit(1)

    logger.info("Initializing Firebase Firestore connection...")
    db.init_db()

    logger.info("Building Telegram Application...")
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init_setup)
        .build()
    )

    # Register Command Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("language", language_command))
    application.add_handler(CommandHandler("role", role_command))
    application.add_handler(CommandHandler("report", report_command))

    # Private Scope Handlers
    application.add_handler(CommandHandler("todo", todo_command))
    application.add_handler(CommandHandler("todos", todos_command))
    application.add_handler(CommandHandler("mytasks", mytasks_command))
    application.add_handler(CommandHandler("membertasks", membertasks_command))

    # Group Scope Handlers
    application.add_handler(CommandHandler("assign", assign_command))
    application.add_handler(CommandHandler("grouptasks", grouptasks_command))
    application.add_handler(CommandHandler("complete", complete_command))

    # Persistent Reply Keyboard Text Handlers (Khmer & English) - TOP ROW BUTTONS FIRST
    application.add_handler(MessageHandler(filters.Regex(r"^(➕ បន្ថែមភារកិច្ច \(ខ្លួនឯង / មន្ត្រី\)|➕ Add To-Do \(Self / Staff\)|➕ បន្ថែមភារកិច្ចផ្ទាល់ខ្លួន|➕ Add Personal To-Do|➕ ប្រគល់ភារកិច្ចជូនមន្ត្រី|➕ Assign Task to Staff)$"), prompt_add_task_options))
    application.add_handler(MessageHandler(filters.Regex(r"^(✓ បញ្ចប់ភារកិច្ចដែលបានប្រគល់|✓ Complete Assigned Task|✓ បញ្ចប់ភារកិច្ចក្រុម|✓ Complete Group Task)$"), prompt_complete_assigned_task))
    
    application.add_handler(MessageHandler(filters.Regex(r"^(📋 បញ្ជីភារកិច្ចផ្ទាល់ខ្លួន|📋 Personal To-Dos)$"), todos_command))
    application.add_handler(MessageHandler(filters.Regex(r"^(📌 ភារកិច្ចដែលបានប្រគល់ជូនខ្ញុំ|📌 Tasks Assigned to Me)$"), mytasks_command))
    application.add_handler(MessageHandler(filters.Regex(r"^(📋 ភារកិច្ចក្រុមដែលកំពុងរង់ចាំ|📋 Active Group Tasks)$"), grouptasks_command))
    application.add_handler(MessageHandler(filters.Regex(r"^(👥 ពិនិត្យភារកិច្ចមន្ត្រី \(ប្រធាន\)|👥 Check Staff Tasks \(Boss\)|👥 ពិនិត្យភារកិច្ចសមាជិក|👥 Check Member Assignments)$"), membertasks_command))
    application.add_handler(MessageHandler(filters.Regex(r"^(📊 របាយការណ៍ \(ប្រធាន\)|📊 Task Report \(Boss\)|📊 របាយការណ៍ \(មន្ត្រី\)|📊 Task Report \(Staff\))$"), report_command))

    application.add_handler(CallbackQueryHandler(cancel_wizard_callback, pattern="^cancel_wizard$"))
    application.add_handler(CallbackQueryHandler(calendar_callback_handler, pattern="^cal_"))
    application.add_handler(CallbackQueryHandler(report_type_callback, pattern="^rpt_type_"))
    application.add_handler(CallbackQueryHandler(report_generate_callback, pattern="^rpt_fmt_"))
    application.add_handler(CallbackQueryHandler(add_task_type_callback, pattern="^add_type_"))
    application.add_handler(CallbackQueryHandler(deadline_preset_callback, pattern="^dl_preset_"))
    application.add_handler(CallbackQueryHandler(role_button_callback, pattern="^set_role_"))
    application.add_handler(CallbackQueryHandler(navigation_callback_handler, pattern="^cb_nav_"))
    application.add_handler(CallbackQueryHandler(language_button_callback, pattern="^set_lang_"))
    application.add_handler(CallbackQueryHandler(private_done_button_callback, pattern="^done_"))

    # Generic Text Handler for Interactive Wizard
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wizard_text_input_handler))

    # Global Error Handler
    application.add_error_handler(global_error_handler)

    # Initialize Scheduler Jobs
    scheduler.setup_scheduler(application)

    logger.info("Bot successfully initialized. Starting long polling listener...")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
