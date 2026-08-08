"""
Private Chat Handlers (Boss Persona & Individual Member Scope).
Enforces strict scope isolation for personal To-Dos and multi-group task aggregation.
Includes step-by-step interactive wizard with quick deadline presets and creation/completion timestamps.
"""

import datetime
import pytz
from typing import Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
from i18n import t
from config import DEFAULT_TIMEZONE


def parse_datetime(date_str: str, tz_name: str = DEFAULT_TIMEZONE) -> Optional[datetime.datetime]:
    """Parse date/time string in format 'YYYY-MM-DD HH:MM' into UTC datetime."""
    try:
        local_tz = pytz.timezone(tz_name)
        dt = datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M")
        local_dt = local_tz.localize(dt)
        return local_dt.astimezone(pytz.utc)
    except ValueError:
        return None


def format_dt(dt_val: Optional[Any], tz_name: str = DEFAULT_TIMEZONE) -> str:
    """Format Firestore/Python datetime object into local timezone string YYYY-MM-DD HH:MM."""
    if not dt_val:
        return "N/A"
    try:
        local_tz = pytz.timezone(tz_name)
        if hasattr(dt_val, "to_datetime"):
            dt_val = dt_val.to_datetime()
        if dt_val.tzinfo is None:
            dt_val = pytz.utc.localize(dt_val)
        return dt_val.astimezone(local_tz).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "N/A"


async def todo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /todo command in private chat.
    Syntax:
      /todo add <description> [YYYY-MM-DD HH:MM]
      /todo list
      /todo done <task_id>
    """
    user = update.effective_user
    chat = update.effective_chat
    target_msg = update.effective_message
    if not user or not chat or not target_msg or chat.type != "private":
        return

    lang = db.get_user_language(user.id)
    args = context.args or []

    if not args:
        await target_msg.reply_text(t("invalid_syntax", lang))
        return

    subcommand = args[0].lower()

    if subcommand == "add":
        if len(args) < 2:
            await target_msg.reply_text(t("invalid_syntax", lang))
            return
        
        full_text = " ".join(args[1:])
        deadline = None
        description = full_text

        # Check if last 2 tokens match YYYY-MM-DD HH:MM
        tokens = full_text.rsplit(" ", 2)
        if len(tokens) == 3:
            potential_date = f"{tokens[1]} {tokens[2]}"
            dt_parsed = parse_datetime(potential_date)
            if dt_parsed:
                deadline = dt_parsed
                description = tokens[0]

        task = db.create_task(
            scope="private",
            title=description,
            user_id=user.id,
            deadline=deadline
        )

        dl_str = format_dt(deadline)
        await target_msg.reply_text(t("todo_added", lang, task["task_id"], description, dl_str))

    elif subcommand in ["list", "show"]:
        await show_personal_todos(update, context)

    elif subcommand == "done":
        if len(args) < 2:
            await target_msg.reply_text(t("invalid_syntax", lang))
            return
        task_id = args[1]
        completed = db.complete_task(task_id, user.id)
        if completed:
            cr_str = format_dt(completed.get("created_at"))
            cm_str = format_dt(completed.get("completed_at"))
            await target_msg.reply_text(t("todo_completed", lang, task_id, cr_str, cm_str))
        else:
            await target_msg.reply_text(t("todo_not_found", lang))
    else:
        await target_msg.reply_text(t("invalid_syntax", lang))


async def todos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Alias for /todo list."""
    await show_personal_todos(update, context)


