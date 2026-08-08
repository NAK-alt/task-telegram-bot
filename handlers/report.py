"""
Executive & Staff Reporting Module.
Generates on-demand reports with Telegram inline summaries or downloadable Excel (.xlsx) files.
Supports Boss (Executive) and Officer/Staff roles with strict data isolation.
"""

import io
import datetime
import pytz
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes

import database as db
from i18n import t
from config import DEFAULT_TIMEZONE
from handlers.private import format_dt


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /report command or '📊 របាយការណ៍ (ប្រធាន)' / '📊 របាយការណ៍ (មន្ត្រី)' button press.
    """
    user = update.effective_user
    chat = update.effective_chat
    target_msg = update.effective_message

    if not user or not target_msg:
        return

    is_private = (chat.type == "private") if chat else True
    lang = db.get_user_language(user.id) if is_private else db.get_chat_language(chat.id if chat else user.id)

    cancel_btn = InlineKeyboardButton(t("btn_cancel", lang), callback_data="cancel_wizard")

    if db.is_boss(user.id):
        # Boss persona: Choose between Boss Personal To-Dos vs Staff Member Assignments
        inline_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t("btn_rpt_personal", lang), callback_data="rpt_type_personal"),
            ],
            [
                InlineKeyboardButton(t("btn_rpt_staff", lang), callback_data="rpt_type_staff"),
            ],
            [cancel_btn]
        ])
        await target_msg.reply_text(t("prompt_report_type", lang), reply_markup=inline_kb)
    else:
        # Officer / Staff persona: Directly choose format for self tasks (Personal To-Dos & Boss Assignments)
        fmt_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(t("btn_fmt_msg", lang), callback_data="rpt_fmt_msg_self"),
            ],
            [
                InlineKeyboardButton(t("btn_fmt_excel", lang), callback_data="rpt_fmt_excel_self"),
            ],
            [cancel_btn]
        ])
        await target_msg.reply_text(t("prompt_report_staff_fmt", lang), reply_markup=fmt_kb)


async def report_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user to choose output format (Telegram vs Excel) for selected report type."""
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return

    await query.answer()
    data = query.data
    lang = db.get_user_language(user.id)
    cancel_btn = InlineKeyboardButton(t("btn_cancel", lang), callback_data="cancel_wizard")

    report_type = data.replace("rpt_type_", "")  # 'personal' or 'staff'

    fmt_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_fmt_msg", lang), callback_data=f"rpt_fmt_msg_{report_type}"),
        ],
        [
            InlineKeyboardButton(t("btn_fmt_excel", lang), callback_data=f"rpt_fmt_excel_{report_type}"),
        ],
        [cancel_btn]
    ])

    await query.edit_message_text(t("prompt_report_fmt", lang), reply_markup=fmt_kb)


