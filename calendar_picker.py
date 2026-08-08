"""
Interactive Telegram Inline Calendar Grid & Time Selector.
Generates dynamic monthly calendar grids and time slot selection keyboards.
"""

import calendar
import datetime
import pytz
from typing import Optional, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import DEFAULT_TIMEZONE
from i18n import t

KHMER_MONTHS = [
    "មករា", "កុម្ភៈ", "មីនា", "មេសា", "ឧសភា", "មិថុនា",
    "កក្កដា", "សីហា", "កញ្ញា", "តុលា", "វិច្ឆិកា", "ធ្នូ"
]

ENGLISH_MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

KHMER_WEEKDAYS = ["ច", "អង្គ", "ពុ", "ព្រ", "សុ", "ស", "អា"]
ENGLISH_WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def get_month_name(month: int, lang: str = "km") -> str:
    if lang == "km":
        return KHMER_MONTHS[month - 1]
    return ENGLISH_MONTHS[month - 1]


def build_calendar_keyboard(year: int, month: int, lang: str = "km") -> InlineKeyboardMarkup:
    """Build a monthly calendar inline keyboard grid."""
    keyboard = []
    local_tz = pytz.timezone(DEFAULT_TIMEZONE)
    today = datetime.datetime.now(local_tz).date()

    # Row 1: Month Name & Navigation (< Month Year >)
    month_str = get_month_name(month, lang)
    nav_row = [
        InlineKeyboardButton("«", callback_data=f"cal_nav_{year}_{month}_prev"),
        InlineKeyboardButton(f"{month_str} {year}", callback_data="cal_ignore"),
        InlineKeyboardButton("»", callback_data=f"cal_nav_{year}_{month}_next")
    ]
    keyboard.append(nav_row)

    # Row 2: Weekday Headers
    weekdays = KHMER_WEEKDAYS if lang == "km" else ENGLISH_WEEKDAYS
    keyboard.append([InlineKeyboardButton(w, callback_data="cal_ignore") for w in weekdays])

    # Month calendar grid matrix (weeks of days)
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
            else:
                day_date = datetime.date(year, month, day)
                if day_date < today:
                    # Disabled past days
                    row.append(InlineKeyboardButton(f"·{day}·", callback_data="cal_ignore"))
                else:
                    # Selectable day
                    prefix = "📍" if day_date == today else ""
                    row.append(InlineKeyboardButton(f"{prefix}{day}", callback_data=f"cal_day_{year:04d}-{month:02d}-{day:02d}"))
        keyboard.append(row)

    # Action Row: No Deadline & Cancel
    btn_none = "🚫 គ្មានកាលបរិច្ឆេទ" if lang == "km" else "🚫 No Deadline"
    btn_cancel = t("btn_cancel", lang)

    keyboard.append([
        InlineKeyboardButton(btn_none, callback_data="cal_day_none"),
        InlineKeyboardButton(btn_cancel, callback_data="cancel_wizard")
    ])

    return InlineKeyboardMarkup(keyboard)


def build_time_picker_keyboard(date_str: str, lang: str = "km") -> InlineKeyboardMarkup:
    """Build time slot selection keyboard for selected date (YYYY-MM-DD)."""
    btn_eod = "🗓️ ត្រឹមចុងថ្ងៃ" if lang == "km" else "🗓️ End of Day"
    btn_back = "↩️ ត្រឡប់ (Back)" if lang == "km" else "↩️ Back"
    btn_cancel = t("btn_cancel", lang)

    keyboard = [
        # Option: Finished by end of that day (23:59)
        [
            InlineKeyboardButton(btn_eod, callback_data=f"cal_time_{date_str}_23:59"),
        ],
        # Navigation & Cancel
        [
            InlineKeyboardButton(btn_back, callback_data="cal_back_to_date"),
            InlineKeyboardButton(btn_cancel, callback_data="cancel_wizard")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)