async def show_personal_todos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display all pending personal to-dos AND group tasks assigned to the user in a consolidated list."""
    user = update.effective_user
    chat = update.effective_chat
    target_msg = update.effective_message
    if not user or not target_msg:
        return

    from handlers.common import get_main_keyboard

    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)
    role = db.get_user_role(user.id) or "staff"
    main_kb = get_main_keyboard(lang, is_private=is_private, role=role)

    private_tasks = db.get_private_tasks(user.id)
    assigned_tasks = db.get_tasks_assigned_to_user(username=user.username or "", user_id=user.id)

    if not private_tasks and not assigned_tasks:
        await target_msg.reply_text(t("all_tasks_empty", lang), reply_markup=main_kb)
        return

    response_lines = [t("todo_list_header", lang)]
    keyboard = []

    # 1. Personal To-Dos
    if private_tasks:
        for task in private_tasks:
            cr_str = format_dt(task.get("created_at"))
            dl_str = format_dt(task.get("deadline"))

            line = f"• [{task['task_id']}] {task['title']}\n  📅 បង្កើត (Created): {cr_str} | ⏰ កំណត់ (Deadline): {dl_str}"
            response_lines.append(line)

            btn_text = f"✓ {t('btn_complete', lang)} #{task['task_id']}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"done_priv_{task['task_id']}")])

    # 2. Group Tasks Assigned to User
    if assigned_tasks:
        response_lines.append(f"\n{t('my_tasks_header', lang).strip()}")
        for task in assigned_tasks:
            cr_str = format_dt(task.get("created_at"))
            dl_str = format_dt(task.get("deadline"))

            line = f"• [{task['task_id']}] {task['title']}\n  📅 បង្កើត (Created): {cr_str} | ⏰ កំណត់ (Deadline): {dl_str}"
            response_lines.append(line)

            btn_text = f"✓ {t('btn_complete', lang)} #{task['task_id']}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"done_grp_{task['task_id']}")])

    inline_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    # Refresh reply keyboard and send inline completion buttons
    await target_msg.reply_text("\n".join(response_lines), reply_markup=main_kb)
    if inline_markup:
        await target_msg.reply_text("--- Active Completion Panel ---", reply_markup=inline_markup)


async def mytasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Consolidated task handler."""
    await show_personal_todos(update, context)


async def private_done_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button clicks to complete private or assigned group tasks."""
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return

    await query.answer()
    data = query.data
    lang = db.get_user_language(user.id)

    if data.startswith("done_priv_"):
        task_id = data.replace("done_priv_", "")
        completed = db.complete_task(task_id, user.id)
        if completed:
            cr_str = format_dt(completed.get("created_at"))
            cm_str = format_dt(completed.get("completed_at"))
            await query.edit_message_text(t("todo_completed", lang, task_id, cr_str, cm_str))
        else:
            await query.edit_message_text(t("todo_not_found", lang))
    elif data.startswith("done_grp_"):
        task_id = data.replace("done_grp_", "")
        completed = db.complete_task(task_id, user.id)
        if completed:
            cr_str = format_dt(completed.get("created_at"))
            cm_str = format_dt(completed.get("completed_at"))
            await query.edit_message_text(t("task_completed_group", lang, task_id, user.first_name, cr_str, cm_str))
        else:
            await query.edit_message_text(t("todo_not_found", lang))


async def prompt_add_task_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user with interactive inline choice for adding task (Self vs Staff)."""
    user = update.effective_user
    chat = update.effective_chat
    target_msg = update.effective_message
    if not user or not target_msg:
        return
    
    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)
    role = db.get_user_role(user.id) or "staff"

    if role == "boss":
        inline_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t("btn_type_personal", lang), callback_data="add_type_personal"),
                InlineKeyboardButton(t("btn_type_staff", lang), callback_data="add_type_staff")
            ]
        ])
        await target_msg.reply_text(t("wizard_select_type", lang), reply_markup=inline_kb)
    else:
        # Staff: Immediately prompt for personal task description
        context.user_data["task_draft"] = {"scope": "private"}
        await target_msg.reply_text(t("wizard_prompt_personal_title", lang))


async def add_task_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process selection of Personal vs Staff task type in wizard."""
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return

    await query.answer()
    data = query.data
    lang = db.get_user_language(user.id)

    if data == "add_type_personal":
        context.user_data["task_draft"] = {"scope": "private"}
        await query.edit_message_text(t("wizard_prompt_personal_title", lang))
    elif data == "add_type_staff":
        context.user_data["task_draft"] = {"scope": "group"}
        await query.edit_message_text(t("wizard_prompt_staff_task", lang))


async def handle_task_creation_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if user is currently in a task creation draft state.
    Returns True if handled, False otherwise.
    """
    user = update.effective_user
    msg = update.message
    if not user or not msg or not msg.text:
        return False

    draft = context.user_data.get("task_draft")
    if not draft:
        return False

    lang = db.get_user_language(user.id)
    text = msg.text.strip()

    if draft["scope"] == "private":
        draft["title"] = text
    else:  # group / staff assignment
        tokens = text.split(" ", 1)
        if len(tokens) < 2 or not tokens[0].startswith("@"):
            await msg.reply_text(t("wizard_prompt_staff_task", lang))
            return True
        draft["assigned_to_username"] = tokens[0].lstrip("@")
        draft["title"] = tokens[1]

    # Present Quick Deadline Presets Inline Keyboard
    dl_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_dl_today_17", lang), callback_data="dl_preset_today_17"),
            InlineKeyboardButton(t("btn_dl_tomorrow_09", lang), callback_data="dl_preset_tomorrow_09"),
        ],
        [
            InlineKeyboardButton(t("btn_dl_monday_09", lang), callback_data="dl_preset_monday_09"),
            InlineKeyboardButton(t("btn_dl_none", lang), callback_data="dl_preset_none"),
        ]
    ])

    prompt_text = t("wizard_prompt_deadline", lang, draft["title"])
    await msg.reply_text(prompt_text, reply_markup=dl_keyboard)
    return True


