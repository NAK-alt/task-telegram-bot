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
    keyboard = [
        # Row 1: Morning slots
        [
            InlineKeyboardButton("⏱️ 08:00", callback_data=f"cal_time_{date_str}_08:00"),
            InlineKeyboardButton("⏱️ 09:00", callback_data=f"cal_time_{date_str}_09:00"),
            InlineKeyboardButton("⏱️ 10:00", callback_data=f"cal_time_{date_str}_10:00"),
            InlineKeyboardButton("⏱️ 11:00", callback_data=f"cal_time_{date_str}_11:00"),
        ],
        # Row 2: Afternoon slots
        [
            InlineKeyboardButton("⏱️ 14:00", callback_data=f"cal_time_{date_str}_14:00"),
            InlineKeyboardButton("⏱️ 15:00", callback_data=f"cal_time_{date_str}_15:00"),
            InlineKeyboardButton("⏱️ 16:00", callback_data=f"cal_time_{date_str}_16:00"),
            InlineKeyboardButton("⏱️ 17:00", callback_data=f"cal_time_{date_str}_17:00"),
        ],
        # Row 3: Evening slots
        [
            InlineKeyboardButton("⏱️ 18:00", callback_data=f"cal_time_{date_str}_18:00"),
            InlineKeyboardButton("⏱️ 19:00", callback_data=f"cal_time_{date_str}_19:00"),
            InlineKeyboardButton("⏱️ 20:00", callback_data=f"cal_time_{date_str}_20:00"),
            InlineKeyboardButton("⏱️ 21:00", callback_data=f"cal_time_{date_str}_21:00"),
        ],
        # Row 4: Custom Time & Navigation
        [
            InlineKeyboardButton("↩️ ត្រឡប់ (Back)" if lang == "km" else "↩️ Back", callback_data="cal_back_to_date"),
            InlineKeyboardButton(t("btn_cancel", lang), callback_data="cancel_wizard")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)
