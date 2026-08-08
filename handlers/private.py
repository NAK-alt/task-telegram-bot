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
from calendar_picker import build_calendar_keyboard, build_time_picker_keyboard


def parse_datetime(date_str: str, tz_name: str = DEFAULT_TIMEZONE) -> Optional[datetime.datetime]:
    """Parse date/time string into UTC datetime."""
    text = date_str.strip()
    local_tz = pytz.timezone(tz_name)
    formats = ["%H:%M %d-%m-%Y", "%H:%M %d/%m/%Y", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M"]
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(text, fmt)
            local_dt = local_tz.localize(dt)
            return local_dt.astimezone(pytz.utc)
        except ValueError:
            continue
    return None


def format_dt(dt_val: Optional[Any], tz_name: str = DEFAULT_TIMEZONE, lang: str = "km") -> str:
    """Format Firestore/Python datetime object into local timezone string HH:MM || DD-MM-YYYY or End of Day || DD-MM-YYYY."""
    if not dt_val:
        return "N/A"
    try:
        local_tz = pytz.timezone(tz_name)
        if hasattr(dt_val, "to_datetime"):
            dt_val = dt_val.to_datetime()
        if dt_val.tzinfo is None:
            dt_val = pytz.utc.localize(dt_val)
        local_dt = dt_val.astimezone(local_tz)
        if local_dt.hour == 23 and local_dt.minute == 59:
            eod_str = "ត្រឹមចុងថ្ងៃ" if lang == "km" else "End of Day"
            return f"{eod_str} || {local_dt.strftime('%d-%m-%Y')}"
        return local_dt.strftime("%H:%M || %d-%m-%Y")
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
        await target_msg.reply_text(t("todo_added", lang, description, dl_str))

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
            await target_msg.reply_text(t("todo_completed", lang, cr_str, cm_str))
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

            line = f"• {task['title']}\n  📅 បង្កើត (Created): {cr_str} | ⏰ កំណត់ (Deadline): {dl_str}"
            response_lines.append(line)

            title_snippet = task['title'][:25] + ('...' if len(task['title']) > 25 else '')
            btn_text = f"✓ {t('btn_complete', lang)}: {title_snippet}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"done_priv_{task['task_id']}")])

    # 2. Group Tasks Assigned to User
    if assigned_tasks:
        response_lines.append(f"\n{t('my_tasks_header', lang).strip()}")
        for task in assigned_tasks:
            cr_str = format_dt(task.get("created_at"))
            dl_str = format_dt(task.get("deadline"))

            line = f"• {task['title']}\n  📅 បង្កើត (Created): {cr_str} | ⏰ កំណត់ (Deadline): {dl_str}"
            response_lines.append(line)

            title_snippet = task['title'][:25] + ('...' if len(task['title']) > 25 else '')
            btn_text = f"✓ {t('btn_complete', lang)}: {title_snippet}"
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
            await query.edit_message_text(t("todo_completed", lang, cr_str, cm_str))
        else:
            await query.edit_message_text(t("todo_not_found", lang))
    elif data.startswith("done_grp_"):
        task_id = data.replace("done_grp_", "")
        completed = db.complete_task(task_id, user.id)
        if completed:
            cr_str = format_dt(completed.get("created_at"))
            cm_str = format_dt(completed.get("completed_at"))
            await query.edit_message_text(t("task_completed_group", lang, user.first_name, cr_str, cm_str))
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

    cancel_btn = InlineKeyboardButton(t("btn_cancel", lang), callback_data="cancel_wizard")
    if role == "boss":
        inline_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t("btn_type_personal", lang), callback_data="add_type_personal"),
                InlineKeyboardButton(t("btn_type_staff", lang), callback_data="add_type_staff")
            ],
            [cancel_btn]
        ])
        await target_msg.reply_text(t("wizard_select_type", lang), reply_markup=inline_kb)
    else:
        # Staff: Immediately prompt for personal task description
        context.user_data["task_draft"] = {"scope": "private"}
        cancel_kb = InlineKeyboardMarkup([[cancel_btn]])
        await target_msg.reply_text(t("wizard_prompt_personal_title", lang), reply_markup=cancel_kb)