async def deadline_preset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process quick deadline preset selection and save task to database."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if not query or not user:
        return

    await query.answer()
    data = query.data
    lang = db.get_user_language(user.id) if (chat and chat.type == "private") else db.get_chat_language(chat.id if chat else user.id)

    draft = context.user_data.get("task_draft")
    if not draft or "title" not in draft:
        await query.edit_message_text(t("error_occurred", lang))
        return

    local_tz = pytz.timezone(DEFAULT_TIMEZONE)
    now = datetime.datetime.now(local_tz)

    deadline = None

    if data == "dl_preset_today_17":
        deadline_dt = now.replace(hour=17, minute=0, second=0, microsecond=0)
        if deadline_dt <= now:
            deadline_dt += datetime.timedelta(days=1)
        deadline = deadline_dt.astimezone(pytz.utc)

    elif data == "dl_preset_tomorrow_09":
        tomorrow = now + datetime.timedelta(days=1)
        deadline_dt = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        deadline = deadline_dt.astimezone(pytz.utc)

    elif data == "dl_preset_monday_09":
        days_ahead = (0 - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        next_monday = now + datetime.timedelta(days=days_ahead)
        deadline_dt = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
        deadline = deadline_dt.astimezone(pytz.utc)

    elif data == "dl_preset_none":
        deadline = None

    # Save to database
    if draft["scope"] == "private":
        task = db.create_task(
            scope="private",
            title=draft["title"],
            user_id=user.id,
            deadline=deadline
        )
        dl_str = format_dt(deadline)
        confirm_text = t("todo_added", lang, task["task_id"], draft["title"], dl_str)
    else:
        task = db.create_task(
            scope="group",
            title=draft["title"],
            user_id=user.id,
            group_id=chat.id if (chat and chat.type != "private") else user.id,
            assigned_to_username=draft.get("assigned_to_username"),
            assigned_by_id=user.id,
            assigned_by_username=user.username or user.first_name,
            deadline=deadline
        )
        dl_str = format_dt(deadline)
        confirm_text = t(
            "task_assigned",
            lang,
            f"@{draft.get('assigned_to_username')}",
            task["task_id"],
            draft["title"],
            dl_str,
            user.first_name
        )

    # Clear draft state
    context.user_data.pop("task_draft", None)

    await query.edit_message_text(confirm_text)


async def prompt_complete_assigned_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger list of assigned tasks with 1-tap inline completion buttons."""
    await show_personal_todos(update, context)


async def membertasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Boss Persona Handler: Inspect all tasks assigned to a specific team member.
    Syntax: /membertasks @username
    """
    user = update.effective_user
    chat = update.effective_chat
    target_msg = update.effective_message
    if not user or not target_msg:
        return

    from handlers.common import get_main_keyboard
    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)
    role = db.get_user_role(user.id) or "staff"
    main_kb = get_main_keyboard(lang, is_private=is_private, role=role)

    # Permission check: Only Boss (ប្រធាន) can inspect member assignments
    if not db.is_boss(user.id):
        await target_msg.reply_text(t("unauthorized_boss_only", lang), reply_markup=main_kb)
        return

    args = context.args or []

    if not args:
        await target_msg.reply_text(t("prompt_member_tasks", lang), reply_markup=main_kb)
        return

    target_mention = args[0]
    target_username = target_mention.lstrip("@")

    tasks = db.get_tasks_assigned_to_user(username=target_username)

    if not tasks:
        await target_msg.reply_text(t("member_tasks_empty", lang, f"@{target_username}"), reply_markup=main_kb)
        return

    lines = [t("member_tasks_header", lang, f"@{target_username}")]
    keyboard = []

    for task in tasks:
        cr_str = format_dt(task.get("created_at"))
        dl_str = format_dt(task.get("deadline"))

        lines.append(f"• [{task['task_id']}] {task['title']}\n  📅 បង្កើត (Created): {cr_str} | ⏰ កំណត់ (Deadline): {dl_str}")

        btn_text = f"✓ {t('btn_complete', lang)} #{task['task_id']}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"done_grp_{task['task_id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await target_msg.reply_text("\n".join(lines), reply_markup=main_kb)
    if reply_markup:
        await target_msg.reply_text("--- Member Tasks Panel ---", reply_markup=reply_markup)
