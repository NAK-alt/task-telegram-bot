"""
Background Scheduler Module.
Manages automated deadline reminder alerts and morning executive daily briefings.
"""

import datetime
import logging
import pytz
from telegram.ext import ContextTypes
from telegram.error import Forbidden, TelegramError

import database as db
from i18n import t
from config import DEFAULT_TIMEZONE, DAILY_BRIEFING_TIME

logger = logging.getLogger(__name__)


async def check_deadline_reminders_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Periodic job (every 60 seconds) to check for upcoming or due tasks.
    Sends targeted alerts to groups or private chats.
    """
    logger.debug("Executing deadline reminder check...")
    due_tasks = db.get_upcoming_reminders()

    local_tz = pytz.timezone(DEFAULT_TIMEZONE)

    for task in due_tasks:
        task_id = task.get("task_id")
        scope = task.get("scope")
        deadline = task.get("deadline")

        if hasattr(deadline, "to_datetime"):
            deadline = deadline.to_datetime()
        if deadline and deadline.tzinfo is None:
            deadline = pytz.utc.localize(deadline)

        dl_str = deadline.astimezone(local_tz).strftime("%Y-%m-%d %H:%M") if deadline else "N/A"

        if scope == "group":
            group_id = task.get("group_id")
            if not group_id:
                continue

            lang = db.get_chat_language(group_id)
            assignee = f"@{task['assigned_to_username']}" if task.get("assigned_to_username") else "Team"

            msg = t(
                "group_reminder_alert",
                lang,
                assignee,
                task.get("title", ""),
                dl_str
            )

            try:
                await context.bot.send_message(chat_id=group_id, text=msg)
                db.mark_task_reminded(task_id)
                logger.info(f"Sent group deadline reminder for task {task_id} to group {group_id}")
            except TelegramError as e:
                logger.error(f"Failed to send group reminder for task {task_id} to group {group_id}: {e}")

        elif scope == "private":
            user_id = task.get("user_id")
            if not user_id:
                continue

            lang = db.get_user_language(user_id)
            msg = t(
                "private_reminder_alert",
                lang,
                task.get("title", ""),
                dl_str
            )

            try:
                await context.bot.send_message(chat_id=user_id, text=msg)
                db.mark_task_reminded(task_id)
                logger.info(f"Sent private deadline reminder for task {task_id} to user {user_id}")
            except Forbidden:
                logger.warning(f"User {user_id} has not started a private chat or blocked bot. Cannot deliver reminder.")
            except TelegramError as e:
                logger.error(f"Failed to send private reminder for task {task_id} to user {user_id}: {e}")


async def daily_briefing_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Scheduled job running every morning to dispatch a personalized briefing of pending tasks.
    """
    logger.info("Executing daily morning executive briefing job...")
    users = db.get_all_registered_users()
    today_str = datetime.datetime.now(pytz.timezone(DEFAULT_TIMEZONE)).strftime("%Y-%m-%d")

    for user in users:
        user_id = user.get("user_id")
        if not user_id:
            continue

        lang = user.get("language", "km")
        private_tasks = db.get_private_tasks(user_id)

        local_tz = pytz.timezone(DEFAULT_TIMEZONE)
        lines = [t("daily_briefing_header", lang, today_str)]

        if not private_tasks:
            lines.append(t("daily_briefing_empty", lang))
        else:
            for task in private_tasks:
                dl_val = task.get("deadline")
                dl_str = "N/A"
                if dl_val:
                    if hasattr(dl_val, "to_datetime"):
                        dl_val = dl_val.to_datetime()
                    if dl_val.tzinfo is None:
                        dl_val = pytz.utc.localize(dl_val)
                    dl_str = dl_val.astimezone(local_tz).strftime("%H:%M")
                lines.append(f"• {task['title']} (Time: {dl_str})")

        briefing_text = "\n".join(lines)

        try:
            await context.bot.send_message(chat_id=user_id, text=briefing_text)
            logger.info(f"Successfully delivered daily briefing to user {user_id}")
        except Forbidden:
            logger.warning(f"User {user_id} has not started chat with bot. Briefing skipped.")
        except TelegramError as e:
            logger.error(f"Error delivering daily briefing to user {user_id}: {e}")


def setup_scheduler(application) -> None:
    """
    Register recurring background jobs with python-telegram-bot's JobQueue.
    """
    job_queue = application.job_queue

    if not job_queue:
        logger.error("JobQueue is not initialized! Ensure python-telegram-bot[job-queue] is installed.")
        return

    # Run deadline reminder check every 60 seconds
    job_queue.run_repeating(
        check_deadline_reminders_job,
        interval=60,
        first=10,
        name="deadline_reminders"
    )

    # Parse briefing time HH:MM
    try:
        hour, minute = map(int, DAILY_BRIEFING_TIME.split(":"))
        briefing_time = datetime.time(hour=hour, minute=minute, tzinfo=pytz.timezone(DEFAULT_TIMEZONE))
        
        # Schedule daily briefing job
        job_queue.run_daily(
            daily_briefing_job,
            time=briefing_time,
            name="daily_briefing"
        )
        logger.info(f"Daily briefing scheduled for {DAILY_BRIEFING_TIME} {DEFAULT_TIMEZONE}")
    except Exception as e:
        logger.error(f"Failed to schedule daily briefing job: {e}")