async def add_task_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process selection of Personal vs Staff task type in wizard."""
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return

    await query.answer()
    data = query.data
    lang = db.get_user_language(user.id)
    cancel_btn = InlineKeyboardButton(t("btn_cancel", lang), callback_data="cancel_wizard")
    cancel_kb = InlineKeyboardMarkup([[cancel_btn]])

    if data == "add_type_personal":
        context.user_data["task_draft"] = {"scope": "private"}
        await query.edit_message_text(t("wizard_prompt_personal_title", lang), reply_markup=cancel_kb)
    elif data == "add_type_staff":
        context.user_data["task_draft"] = {"scope": "group"}
        await query.edit_message_text(t("wizard_prompt_staff_task", lang), reply_markup=cancel_kb)


def parse_flexible_datetime(date_str: str, tz_name: str = DEFAULT_TIMEZONE, base_date: Optional[str] = None) -> Optional[datetime.datetime]:
    """Parse flexible date/time strings into UTC datetime."""
    text = date_str.strip()
    if text.lower() in ["none", "no", "0", "គ្មាន", "skip", "n/a"]:
        return None
    local_tz = pytz.timezone(tz_name)
    now = datetime.datetime.now(local_tz)

    if base_date:
        try:
            full_str = f"{base_date} {text}"
            dt = datetime.datetime.strptime(full_str, "%Y-%m-%d %H:%M")
            local_dt = local_tz.localize(dt)
            return local_dt.astimezone(pytz.utc)
        except ValueError:
            pass

    formats = [
        "%H:%M %d-%m-%Y",
        "%H:%M %d/%m/%Y",
        "%H:%M %Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(text, fmt)
            if " " not in fmt:
                dt = dt.replace(hour=23, minute=59, second=0)
            local_dt = local_tz.localize(dt)
            return local_dt.astimezone(pytz.utc)
        except ValueError:
            continue

    # Try HH:MM for today/tomorrow
    try:
        dt_time = datetime.datetime.strptime(text, "%H:%M")
        local_dt = now.replace(hour=dt_time.hour, minute=dt_time.minute, second=0, microsecond=0)
        if local_dt <= now:
            local_dt += datetime.timedelta(days=1)
        return local_dt.astimezone(pytz.utc)
    except ValueError:
        pass

    return None


async def finalize_task_with_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE, draft: dict, deadline: Optional[datetime.datetime], lang: str) -> None:
    """Save task to database and notify user with confirmation text."""
    user = update.effective_user
    chat = update.effective_chat
    query = update.callback_query

    if draft["scope"] == "private":
        task = db.create_task(
            scope="private",
            title=draft["title"],
            user_id=user.id,
            deadline=deadline
        )
        dl_str = format_dt(deadline)
        confirm_text = t("todo_added", lang, draft["title"], dl_str)
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
            draft["title"],
            dl_str,
            user.first_name
        )

    context.user_data.pop("task_draft", None)
    if query:
        await query.edit_message_text(confirm_text)
    elif update.effective_message:
        await update.effective_message.reply_text(confirm_text)


async def calendar_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process calendar grid navigation, date selection, and time slot selection."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if not query or not user:
        return

    await query.answer()
    data = query.data
    lang = db.get_user_language(user.id) if (chat and chat.type == "private") else db.get_chat_language(chat.id if chat else user.id)

    draft = context.user_data.get("task_draft")
    if data == "cal_ignore":
        return

    if not draft or "title" not in draft:
        await query.edit_message_text(t("error_occurred", lang))
        return

    # Handle Navigation: prev / next month
    if data.startswith("cal_nav_"):
        parts = data.split("_")  # ['cal', 'nav', '2026', '8', 'prev']
        year, month, action = int(parts[2]), int(parts[3]), parts[4]
        if action == "prev":
            month -= 1
            if month < 1:
                month = 12
                year -= 1
        elif action == "next":
            month += 1
            if month > 12:
                month = 1
                year += 1
        
        cal_kb = build_calendar_keyboard(year, month, lang=lang)
        prompt_text = t("wizard_prompt_deadline", lang, draft["title"])
        await query.edit_message_text(prompt_text, reply_markup=cal_kb)

    # Handle Date Selection: cal_day_YYYY-MM-DD or cal_day_none
    elif data.startswith("cal_day_"):
        date_part = data.replace("cal_day_", "")
        if date_part == "none":
            await finalize_task_with_deadline(update, context, draft, deadline=None, lang=lang)
        else:
            draft["selected_date"] = date_part
            time_kb = build_time_picker_keyboard(date_part, lang=lang)
            prompt_text = (
                f"📅 **កាលបរិច្ឆេទ៖ {date_part}**\n\n⏰ **សូមវាយបញ្ចូលម៉ោងកំណត់ (ឧទាហរណ៍៖ 14:30) ៖**\n*(ឬចុចប៊ូតុង '🗓️ ត្រឹមចុងថ្ងៃ' ខាងក្រោម)*"
                if lang == "km" else
                f"📅 **Selected Date: {date_part}**\n\n⏰ **Please type your time (e.g. 14:30):**\n*(or click '🗓️ End of Day' below)*"
            )
            await query.edit_message_text(prompt_text, reply_markup=time_kb, parse_mode="Markdown")

    # Handle Back to Date Picker
    elif data == "cal_back_to_date":
        local_tz = pytz.timezone(DEFAULT_TIMEZONE)
        now = datetime.datetime.now(local_tz)
        cal_kb = build_calendar_keyboard(now.year, now.month, lang=lang)
        prompt_text = t("wizard_prompt_deadline", lang, draft["title"])
        await query.edit_message_text(prompt_text, reply_markup=cal_kb)

    # Handle Time Slot Selection: cal_time_YYYY-MM-DD_HH:MM
    elif data.startswith("cal_time_"):
        raw_val = data.replace("cal_time_", "")
        date_str, time_str = raw_val.split("_")
        full_dt_str = f"{date_str} {time_str}"
        deadline = parse_flexible_datetime(full_dt_str)
        await finalize_task_with_deadline(update, context, draft, deadline=deadline, lang=lang)


async def handle_task_creation_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if user is currently in a task creation draft state.
    Handles both Step 1 (Title/Assignee) and Step 2 (Interactive Calendar & Text Input).
    Returns True if handled, False otherwise.
    """
    user = update.effective_user
    msg = update.message
    chat = update.effective_chat
    if not user or not msg or not msg.text:
        return False

    draft = context.user_data.get("task_draft")
    if not draft:
        return False

    lang = db.get_user_language(user.id)
    text = msg.text.strip()

    # Step 2: User is typing custom deadline text because title was already collected
    if draft.get("step") == "awaiting_deadline":
        base_date = draft.get("selected_date")
        deadline = parse_flexible_datetime(text, base_date=base_date)
        if deadline is None and text.lower() not in ["none", "no", "0", "គ្មាន", "skip", "n/a"]:
            error_msg = (
                "⚠️ ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ។ សូមជ្រើសរើសតាមរយៈប្រតិទិនខាងលើ ឬវាយបញ្ចូលទម្រង់៖ YYYY-MM-DD HH:MM (ឧទាហរណ៍៖ 2026-08-20 17:00 ឬ 20/08/2026) ឬ 14:30!"
                if lang == "km" else
                "⚠️ Invalid date format. Please choose from calendar or type: YYYY-MM-DD HH:MM (e.g. 2026-08-20 17:00) or 14:30!"
            )
            await msg.reply_text(error_msg)
            return True

        await finalize_task_with_deadline(update, context, draft, deadline=deadline, lang=lang)
        return True

    # Step 1: User is typing title (and assignee if staff assignment)
    if draft["scope"] == "private":
        draft["title"] = text
    else:  # group / staff assignment
        tokens = text.split(" ", 1)
        if len(tokens) < 2 or not tokens[0].startswith("@"):
            await msg.reply_text(t("wizard_prompt_staff_task", lang))
            return True
        draft["assigned_to_username"] = tokens[0].lstrip("@")
        draft["title"] = tokens[1]

    draft["step"] = "awaiting_deadline"

    local_tz = pytz.timezone(DEFAULT_TIMEZONE)
    now = datetime.datetime.now(local_tz)
    cal_kb = build_calendar_keyboard(now.year, now.month, lang=lang)

    prompt_text = t("wizard_prompt_deadline", lang, draft["title"])
    await msg.reply_text(prompt_text, reply_markup=cal_kb)
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
