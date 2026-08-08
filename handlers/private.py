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
from handlers.common import get_main_keyboard


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
    """Format Firestore/Python datetime object into clean local timezone string HH:MM (DD/MM/YYYY)."""
    if not dt_val:
        return "គ្មាន" if lang == "km" else "None"
    try:
        local_tz = pytz.timezone(tz_name)
        if hasattr(dt_val, "to_datetime"):
            dt_val = dt_val.to_datetime()
        if dt_val.tzinfo is None:
            dt_val = pytz.utc.localize(dt_val)
        local_dt = dt_val.astimezone(local_tz)
        if local_dt.hour == 23 and local_dt.minute == 59:
            eod_str = "ត្រឹមចុងថ្ងៃ" if lang == "km" else "End of Day"
            return f"{eod_str} ({local_dt.strftime('%d/%m/%Y')})"
        return local_dt.strftime("%H:%M (%d/%m/%Y)")
    except Exception:
        return "គ្មាន" if lang == "km" else "None"


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
    if not user or not chat or not target_msg:
        return

    lang = db.get_user_language(user.id) if (chat.type == "private") else db.get_chat_language(chat.id)

    if chat.type != "private":
        msg = (
            "⚠️ ពាក្យបញ្ជា /todo សម្រាប់ប្រើប្រាស់ផ្ទាល់ខ្លួនក្នុង Private Chat តែប៉ុណ្ណោះ (@TaskOSHBot)។ ក្នុងក្រុមសូមប្រើ @username ឈ្មោះភារកិច្ច ឬ /assign ដើម្បីប្រគល់ភារកិច្ចជូនមន្ត្រី។"
            if lang == "km" else
            "⚠️ The /todo command is exclusively for personal to-dos in Private Chat (@TaskOSHBot). In group chats, use @username task or /assign to delegate tasks."
        )
        await target_msg.reply_text(msg)
        return

    args = context.args or []

    if not args:
        await target_msg.reply_text(t("invalid_syntax", lang))
        return

    subcommand = args[0].lower()

    if subcommand == "add":
        if len(args) < 2:
            await target_msg.reply_text(t("invalid_syntax", lang))
            return
        
        # Determine if deadline is provided at the end
        deadline = None
        description = " ".join(args[1:])

        # Try parsing last two tokens as HH:MM DD-MM-YYYY or YYYY-MM-DD HH:MM
        if len(args) >= 3:
            possible_dt = f"{args[-2]} {args[-1]}"
            parsed = parse_datetime(possible_dt, db.get_user_timezone(user.id))
            if parsed:
                deadline = parsed
                description = " ".join(args[1:-2])

        task = db.create_task(
            scope="private",
            title=description,
            user_id=user.id,
            deadline=deadline
        )

        dl_str = format_dt(deadline, lang=lang)
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
            cr_str = format_dt(completed.get("created_at"), lang=lang)
            cm_str = format_dt(completed.get("completed_at"), lang=lang)
            await target_msg.reply_text(t("todo_completed", lang, cr_str, cm_str))
        else:
            await target_msg.reply_text(t("todo_not_found", lang))
    else:
        await target_msg.reply_text(t("invalid_syntax", lang))


async def todos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Consolidated task handler."""
    await show_personal_todos(update, context)


async def show_personal_todos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send user list of ALL tasks (both pending and completed) for full overview."""
    user = update.effective_user
    chat = update.effective_chat
    target_msg = update.effective_message
    if not user or not target_msg:
        return

    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)
    role = db.get_user_role(user.id) or "staff"

    all_tasks = db.get_all_tasks_for_staff(user.id, username=user.username or "")
    main_kb = get_main_keyboard(lang, is_private=is_private, role=role)

    if not all_tasks:
        await target_msg.reply_text(t("all_tasks_empty", lang), reply_markup=main_kb)
        return

    header_title = "📋 **បញ្ជីភារកិច្ចទាំងអស់៖**\n" if lang == "km" else "📋 **All Tasks Overview:**\n"
    response_lines = [header_title.strip()]
    keyboard = []

    for task in all_tasks:
        is_completed = (task.get("status") == "completed")
        status_icon = "✅" if is_completed else "⏳"
        dl_str = format_dt(task.get("deadline"), lang=lang)

        if is_completed:
            cm_str = format_dt(task.get("completed_at"), lang=lang)
            line = f"{status_icon} **{task['title']}** (បានបញ្ចប់: {cm_str})"
        else:
            line = f"{status_icon} **{task['title']}** (កំណត់: {dl_str})"

        response_lines.append(line)

        # Only add completion button if the task is STILL PENDING
        if not is_completed:
            title_snippet = task['title'][:25] + ('...' if len(task['title']) > 25 else '')
            btn_text = f"✓ {t('btn_complete', lang)}: {title_snippet}"
            cb_prefix = "done_priv_" if task.get("scope") == "private" else "done_grp_"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"{cb_prefix}{task['task_id']}")])

    inline_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    await target_msg.reply_text("\n".join(response_lines), reply_markup=main_kb)
    if inline_markup:
        await target_msg.reply_text("--- Action Panel ---", reply_markup=inline_markup)