async def report_generate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate and deliver Telegram text summary or Excel document."""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    if not query or not user:
        return

    await query.answer()
    data = query.data
    lang = db.get_user_language(user.id) if (chat and chat.type == "private") else db.get_chat_language(chat.id if chat else user.id)

    # Parse callback string: e.g., rpt_fmt_msg_personal, rpt_fmt_excel_staff, rpt_fmt_msg_self
    parts = data.replace("rpt_fmt_", "").split("_", 1)  # ['msg', 'personal'] or ['excel', 'self']
    fmt = parts[0]  # 'msg' or 'excel'
    report_type = parts[1]  # 'personal', 'staff', or 'self'

    if report_type == "personal":
        if not db.is_boss(user.id):
            await query.edit_message_text(t("unauthorized_boss_only", lang))
            return
        tasks = db.get_all_personal_tasks(user.id)
        title = t("report_personal_title", lang)
        filename_prefix = "Boss_Personal_Tasks"

    elif report_type == "staff":
        if not db.is_boss(user.id):
            await query.edit_message_text(t("unauthorized_boss_only", lang))
            return
        tasks = db.get_all_assigned_by_boss(user.id)
        title = t("report_staff_title", lang)
        filename_prefix = "Staff_Assignments"

    else:  # report_type == 'self'
        tasks = db.get_all_tasks_for_staff(user.id, username=user.username or "")
        title = t("report_staff_self_title", lang)
        filename_prefix = f"Staff_Report_{user.username or user.id}"

    total = len(tasks)
    completed_count = sum(1 for t in tasks if t.get("status") == "completed")
    pending_count = total - completed_count
    pct = round((completed_count / total * 100), 1) if total > 0 else 0.0

    if fmt == "msg":
        # Generate Markdown Summary Message
        lines = [
            title,
            t("report_stat_summary", lang, total, completed_count, str(pct), pending_count),
            "---------------------------------------"
        ]

        if not tasks:
            lines.append("មិនមានទិន្នន័យភារកិច្ចនោះទេ។ (No task records found)")
        else:
            for task in tasks:
                status_icon = "✅" if task.get("status") == "completed" else "⏳"
                cr_str = format_dt(task.get("created_at"))
                dl_str = format_dt(task.get("deadline"))
                cm_str = format_dt(task.get("completed_at"))

                if report_type == "staff":
                    target_staff = f"@{task['assigned_to_username']}" if task.get("assigned_to_username") else "Unassigned"
                    line = f"{status_icon} [{task['task_id']}] {target_staff} - {task['title']}\n  📅 បង្កើត: {cr_str} | ⏰ កំណត់: {dl_str}"
                elif report_type == "self":
                    scope_tag = "(Personal)" if task.get("scope") == "private" else "(Assigned)"
                    line = f"{status_icon} [{task['task_id']}] {scope_tag} {task['title']}\n  📅 បង្កើត: {cr_str} | ⏰ កំណត់: {dl_str}"
                else:
                    line = f"{status_icon} [{task['task_id']}] {task['title']}\n  📅 បង្កើត: {cr_str} | ⏰ កំណត់: {dl_str}"

                if task.get("status") == "completed":
                    line += f" | ✅ បញ្ចប់: {cm_str}"
                lines.append(line)

        await query.edit_message_text("\n".join(lines))

    elif fmt == "excel":
        # Generate Excel (.xlsx) Document
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Task Report"

        # Styling Definitions
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9")
        )

        if report_type == "personal":
            headers = ["Task ID", "Title / Description", "Scope", "Status", "Created At", "Deadline", "Completed At"]
        elif report_type == "staff":
            headers = ["Task ID", "Assigned Staff", "Title / Description", "Status", "Assigned By", "Created At", "Deadline", "Completed At"]
        else:  # self
            headers = ["Task ID", "Task Type", "Title / Description", "Status", "Assigned By", "Created At", "Deadline", "Completed At"]

        ws.append(headers)

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Fill Data Rows
        for task in tasks:
            cr_str = format_dt(task.get("created_at"))
            dl_str = format_dt(task.get("deadline"))
            cm_str = format_dt(task.get("completed_at"))
            status_str = "Completed" if task.get("status") == "completed" else "Pending"

            if report_type == "personal":
                row = [
                    task.get("task_id", ""),
                    task.get("title", ""),
                    task.get("scope", "private"),
                    status_str,
                    cr_str,
                    dl_str,
                    cm_str if status_str == "Completed" else "N/A"
                ]
            elif report_type == "staff":
                staff_name = f"@{task['assigned_to_username']}" if task.get("assigned_to_username") else "Unassigned"
                row = [
                    task.get("task_id", ""),
                    staff_name,
                    task.get("title", ""),
                    status_str,
                    task.get("assigned_by_username", "Boss"),
                    cr_str,
                    dl_str,
                    cm_str if status_str == "Completed" else "N/A"
                ]
            else:  # self
                type_tag = "Personal To-Do" if task.get("scope") == "private" else "Assigned by Boss"
                assigner = task.get("assigned_by_username", "Self") if task.get("scope") == "group" else "Self"
                row = [
                    task.get("task_id", ""),
                    type_tag,
                    task.get("title", ""),
                    status_str,
                    assigner,
                    cr_str,
                    dl_str,
                    cm_str if status_str == "Completed" else "N/A"
                ]

            ws.append(row)

        # Apply borders and auto-width
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(headers)):
            for cell in row:
                cell.border = border
                cell.alignment = Alignment(vertical="center")

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        # Save workbook to memory buffer
        output_buffer = io.BytesIO()
        wb.save(output_buffer)
        output_buffer.seek(0)

        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{now_str}.xlsx"

        await query.edit_message_text(f"✓ Excel document generated successfully. Sending {filename}...")

        await context.bot.send_document(
            chat_id=chat.id,
            document=InputFile(output_buffer, filename=filename),
            caption=f"📊 {title.strip()}\nTotal: {total} | Completed: {completed_count} ({pct}%) | Pending: {pending_count}"
        )
