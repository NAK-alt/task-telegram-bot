"""
Common Handlers: /start, /help, /language, /role, Keyboards (Inline & Reply), and Global Error Handler.
"""

import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats
)
from telegram.ext import ContextTypes
from telegram.error import TelegramError, Forbidden

import database as db
from i18n import t

logger = logging.getLogger(__name__)


def get_main_keyboard(lang: str = "km", is_private: bool = True, role: str = "staff") -> ReplyKeyboardMarkup:
    """
    Construct persistent reply keyboard pinned at bottom of chat input box.
    Consolidates personal to-dos and assigned tasks into '📋 បញ្ជីភារកិច្ចផ្ទាល់ខ្លួន'.
    Includes Report button for both Boss and Staff personas.
    """
    if is_private:
        if role == "boss":
            keyboard = [
                [
                    KeyboardButton(t("btn_menu_add_task_boss", lang)),
                    KeyboardButton(t("btn_menu_complete_task", lang)),
                ],
                [
                    KeyboardButton(t("btn_menu_todos", lang)),
                    KeyboardButton(t("btn_menu_member_tasks", lang)),
                ],
                [
                    KeyboardButton(t("btn_menu_report", lang)),
                ]
            ]
        else:
            keyboard = [
                [
                    KeyboardButton(t("btn_menu_add_task_staff", lang)),
                    KeyboardButton(t("btn_menu_complete_task", lang)),
                ],
                [
                    KeyboardButton(t("btn_menu_todos", lang)),
                    KeyboardButton(t("btn_menu_report_staff", lang)),
                ]
            ]
    else:
        if role == "boss":
            keyboard = [
                [
                    KeyboardButton(t("btn_menu_assign_coworker", lang)),
                    KeyboardButton(t("btn_menu_complete_group", lang)),
                ],
                [
                    KeyboardButton(t("btn_menu_grouptasks", lang)),
                    KeyboardButton(t("btn_menu_member_tasks", lang)),
                ],
                [
                    KeyboardButton(t("btn_menu_report", lang)),
                ]
            ]
        else:
            keyboard = [
                [
                    KeyboardButton(t("btn_menu_complete_group", lang)),
                ],
                [
                    KeyboardButton(t("btn_menu_grouptasks", lang)),
                    KeyboardButton(t("btn_menu_report_staff", lang)),
                ]
            ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


def get_inline_dashboard(lang: str = "km", is_private: bool = True, role: str = "staff") -> InlineKeyboardMarkup:
    """
    Construct rich inline action buttons attached directly to message bubbles.
    """
    if is_private:
        if role == "boss":
            keyboard = [
                [
                    InlineKeyboardButton(t("btn_menu_add_task_boss", lang), callback_data="cb_nav_add_task"),
                    InlineKeyboardButton(t("btn_menu_complete_task", lang), callback_data="cb_nav_complete_task"),
                ],
                [
                    InlineKeyboardButton(t("btn_menu_todos", lang), callback_data="cb_nav_todos"),
                    InlineKeyboardButton(t("btn_menu_member_tasks", lang), callback_data="cb_nav_member_tasks"),
                ],
                [
                    InlineKeyboardButton(t("btn_menu_report", lang), callback_data="cb_nav_report"),
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton(t("btn_menu_add_task_staff", lang), callback_data="cb_nav_add_task"),
                    InlineKeyboardButton(t("btn_menu_complete_task", lang), callback_data="cb_nav_complete_task"),
                ],
                [
                    InlineKeyboardButton(t("btn_menu_todos", lang), callback_data="cb_nav_todos"),
                    InlineKeyboardButton(t("btn_menu_report_staff", lang), callback_data="cb_nav_report"),
                ]
            ]
    else:
        if role == "boss":
            keyboard = [
                [
                    InlineKeyboardButton(t("btn_menu_assign_coworker", lang), callback_data="cb_nav_assign_coworker"),
                    InlineKeyboardButton(t("btn_menu_complete_group", lang), callback_data="cb_nav_complete_group"),
                ],
                [
                    InlineKeyboardButton(t("btn_menu_grouptasks", lang), callback_data="cb_nav_grouptasks"),
                    InlineKeyboardButton(t("btn_menu_member_tasks", lang), callback_data="cb_nav_member_tasks"),
                ],
                [
                    InlineKeyboardButton(t("btn_menu_report", lang), callback_data="cb_nav_report"),
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton(t("btn_menu_complete_group", lang), callback_data="cb_nav_complete_group"),
                ],
                [
                    InlineKeyboardButton(t("btn_menu_grouptasks", lang), callback_data="cb_nav_grouptasks"),
                    InlineKeyboardButton(t("btn_menu_report_staff", lang), callback_data="cb_nav_report"),
                ]
            ]

    return InlineKeyboardMarkup(keyboard)


async def register_bot_commands(application) -> None:
    """Set native Telegram bot command menu for private and group scopes."""
    try:
        private_commands = [
            BotCommand("todos", "View all pending personal & assigned tasks"),
            BotCommand("report", "Generate and download task report"),
            BotCommand("membertasks", "Inspect staff tasks (Boss only)"),
            BotCommand("todo", "Manage personal to-dos"),
            BotCommand("role", "Select role (ប្រធានការិយាល័យ / មន្ត្រី)"),
            BotCommand("language", "Switch language / ផ្លាស់ប្តូរភាសា"),
            BotCommand("help", "View guide and documentation"),
        ]
        group_commands = [
            BotCommand("grouptasks", "View pending group tasks"),
            BotCommand("report", "Generate and download task report"),
            BotCommand("assign", "Delegate task to staff (Boss only)"),
            BotCommand("complete", "Mark task as completed"),
            BotCommand("membertasks", "Inspect staff tasks (Boss only)"),
            BotCommand("role", "Select role (ប្រធាន / មន្ត្រី)"),
            BotCommand("help", "View guide and documentation"),
        ]

        await application.bot.set_my_commands(
            private_commands,
            scope=BotCommandScopeAllPrivateChats()
        )
        await application.bot.set_my_commands(
            group_commands,
            scope=BotCommandScopeAllGroupChats()
        )
        logger.info("Native Bot Commands successfully registered.")
    except Exception as e:
        logger.error(f"Failed to register native bot commands: {e}")


ADMIN_USER_ID = 1079885088


async def prompt_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send Inline Keyboard asking user to select role: ប្រធានការិយាល័យ or មន្ត្រី."""
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return
    lang = db.get_chat_language(chat.id)

    if user.id != ADMIN_USER_ID:
        if update.effective_message:
            await update.effective_message.reply_text(t("unauthorized_admin", lang))
        return

    keyboard = [
        [
            InlineKeyboardButton(t("btn_role_boss", lang), callback_data="set_role_boss"),
            InlineKeyboardButton(t("btn_role_staff", lang), callback_data="set_role_staff"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(t("select_role", lang), reply_markup=reply_markup)


async def role_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /role command to switch user role (Restricted strictly to Telegram ID 1079885088)."""
    await prompt_role_selection(update, context)


async def role_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process inline button selection for role change (Restricted to ID 1079885088)."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if not query or not user:
        return

    lang = db.get_user_language(user.id)
    if user.id != ADMIN_USER_ID:
        await query.answer(t("unauthorized_admin", lang), show_alert=True)
        return

    await query.answer()
    data = query.data

    if not data or not data.startswith("set_role_"):
        return

    target_role = data.split("set_role_")[1]
    db.set_user_role(user.id, target_role)

    confirm_key = "role_selected_boss" if target_role == "boss" else "role_selected_staff"
    confirm_msg = t(confirm_key, lang)

    await query.edit_message_text(confirm_msg)

    # Refresh persistent keyboard & inline dashboard with role-specific permissions
    is_private = (chat.type == "private") if chat else True
    reply_markup = get_main_keyboard(lang, is_private=is_private, role=target_role)

    if update.effective_message:
        role_label = "ប្រធាន" if target_role == "boss" else "មន្ត្រី"
        await context.bot.send_message(
            chat_id=chat.id if chat else user.id,
            text=f"🔄 **ម៉ឺនុយត្រូវបានផ្លាស់ប្តូរទៅជា៖ {role_label}**",
            reply_markup=reply_markup
        )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command in private and group chats."""
    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    # Track/update user in database
    db.register_or_update_user(user.id, user.username, user.first_name)

    is_private = (chat.type == "private")
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id)
    role = db.get_user_role(user.id)

    msg = t("welcome_private", lang) if is_private else t("welcome_group", lang)

    # If new user has no role set yet in private chat, send welcome message then prompt role selection
    if is_private and not role:
        await update.message.reply_text(msg)
        await prompt_role_selection(update, context)
        return

    role = role or "staff"
    reply_markup = get_main_keyboard(lang, is_private=is_private, role=role)
    inline_markup = get_inline_dashboard(lang, is_private=is_private, role=role)

    await update.message.reply_text(msg, reply_markup=reply_markup)
    await context.bot.send_message(
        chat_id=chat.id,
        text="--- Action Panel ---",
        reply_markup=inline_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return

    is_private = (chat.type == "private")
    lang = db.get_chat_language(chat.id)
    role = db.get_user_role(user.id) or "staff"

    reply_markup = get_main_keyboard(lang, is_private=is_private, role=role)
    inline_markup = get_inline_dashboard(lang, is_private=is_private, role=role)

    await update.message.reply_text(t("help_text", lang), reply_markup=reply_markup)
    await update.message.reply_text("--- Executive Action Panel ---", reply_markup=inline_markup)


async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide inline keyboard to select system language."""
    chat = update.effective_chat
    if not chat:
        return

    lang = db.get_chat_language(chat.id)
    keyboard = [
        [
            InlineKeyboardButton(t("btn_lang_km", lang), callback_data="set_lang_km"),
            InlineKeyboardButton(t("btn_lang_en", lang), callback_data="set_lang_en"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(t("select_language", lang), reply_markup=reply_markup)


async def language_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process inline button selection for language change."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data
    chat = update.effective_chat
    user = update.effective_user

    if not data or not data.startswith("set_lang_") or not user:
        return

    target_lang = data.split("set_lang_")[1]
    is_private = True

    if chat and chat.type in ["group", "supergroup"]:
        db.set_group_language(chat.id, target_lang)
        is_private = False
    elif user:
        db.set_user_language(user.id, target_lang)

    role = db.get_user_role(user.id) or "staff"
    confirm_msg = t("lang_selected", target_lang)
    await query.edit_message_text(confirm_msg)

    # Refresh persistent keyboard & inline dashboard with new language
    if update.effective_message:
        reply_markup = get_main_keyboard(target_lang, is_private=is_private, role=role)
        inline_markup = get_inline_dashboard(target_lang, is_private=is_private, role=role)
        await context.bot.send_message(
            chat_id=chat.id if chat else user.id,
            text=confirm_msg,
            reply_markup=reply_markup
        )
        await context.bot.send_message(
            chat_id=chat.id if chat else user.id,
            text="--- Executive Action Panel ---",
            reply_markup=inline_markup
        )


async def navigation_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle clicks on inline dashboard navigation buttons."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return

    from handlers.private import (
        show_personal_todos,
        membertasks_command,
        prompt_add_task_options,
        prompt_complete_assigned_task
    )
    from handlers.group import grouptasks_command
    from handlers.report import report_command

    is_private = (chat.type == "private")
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id)

    if data == "cb_nav_add_task":
        await prompt_add_task_options(update, context)
    elif data == "cb_nav_complete_task":
        await prompt_complete_assigned_task(update, context)
    elif data == "cb_nav_todos" or data == "cb_nav_mytasks":
        await show_personal_todos(update, context)
    elif data == "cb_nav_member_tasks":
        await membertasks_command(update, context)
    elif data == "cb_nav_report":
        await report_command(update, context)
    elif data == "cb_nav_assign_coworker":
        await prompt_add_task_options(update, context)
    elif data == "cb_nav_complete_group":
        await grouptasks_command(update, context)
    elif data == "cb_nav_grouptasks":
        await grouptasks_command(update, context)


async def invite_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /invite command to send formal invitation message."""
    target_msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not target_msg or not user:
        return

    lang = db.get_user_language(user.id) if (chat and chat.type == "private") else db.get_chat_language(chat.id if chat else user.id)
    invite_text = t("invite_message", lang)
    await target_msg.reply_text(invite_text)


async def cancel_wizard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle ❌ Cancel inline button click across any wizard flow."""
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return

    await query.answer()
    lang = db.get_user_language(user.id)
    context.user_data.pop("task_draft", None)
    context.user_data.pop("report_draft", None)

    await query.edit_message_text(t("wizard_cancelled", lang))


async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log exceptions and handle specific Telegram API errors cleanly."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    if isinstance(context.error, Forbidden):
        logger.warning("Bot was blocked or permission denied by user.")
        return

    if isinstance(update, Update) and update.effective_message:
        chat_id = update.effective_chat.id if update.effective_chat else 0
        lang = db.get_chat_language(chat_id)
        try:
            await update.effective_message.reply_text(t("error_occurred", lang))
        except Exception as e:
            logger.error(f"Failed to send error notification message: {e}")