async def mytasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Consolidated task handler."""
    await show_personal_todos(update, context)


async def private_done_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button clicks to complete private or assigned group tasks."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if not query or not user:
        return

    await query.answer()
    data = query.data
    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)

    if data.startswith("done_priv_"):
        task_id = data.replace("done_priv_", "")
        completed = db.complete_task(task_id, user.id)
        if completed:
            cr_str = format_dt(completed.get("created_at"), lang=lang)
            cm_str = format_dt(completed.get("completed_at"), lang=lang)
            await query.edit_message_text(t("todo_completed", lang, cr_str, cm_str))
        else:
            await query.edit_message_text(t("todo_not_found", lang))
    elif data.startswith("done_grp_"):
        task_id = data.replace("done_grp_", "")
        completed = db.complete_task(task_id, user.id)
        if completed:
            cr_str = format_dt(completed.get("created_at"), lang=lang)
            cm_str = format_dt(completed.get("completed_at"), lang=lang)
            await query.edit_message_text(t("task_completed_group", lang, user.first_name, cr_str, cm_str))
        else:
            await query.edit_message_text(t("todo_not_found", lang))


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Boss / Admin Handler: Permanently delete a task by task_id.
    Syntax: /delete <task_id>
    Allowed ONLY for Boss (ប្រធាន) or Telegram Admin ID 1079885088.
    """
    user = update.effective_user
    chat = update.effective_chat
    target_msg = update.effective_message
    if not user or not target_msg:
        return

    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)

    if not db.is_admin_or_boss(user.id):
        await target_msg.reply_text(t("unauthorized_boss_only", lang))
        return

    args = context.args or []
    if not args:
        prompt_text = (
            "សូមបញ្ចូលពាក្យបញ្ជាដើម្បីលុបភារកិច្ច៖\n/delete <លេខសម្គាល់ភារកិច្ច>\n\nឧទាហរណ៍៖ /delete b682399d"
            if lang == "km" else
            "Please specify task ID to delete:\n/delete <task_id>\n\nExample: /delete b682399d"
        )
        await target_msg.reply_text(prompt_text)
        return

    task_id = args[0]
    deleted = db.delete_task(task_id, user.id)

    if deleted:
        confirm_text = (
            f"🗑️ **ភារកិច្ច #{task_id} ត្រូវបានលុបចេញពីប្រព័ន្ធ និងរបាយការណ៍ទាំងអស់ដោយជោគជ័យ!**"
            if lang == "km" else
            f"🗑️ **Task #{task_id} has been permanently deleted from all reports and lists!**"
        )
        await target_msg.reply_text(confirm_text)
    else:
        await target_msg.reply_text(t("todo_not_found", lang))


async def private_delete_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button clicks to delete tasks (Boss / Admin only)."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if not query or not user:
        return

    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)

    if not db.is_admin_or_boss(user.id):
        await query.answer(t("unauthorized_boss_only", lang), show_alert=True)
        return

    await query.answer()
    data = query.data

    if data.startswith("del_task_"):
        task_id = data.replace("del_task_", "")
        deleted = db.delete_task(task_id, user.id)
        if deleted:
            confirm_text = (
                f"🗑️ **ភារកិច្ច #{task_id} ត្រូវបានលុបចេញពីប្រព័ន្ធ និងរបាយការណ៍ទាំងអស់!**"
                if lang == "km" else
                f"🗑️ **Task #{task_id} deleted from all system records and reports!**"
            )
            await query.edit_message_text(confirm_text)
        else:
            await query.edit_message_text(t("todo_not_found", lang))


