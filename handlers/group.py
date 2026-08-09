"""
Group Chat Handlers (Team Delegation & Group Tasks).
Handles task delegation, mentions, group task listing, and status updates with timestamps.
"""

import datetime
import pytz
from typing import Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import Forbidden

import database as db
from i18n import t
from config import DEFAULT_TIMEZONE


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


async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the requesting user is a group administrator or creator."""
    chat = update.effective_chat
    user = update.effective_user
    if not chat or not user:
        return False
    if chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ["administrator", "creator"]
    except Exception:
        return False


import logging
logger = logging.getLogger(__name__)


async def notify_assigned_user(context: ContextTypes.DEFAULT_TYPE, task: dict, group_title: str = "") -> None:
    """Send direct private Telegram alert to assigned staff member if registered with bot."""
    assigned_username = task.get("assigned_to_username")
    if not assigned_username:
        return
    
    assigned_user = db.get_user_by_username(assigned_username)
    if not assigned_user or not assigned_user.get("user_id"):
        return

    assigned_user_id = assigned_user["user_id"]
    lang = assigned_user.get("language", "km")
    dl_str = format_dt(task.get("deadline"), lang=lang)
    assigner_name = task.get("assigned_by_username") or "ប្រធាន"

    if lang == "km":
        notify_msg = (
            f"🔔 **លោកអ្នកទទួលបានភារកិច្ចថ្មីដែលបានប្រគល់ជូន!**\n\n"
            f"📌 **បរិយាយ (Task)៖** {task['title']}\n"
            f"⏰ **កាលបរិច្ឆេទកំណត់ (Deadline)៖** {dl_str}\n"
            f"👔 **ប្រគល់ដោយប្រធាន (Assigned By)៖** @{assigner_name}\n"
            f"💬 **ក្រុម (Group)៖** {group_title or 'Group'}"
        )
    else:
        notify_msg = (
            f"🔔 **You have received a new assigned task!**\n\n"
            f"📌 **Task:** {task['title']}\n"
            f"⏰ **Deadline:** {dl_str}\n"
            f"👔 **Assigned By:** @{assigner_name}\n"
            f"💬 **Group:** {group_title or 'Group'}"
        )

    try:
        await context.bot.send_message(chat_id=assigned_user_id, text=notify_msg, parse_mode="Markdown")
        logger.info(f"Delivered private assignment notification to @{assigned_username} (ID {assigned_user_id})")
    except Exception as e:
        logger.warning(f"Could not deliver private assignment notification to @{assigned_username} (ID {assigned_user_id}): {e}")


async def assign_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /assign command in group chat.
    Syntax: /assign @username <task_description> <YYYY-MM-DD HH:MM>
    """
    chat = update.effective_chat
    user = update.effective_user
    target_msg = update.effective_message

    if not chat or not user or not target_msg or chat.type == "private":
        return

    lang = db.get_chat_language(chat.id)

    # Permission check: Only Boss (ប្រធាន) or Group Admins can delegate
    if not (db.is_boss(user.id) or await is_user_admin(update, context)):
        await target_msg.reply_text(t("unauthorized_boss_only", lang))
        return

    args = context.args or []
    if len(args) < 3:
        await target_msg.reply_text(t("invalid_syntax", lang))
        return

    target_mention = args[0]
    if not target_mention.startswith("@"):
        await target_msg.reply_text(t("invalid_syntax", lang))
        return

    target_username = target_mention.lstrip("@")
    rest_args = " ".join(args[1:])

    # Extract deadline from the end of rest_args (YYYY-MM-DD HH:MM)
    tokens = rest_args.rsplit(" ", 2)
    if len(tokens) < 3:
        await target_msg.reply_text(t("invalid_syntax", lang))
        return

    potential_date = f"{tokens[1]} {tokens[2]}"
    deadline = parse_datetime(potential_date)
    
    if not deadline:
        await target_msg.reply_text(t("invalid_syntax", lang))
        return

    task_description = tokens[0]

    # Store task in database with 'group' scope
    task = db.create_task(
        scope="group",
        title=task_description,
        user_id=user.id,
        group_id=chat.id,
        assigned_to_username=target_username,
        assigned_by_id=user.id,
        assigned_by_username=user.username or user.first_name,
        deadline=deadline
    )

    dl_str = format_dt(deadline, lang=lang)

    # Send public group confirmation with @mention
    response_msg = t(
        "task_assigned",
        lang,
        f"@{target_username}",
        task_description,
        dl_str,
        user.first_name
    )
    await target_msg.reply_text(response_msg)

    # Dispatch direct private notification to assigned staff member
    await notify_assigned_user(context, task, group_title=chat.title or "Group")


async def grouptasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /grouptasks in a group chat.
    Lists all pending tasks assigned within this group.
    """
    chat = update.effective_chat
    target_msg = update.effective_message
    if not chat or not target_msg or chat.type == "private":
        return

    lang = db.get_chat_language(chat.id)
    tasks = db.get_group_tasks(chat.id)

    if not tasks:
        await target_msg.reply_text(t("group_tasks_empty", lang))
        return

    lines = [t("group_tasks_header", lang)]
    keyboard = []

    for task in tasks:
        cr_str = format_dt(task.get("created_at"))
        dl_str = format_dt(task.get("deadline"))

        assignee = f"@{task['assigned_to_username']}" if task.get("assigned_to_username") else "Unassigned"
        lines.append(f"• {assignee} - {task['title']}\n  📅 បង្កើត (Created): {cr_str} | ⏰ កំណត់ (Deadline): {dl_str}")

        title_snippet = task['title'][:25] + ('...' if len(task['title']) > 25 else '')
        btn_text = f"✓ {t('btn_complete', lang)}: {title_snippet}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"done_grp_{task['task_id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await target_msg.reply_text("\n".join(lines), reply_markup=reply_markup)


async def complete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /complete <task_id> in group or private chat.
    """
    chat = update.effective_chat
    user = update.effective_user
    target_msg = update.effective_message
    if not chat or not user or not target_msg:
        return

    lang = db.get_chat_language(chat.id)
    args = context.args or []

    if not args:
        await target_msg.reply_text(t("invalid_syntax", lang))
        return

    task_id = args[0]
    is_admin = await is_user_admin(update, context)
    completed = db.complete_task(task_id, user.id, is_admin=is_admin)

    if completed:
        cr_str = format_dt(completed.get("created_at"))
        cm_str = format_dt(completed.get("completed_at"))
        await target_msg.reply_text(t("task_completed_group", lang, user.first_name, cr_str, cm_str))
    else:
        await target_msg.reply_text(t("todo_not_found", lang))