async def prompt_add_task_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user with interactive inline choice for adding task (Self vs Staff in private, Staff assignment only in group)."""
    user = update.effective_user
    chat = update.effective_chat
    target_msg = update.effective_message
    if not user or not target_msg or not chat:
        return
    
    is_private = (chat.type == "private")
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id)
    cancel_btn = InlineKeyboardButton(t("btn_cancel", lang), callback_data="cancel_wizard")
    cancel_kb = InlineKeyboardMarkup([[cancel_btn]])

    if not is_private:
        # In Group Chat: Only allow assigning members (@username task)
        context.user_data["task_draft"] = {"scope": "group"}
        await target_msg.reply_text(t("wizard_prompt_staff_task", lang), reply_markup=cancel_kb)
        return

    # In Private Chat: Offer Personal To-Do or Staff Assignment (for Boss)
    role = db.get_user_role(user.id) or "staff"
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
        await target_msg.reply_text(t("wizard_prompt_personal_title", lang), reply_markup=cancel_kb)


async def add_task_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process selection of Personal vs Staff task type in wizard."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if not query or not user:
        return

    await query.answer()
    data = query.data
    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)
    cancel_btn = InlineKeyboardButton(t("btn_cancel", lang), callback_data="cancel_wizard")
    cancel_kb = InlineKeyboardMarkup([[cancel_btn]])

    if data == "add_type_personal":
        if not is_private:
            msg = (
                "⚠️ នៅក្នុងក្រុម (Group) អាចធ្វើបានតែការប្រគល់ភារកិច្ចជូនមន្ត្រី (@username)។ សម្រាប់ភារកិច្ចផ្ទាល់ខ្លួន សូមផ្ញើសារផ្ទាល់ខ្លួនមកកាន់ Bot (@TaskOSHBot)។"
                if lang == "km" else
                "⚠️ Group chats are exclusively for assigning staff members (@username). For personal to-dos, please send a private message to @TaskOSHBot."
            )
            await query.edit_message_text(msg)
            return

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
    """Process inline calendar date picker callbacks."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if not query or not user:
        return

    await query.answer()
    data = query.data
    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)

    # Handle Admin Editing Deadline flow if active
    editing_dl_id = context.user_data.get("editing_dl_task_id")
    if editing_dl_id:
        if data.startswith("cal_day_"):
            date_part = data.replace("cal_day_", "")
            if date_part == "none":
                db.update_task_deadline(editing_dl_id, None, user.id)
                context.user_data.pop("editing_dl_task_id", None)
                await query.edit_message_text(f"✅ **កាលបរិច្ឆេទកំណត់នៃភារកិច្ច #{editing_dl_id} ត្រូវបានលុបចេញ (គ្មានការកំណត់)!**")
                return
            else:
                context.user_data["editing_dl_date"] = date_part
                time_kb = build_time_picker_keyboard(date_part, lang=lang)
                await query.edit_message_text(f"📅 **កាលបរិច្ឆេទ៖ {date_part}**\n\n⏰ **សូមជ្រើសរើសម៉ោងកំណត់៖**", reply_markup=time_kb)
                return
        elif data.startswith("cal_time_"):
            raw_val = data.replace("cal_time_", "")
            date_str, time_str = raw_val.split("_")
            full_dt_str = f"{date_str} {time_str}"
            deadline = parse_flexible_datetime(full_dt_str)
            db.update_task_deadline(editing_dl_id, deadline, user.id)
            context.user_data.pop("editing_dl_task_id", None)
            context.user_data.pop("editing_dl_date", None)
            dl_str = format_dt(deadline, lang=lang)
            await query.edit_message_text(f"✅ **កាលបរិច្ឆេទកំណត់នៃភារកិច្ច #{editing_dl_id} ត្រូវបានប្តូរជា៖ {dl_str}**")
            return

    draft = context.user_data.get("task_draft")
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
    Check if user is currently in a task creation draft state or task editing state.
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

    await finalize_task_with_deadline(update, context, draft, deadline=deadline, lang=lang)


async def prompt_complete_assigned_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trigger list of PENDING (not done) tasks with 1-tap inline completion buttons."""
    user = update.effective_user
    chat = update.effective_chat
    target_msg = update.effective_message
    if not user or not target_msg:
        return

    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)
    role = db.get_user_role(user.id) or "staff"

    private_tasks = db.get_private_tasks(user.id)
    assigned_tasks = db.get_tasks_assigned_to_user(username=user.username or "", user_id=user.id)

    main_kb = get_main_keyboard(lang, is_private=is_private, role=role)

    if not private_tasks and not assigned_tasks:
        empty_msg = (
            "✨ មិនមានភារកិច្ចដែលកំពុងរង់ចាំនោះទេ។"
            if lang == "km" else
            "✨ You have no pending tasks."
        )
        await target_msg.reply_text(empty_msg, reply_markup=main_kb)
        return

    header_text = (
        "✓ **សូមជ្រើសរើសភារកិច្ចដែលត្រូវបញ្ចប់៖**\n"
        if lang == "km" else
        "✓ **Select a task to complete:**\n"
    )
    response_lines = [header_text.strip()]
    keyboard = []

    pending_all = list(private_tasks)
    for t_item in assigned_tasks:
        if t_item not in pending_all:
            pending_all.append(t_item)

    for task in pending_all:
        dl_str = format_dt(task.get("deadline"), lang=lang)
        line = f"⏳ **{task['title']}** (កំណត់: {dl_str})"
        response_lines.append(line)

        title_snippet = task['title'][:25] + ('...' if len(task['title']) > 25 else '')
        btn_text = f"✓ {t('btn_complete', lang)}: {title_snippet}"
        cb_prefix = "done_priv_" if task.get("scope") == "private" else "done_grp_"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"{cb_prefix}{task['task_id']}")])

    inline_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    await target_msg.reply_text("\n".join(response_lines), reply_markup=main_kb)
    if inline_markup:
        await target_msg.reply_text("--- Action Panel ---", reply_markup=inline_markup)


async def membertasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Boss Persona Handler: Inspect all tasks assigned to team members.
    Automatically displays staff task summary if no username argument is passed.
    Syntax: /membertasks [@username]
    """
    user = update.effective_user
    chat = update.effective_chat
    target_msg = update.effective_message
    if not user or not target_msg:
        return

    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)
    role = db.get_user_role(user.id) or "staff"
    main_kb = get_main_keyboard(lang, is_private=is_private, role=role)

    # Permission check: Only Boss (ប្រធាន) can inspect member assignments
    if not db.is_boss(user.id):
        await target_msg.reply_text(t("unauthorized_boss_only", lang), reply_markup=main_kb)
        return

    args = context.args or []

    # Filter by specific username if argument passed
    if args:
        target_mention = args[0]
        target_username = target_mention.lstrip("@").lower()
        tasks = db.get_tasks_assigned_to_user(username=target_username)

        if not tasks:
            await target_msg.reply_text(t("member_tasks_empty", lang, f"@{target_username}"), reply_markup=main_kb)
            return

        lines = [f"👥 **បញ្ជីភារកិច្ចមន្ត្រី @{target_username}៖**\n"]
        keyboard = []
        for task in tasks:
            dl_str = format_dt(task.get("deadline"), lang=lang)
            lines.append(f"⏳ **{task['title']}** (កំណត់: {dl_str})")
            title_snippet = task['title'][:25] + ('...' if len(task['title']) > 25 else '')
            btn_text = f"✓ {t('btn_complete', lang)}: {title_snippet}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"done_grp_{task['task_id']}")])

        inline_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await target_msg.reply_text("\n".join(lines), reply_markup=main_kb)
        if inline_markup:
            await target_msg.reply_text("--- Action Panel ---", reply_markup=inline_markup)
        return

    # No argument passed: Automatically retrieve ALL staff assignments for the boss!
    assigned_tasks = db.get_all_assigned_by_boss(user.id)
    pending_tasks = [t_item for t_item in assigned_tasks if t_item.get("status") == "pending"]

    if not pending_tasks:
        empty_msg = (
            "✨ មិនទាន់មានភារកិច្ចដែលបានប្រគល់ជូនមន្ត្រីដែលកំពុងរង់ចាំនៅឡើយទេ។"
            if lang == "km" else
            "✨ No pending staff assignments found."
        )
        await target_msg.reply_text(empty_msg, reply_markup=main_kb)
        return

    # Group tasks by staff username
    by_staff = {}
    for task in pending_tasks:
        staff_name = f"@{task['assigned_to_username']}" if task.get("assigned_to_username") else "Unassigned"
        by_staff.setdefault(staff_name, []).append(task)

    header = "👥 **បញ្ជីភារកិច្ចមន្ត្រីទាំងអស់ (Staff Assignments)៖**\n" if lang == "km" else "👥 **Staff Assignments Summary:**\n"
    response_lines = [header.strip()]
    keyboard = []

    for staff_name, s_tasks in by_staff.items():
        response_lines.append(f"👤 **{staff_name}** ({len(s_tasks)} ភារកិច្ច)៖")
        for task in s_tasks:
            dl_str = format_dt(task.get("deadline"), lang=lang)
            response_lines.append(f"  ⏳ **{task['title']}** (កំណត់: {dl_str})")

            title_snippet = task['title'][:18] + ('...' if len(task['title']) > 18 else '')
            btn_comp = InlineKeyboardButton(f"✓ {title_snippet}", callback_data=f"done_grp_{task['task_id']}")
            btn_del = InlineKeyboardButton(f"🗑️ លុប #{task['task_id']}", callback_data=f"del_task_{task['task_id']}")
            keyboard.append([btn_comp, btn_del])
        response_lines.append("")

    inline_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await target_msg.reply_text("\n".join(response_lines), reply_markup=main_kb)
    if inline_markup:
        await target_msg.reply_text("--- Action Panel ---", reply_markup=inline_markup)
