"""
Internationalization (i18n) Module.
Provides formal translations in Khmer (km, default) and English (en).
Replaces Boss with 'ប្រធាន' / 'ប្រធានការិយាល័យ' and Staff with 'មន្ត្រី'.
"""

from typing import Dict, Any

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "km": {
        # Common / System
        "welcome_private": "សូមស្វាគមន៍មកកាន់ប្រព័ន្ធគ្រប់គ្រងភារកិច្ច និងជំនួយការប្រធាន!",
        "welcome_group": "ប្រព័ន្ធគ្រប់គ្រងភារកិច្ចក្រុមត្រូវបានបើកដំណើរការក្នុងក្រុមនេះ។\nសូមប្រើប្រាស់ /help ដើម្បីពិនិត្យមើលពាក្យបញ្ជាដែលមាន។",
        "help_text": (
            "ប្រព័ន្ធគ្រប់គ្រងភារកិច្ច និងជំនួយការប្រធាន\n\n"
            "ពាក្យបញ្ជាសម្រាប់ប្រធានការិយាល័យ (ប្រធាន):\n"
            "/todo add <បរិយាយ> [YYYY-MM-DD HH:MM] - បន្ថែមភារកិច្ចផ្ទាល់ខ្លួន\n"
            "/assign @អ្នកប្រើប្រាស់ <បរិយាយ> <YYYY-MM-DD HH:MM> - ប្រគល់ភារកិច្ចជូនមន្ត្រី\n"
            "/membertasks @username - ពិនិត្យភារកិច្ចដែលបានប្រគល់ជូនមន្ត្រី\n"
            "/report - ទាញយករបាយការណ៍ ( Telegram / Excel )\n"
            "/todos - បង្ហាញបញ្ជីភារកិច្ចផ្ទាល់ខ្លួន និងភារកិច្ចប្រគល់ជូន\n\n"
            "ពាក្យបញ្ជាសម្រាប់មន្ត្រី:\n"
            "/todo add <បរិយាយ> [YYYY-MM-DD HH:MM] - បន្ថែមភារកិច្ចផ្ទាល់ខ្លួន\n"
            "/todos - បង្ហាញភារកិច្ចផ្ទាល់ខ្លួន និងភារកិច្ចដែលបានប្រគល់ជូនខ្ញុំ\n"
            "/complete <លេខសម្គាល់ភារកិច្ច> - កត់សម្គាល់ភារកិច្ចថាបានបញ្ចប់\n"
            "/role - ផ្លាស់ប្តូរតួនាទី (ប្រធានការិយាល័យ / មន្ត្រី)\n"
            "/language - ផ្លាស់ប្តូរភាសា"
        ),
        "lang_selected": "ភាសាត្រូវបានផ្លាស់ប្តូរទៅជា៖ ភាសាខ្មែរ។",
        "select_language": "សូមជ្រើសរើសភាសាប្រព័ន្ធ៖",
        "unauthorized_admin": "បរាជ័យ៖ ពាក្យបញ្ជានេះត្រូវបានកំណត់ជូនតែអ្នកគ្រប់គ្រងប៉ុណ្ណោះ។",
        "unauthorized_boss_only": "បរាជ័យ៖ ការប្រគល់ភារកិច្ច និងការពិនិត្យភារកិច្ចសមាជិកត្រូវបានកំណត់ជូនតែ ប្រធានការិយាល័យ (ប្រធាន) ប៉ុណ្ណោះ។",
        "invalid_syntax": "ទម្រង់ពាក្យបញ្ជាមិនត្រឹមត្រូវ។ សូមពិនិត្យការណែនាំតាមរយៈ /help។",
        "error_occurred": "កំហុសប្រព័ន្ធបានកើតឡើង។ ប្រតិបត្តិការមិនអាចដំណើរការបានទេ។",
        "bot_blocked_notice": "សមាជិក %s មិនទាន់បានចាប់ផ្តើមប្រអប់សារផ្ទាល់ខ្លួនជាមួយប្រព័ន្ធនៅឡើយទេ។ ការជូនដំណឹងផ្ទាល់ខ្លួនមិនអាចផ្ញើបានទេ។",

        # Role Selection
        "select_role": "សូមជ្រើសរើសតួនាទីរបស់អ្នកក្នុងប្រព័ន្ធ៖",
        "btn_role_boss": "👔 ប្រធានការិយាល័យ (ប្រធាន)",
        "btn_role_staff": "👤 មន្ត្រី",
        "role_selected_boss": "តួនាទីរបស់អ្នកត្រូវបានកំណត់ជា៖ ប្រធានការិយាល័យ (ប្រធាន)។",
        "role_selected_staff": "តួនាទីរបស់អ្នកត្រូវបានកំណត់ជា៖ មន្ត្រី។",
        
        # Interactive Wizard (Step-by-Step Creation)
        "wizard_select_type": "➕ ជ្រើសរើសប្រភេទភារកិច្ចដែលត្រូវបន្ថែម៖",
        "btn_type_personal": "👤 ភារកិច្ចផ្ទាល់ខ្លួន",
        "btn_type_staff": "👥 ប្រគល់ជូនមន្ត្រី",
        "wizard_prompt_personal_title": "📝 សូមវាយបញ្ចូលឈ្មោះភារកិច្ចផ្ទាល់ខ្លួនរបស់អ្នក៖\n(ឧទាហរណ៍៖ រៀបចំរបាយការណ៍)",
        "wizard_prompt_staff_task": "👥 សូមវាយបញ្ចូលឈ្មោះមន្ត្រី និងភារកិច្ចក្នុងទម្រង់៖\n@username ឈ្មោះភារកិច្ច\n\nឧទាហរណ៍៖ @sokha រៀបចំរបាយការណ៍",
        "wizard_prompt_deadline": "⏰ សូមវាយបញ្ចូលកាលបរិច្ឆេទ និងម៉ោងកំណត់ (Deadline) សម្រាប់៖ '%s'\n\nទម្រង់៖ YYYY-MM-DD HH:MM (ឧទាហរណ៍៖ 2026-08-20 17:00 ឬ 20/08/2026)\n* វាយ 'គ្មាន' ប្រសិនបើគ្មានកាលបរិច្ឆេទកំណត់",
        "btn_dl_today_17": "⏱️ ថ្ងៃនេះ 17:00",
        "btn_dl_tomorrow_09": "📅 ស្អែក 09:00",
        "btn_dl_monday_09": "📆 ថ្ងៃច័ន្ទ 09:00",
        "btn_dl_none": "🚫 គ្មានកាលបរិច្ឆេទ",
        
        # Executive Reports (Telegram / Excel)
        "prompt_report_type": "📊 ប្រព័ន្ធរបាយការណ៍ភារកិច្ច (សម្រាប់ប្រធានការិយាល័យ)\n\nសូមជ្រើសរើសប្រភេទរបាយការណ៍ដែលត្រូវពិនិត្យ៖",
        "prompt_report_staff_fmt": "📊 ប្រព័ន្ធរបាយការណ៍ភារកិច្ចមន្ត្រី\n\nសូមជ្រើសរើសទម្រង់បង្ហាញរបាយការណ៍ភារកិច្ចរបស់អ្នក៖",
        "btn_rpt_personal": "📋 របាយការណ៍ភារកិច្ចផ្ទាល់ខ្លួន",
        "btn_rpt_staff": "👥 របាយការណ៍ភារកិច្ចមន្ត្រី",
        "prompt_report_fmt": "📥 ជ្រើសរើសទម្រង់បង្ហាញរបាយការណ៍៖",
        "btn_fmt_msg": "💬 បង្ហាញក្នុង Telegram",
        "btn_fmt_excel": "📥 ទាញយកជាឯកសារ Excel (.xlsx)",
        "report_personal_title": "📊 របាយការណ៍សង្ខេបភារកិច្ចផ្ទាល់ខ្លួនរបស់ប្រធាន\n",
        "report_staff_title": "📊 របាយការណ៍សង្ខេបភារកិច្ចដែលបានប្រគល់ជូនមន្ត្រី\n",
        "report_staff_self_title": "📊 របាយការណ៍សង្ខេបភារកិច្ចមន្ត្រី (ផ្ទាល់ខ្លួន និងភារកិច្ចប្រគល់ជូន)\n",
        "report_stat_summary": "📈 ស្ថិតិសរុប៖\n• ភារកិច្ចសរុប៖ %d\n• បានបញ្ចប់៖ %d (%s%%)\n• កំពុងរង់ចាំ៖ %d\n\n",

        # Tasks - Private Scope
        "todo_added": "✅ **ភារកិច្ចផ្ទាល់ខ្លួនត្រូវបានរក្សាទុកដោយជោគជ័យ!**\n\n📌 **បរិយាយ (Task)៖** %s\n⏰ **កាលបរិច្ឆេទកំណត់ (Deadline)៖** %s",
        "todo_list_header": "📋 **បញ្ជីភារកិច្ចទាំងអស់ (កំពុងរង់ចាំ & បានបញ្ចប់)៖**\n",
        "todo_empty": "✨ មិនមានភារកិច្ចផ្ទាល់ខ្លួននោះទេ។",
        "todo_completed": "✅ **ភារកិច្ចផ្ទាល់ខ្លួនត្រូវបានកត់សម្គាល់ថាបានបញ្ចប់!**\n\n📅 **កាលបរិច្ឆេទបង្កើត៖** %s\n🎉 **កាលបរិច្ឆេទបញ្ចប់៖** %s",
        "todo_not_found": "⚠️ រកមិនឃើញភារកិច្ចដែលបានស្នើសុំ ឬភារកិច្ចនេះត្រូវបានបញ្ចប់រួចរាល់។",
        "all_tasks_empty": "✨ លោកអ្នកមិនទាន់មានភារកិច្ចផ្ទាល់ខ្លួន ឬភារកិច្ចដែលបានប្រគល់ជូននៅឡើយទេ។",
        "prompt_add_options": "សូមជ្រើសរើសទម្រង់បន្ថែមភារកិច្ច៖\n\n1. ភារកិច្ចផ្ទាល់ខ្លួន៖\n/todo add <បរិយាយ> [HH:MM || DD-MM-YYYY]\n\n2. ប្រគល់ជូនមន្ត្រីក្នុងក្រុម (សម្រាប់ប្រធាន)៖\n/assign @username <បរិយាយ> <HH:MM || DD-MM-YYYY>",
        "prompt_complete_help": "សូមចុចលើប៊ូតុងខាងក្រោម ដើម្បីកត់សម្គាល់ភារកិច្ចថាបានបញ្ចប់៖",

        # Tasks - Group Scope & Boss Member Checking
        "task_assigned": "👥 **ភារកិច្ចថ្មីត្រូវបានប្រគល់ជូន៖** %s\n\n📌 **បរិយាយ (Task)៖** %s\n⏰ **កាលបរិច្ឆេទកំណត់ (Deadline)៖** %s\n👔 **ប្រគល់ដោយប្រធាន៖** %s",
        "group_tasks_header": "📋 **បញ្ជីភារកិច្ចក្រុមដែលកំពុងរង់ចាំក្នុងក្រុមនេះ៖**\n",
        "group_tasks_empty": "✨ មិនមានភារកិច្ចដែលកំពុងរង់ចាំក្នុងក្រុមនេះទេ។",
        "my_tasks_header": "📌 **បញ្ជីភារកិច្ចដែលបានប្រគល់ជូនលោកអ្នក៖**\n",
        "my_tasks_empty": "✨ លោកអ្នកមិនមានភារកិច្ចដែលត្រូវបានប្រគល់ជូនឡើយ។",
        "task_completed_group": "✅ **ភារកិច្ចត្រូវបានកត់សម្គាល់ថាបានបញ្ចប់ដោយ %s!**\n\n📅 **កាលបរិច្ឆេទបង្កើត៖** %s\n🎉 **កាលបរិច្ឆេទបញ្ចប់៖** %s",
        "prompt_member_tasks": "សូមបញ្ចូលពាក្យបញ្ជាដើម្បីពិនិត្យភារកិច្ចមន្ត្រី (សម្រាប់ប្រធាន)៖\n/membertasks @username\n\nឧទាហរណ៍៖ /membertasks @john",
        "member_tasks_header": "👥 **បញ្ជីភារកិច្ចដែលបានប្រគល់ជូនមន្ត្រី %s៖**\n",
        "member_tasks_empty": "✨ មិនមានភារកិច្ចដែលកំពុងរង់ចាំសម្រាប់មន្ត្រី %s នោះទេ។",
        
        # Reminders & Daily Briefing
        "daily_briefing_header": "🌅 **របាយការណ៍សង្ខេបជូនប្រធានប្រចាំព្រឹក - %s**\n\n📋 **ភារកិច្ចផ្ទាល់ខ្លួនដែលត្រូវអនុវត្តថ្ងៃនេះ៖**\n",
        "daily_briefing_empty": "✨ លោកអ្នកមិនមានភារកិច្ចផ្ទាល់ខ្លួនសម្រាប់ថ្ងៃនេះទេ។",
        "group_reminder_alert": "⏰ **ការរំលឹកកាលបរិច្ឆេទកំណត់ភារកិច្ចក្រុម៖**\n\n👤 **មន្ត្រីទទូលខុសត្រូវ៖** %s\n📌 **បរិយាយ (Task)៖** %s\n⏰ **កាលបរិច្ឆេទកំណត់៖** %s",
        "private_reminder_alert": "⏰ **ការរំលឹកភារកិច្ចផ្ទាល់ខ្លួន៖**\n\n📌 **បរិយាយ (Task)៖** %s\n⏰ **កាលបរិច្ឆេទកំណត់៖** %s",

        # Formal Invitation Message
        "invite_message": "លោក/លោកស្រី មន្ត្រី និងសមាជិកក្រុមទាំងអស់ ជាទីគោរព,\n\nដើម្បីបង្កើនប្រសិទ្ធភាពនៃការបែងចែក និងតាមដានភារកិច្ចការងារឲ្យមានភាពរហ័ស និងមានរបៀបរៀបរយ យើងខ្ញុំសូមណែនាំប្រព័ន្ធ Telegram Bot គ្រប់គ្រងភារកិច្ចការងារផ្លូវការ។\n\nសូមលោក/លោកស្រី ចុចលើតំណភ្ជាប់ខាងក្រោម ដើម្បីចាប់ផ្តើមប្រើប្រាស់ (Start Bot)៖\n👉 @TaskOSHBot (ឬ https://t.me/TaskOSHBot)\n\nបន្ទាប់ពីចុច /start លោក/លោកស្រីអាច៖\n  • ទទួល និងពិនិត្យមើលភារកិច្ចដែលបានប្រគល់ជូន\n  • កត់សម្គាល់ភារកិច្ចដែលបានបញ្ចប់រៀបរយ\n  • ទទួលបានការរំលឹកកាលបរិច្ឆេទកំណត់ (Deadline) ដោយស្វ័យប្រវត្តិ\n\nសូមអរគុណ!",

        # Buttons
        "btn_complete": "កត់សម្គាល់ថាបានបញ្ចប់",
        "btn_cancel": "❌ បោះបង់",
        "wizard_cancelled": "🚫 ប្រតិបត្តិការត្រូវបានបោះបង់។",
        "btn_lang_km": "ភាសាខ្មែរ (Khmer)",
        "btn_lang_en": "English",
        
        # Pinned Keyboard Buttons (Boss vs Staff)
        "btn_menu_add_task_boss": "➕ បន្ថែមភារកិច្ច (ខ្លួនឯង / មន្ត្រី)",
        "btn_menu_add_task_staff": "➕ បន្ថែមភារកិច្ចផ្ទាល់ខ្លួន",
        "btn_menu_complete_task": "✓ បញ្ចប់ភារកិច្ចដែលបានប្រគល់",
        "btn_menu_todos": "📋 បញ្ជីភារកិច្ចផ្ទាល់ខ្លួន",
        "btn_menu_mytasks": "📌 ភារកិច្ចដែលបានប្រគល់ជូនខ្ញុំ",
        "btn_menu_member_tasks": "👥 ពិនិត្យភារកិច្ចមន្ត្រី (ប្រធាន)",
        "btn_menu_report": "📊 របាយការណ៍ (ប្រធាន)",
        "btn_menu_report_staff": "📊 របាយការណ៍ (មន្ត្រី)",
        
        "btn_menu_assign_coworker": "➕ ប្រគល់ភារកិច្ចជូនមន្ត្រី",
        "btn_menu_complete_group": "✓ បញ្ចប់ភារកិច្ចក្រុម",
        "btn_menu_grouptasks": "📋 ភារកិច្ចក្រុមដែលកំពុងរង់ចាំ",
    },
    "en": {
        # Common / System
        "welcome_private": "Welcome to the Task Management System & Boss Assistant!",
        "welcome_group": "Group Task Delegation System initialized for this chat.\nPlease use /help to view available commands.",
        "help_text": (
            "Task Management System (Boss / Staff)\n\n"
            "Commands for Boss (ប្រធានការិយាល័យ):\n"
            "/todo add <description> [YYYY-MM-DD HH:MM] - Add personal task\n"
            "/assign @username <description> <YYYY-MM-DD HH:MM> - Delegate task to staff\n"
            "/membertasks @username - Inspect tasks assigned to staff\n"
            "/report - Download Executive Reports (Telegram / Excel)\n"
            "/todos - View pending personal & assigned tasks\n\n"
            "Commands for Staff (មន្ត្រី):\n"
            "/todo add <description> [YYYY-MM-DD HH:MM] - Add personal task\n"
            "/todos - View personal & assigned tasks\n"
            "/complete <task_id> - Mark task as completed\n"
            "/role - Switch role (Boss / Staff)\n"
            "/language - Switch language"
        ),
        "lang_selected": "System language updated to: English.",
        "select_language": "Please select system language:",
        "unauthorized_admin": "Access Denied: Command restricted to group administrators only.",
        "unauthorized_boss_only": "Access Denied: Task delegation and assignment inspection are restricted to Boss (ប្រធាន) only.",
        "invalid_syntax": "Invalid command syntax. Please refer to /help for correct format.",
        "error_occurred": "A system error occurred. The requested action could not be completed.",
        "bot_blocked_notice": "Member %s has not initiated a private chat with the bot. Direct notification could not be delivered.",

        # Role Selection
        "select_role": "Please select your role in the system:",
        "btn_role_boss": "👔 Boss (ប្រធានការិយាល័យ)",
        "btn_role_staff": "👤 Staff (មន្ត្រី)",
        "role_selected_boss": "Your role has been set to: Boss (ប្រធានការិយាល័យ).",
        "role_selected_staff": "Your role has been set to: Staff (មន្ត្រី).",
        
        # Interactive Wizard
        "wizard_select_type": "➕ Select task type to add:",
        "btn_type_personal": "👤 Personal To-Do",
        "btn_type_staff": "👥 Assign to Staff",
        "wizard_prompt_personal_title": "📝 Please send your personal task description:\n(Example: Prepare monthly report)",
        "wizard_prompt_staff_task": "👥 Please send staff username and task description in format:\n@username Task Description\n\nExample: @sokha Prepare report",
        "wizard_prompt_deadline": "⏰ Please enter date & time deadline for: '%s'\n\nFormat: YYYY-MM-DD HH:MM (e.g., 2026-08-20 17:00 or 20/08/2026)\n* Type 'none' for no deadline",
        "btn_dl_today_17": "⏱️ Today 17:00",
        "btn_dl_tomorrow_09": "📅 Tomorrow 09:00",
        "btn_dl_monday_09": "📆 Monday 09:00",
        "btn_dl_none": "🚫 No Deadline",

        # Executive Reports
        "prompt_report_type": "📊 Task Reporting System (Executive / Boss)\n\nPlease select report type:",
        "btn_rpt_personal": "📋 Boss Personal Tasks Report",
        "btn_rpt_staff": "👥 Staff Assignments Report",
        "prompt_report_fmt": "📥 Select report output format:",
        "btn_fmt_msg": "💬 Display in Telegram",
        "btn_fmt_excel": "📥 Download Excel File (.xlsx)",
        "report_personal_title": "📊 Executive Summary - Personal To-Do Tasks\n",
        "report_staff_title": "📊 Executive Summary - Staff Task Assignments\n",
        "report_stat_summary": "📈 Overall Statistics:\n• Total Tasks: %d\n• Completed: %d (%s%%)\n• Pending: %d\n\n",
        
        # Tasks - Private Scope
        "todo_added": "✅ **Personal task recorded successfully!**\n\n📌 **Task:** %s\n⏰ **Deadline:** %s",
        "todo_list_header": "📋 **Pending Personal Tasks:**\n",
        "todo_empty": "✨ No pending personal tasks found.",
        "todo_completed": "✅ **Personal task marked as completed!**\n\n📅 **Created:** %s\n🎉 **Completed:** %s",
        "todo_not_found": "⚠️ Requested task not found or already completed.",
        "all_tasks_empty": "✨ You currently have no pending personal or assigned tasks.",
        "prompt_add_options": "How would you like to add a task?\n\n1. For Yourself (Personal To-Do):\n/todo add <description> [HH:MM || DD-MM-YYYY]\n\n2. Delegate to Staff (Boss only):\n/assign @username <description> <HH:MM || DD-MM-YYYY>",
        "prompt_complete_help": "Please select an assigned task below to complete:",

        # Tasks - Group Scope & Boss Member Checking
        "task_assigned": "👥 **New Task Delegated to:** %s\n\n📌 **Task:** %s\n⏰ **Deadline:** %s\n👔 **Assigned By:** %s",
        "group_tasks_header": "📋 **Pending Group Tasks for this Chat:**\n",
        "group_tasks_empty": "✨ No pending group tasks in this chat.",
        "my_tasks_header": "📌 **Tasks Assigned to You:**\n",
        "my_tasks_empty": "✨ You currently have no assigned tasks.",
        "task_completed_group": "✅ **Task marked as completed by %s!**\n\n📅 **Created:** %s\n🎉 **Completed:** %s",
        "prompt_member_tasks": "Please specify staff username to inspect:\n/membertasks @username",
        "member_tasks_header": "👥 **Pending tasks assigned to staff %s:**\n",
        "member_tasks_empty": "✨ No pending tasks found for staff %s.",

        # Reminders & Daily Briefing
        "daily_briefing_header": "🌅 **Daily Executive Briefing - %s**\n\n📋 **Pending Personal Tasks:**\n",
        "daily_briefing_empty": "✨ You have no personal tasks scheduled for today.",
        "group_reminder_alert": "⏰ **Group Task Deadline Warning:**\n\n👤 **Staff:** %s\n📌 **Task:** %s\n⏰ **Deadline:** %s",
        "private_reminder_alert": "⏰ **Personal Task Reminder:**\n\n📌 **Task:** %s\n⏰ **Deadline:** %s",

        # Formal Invitation Message
        "invite_message": "Dear Team Members & Officers,\n\nTo streamline task assignment, delegation, and daily task tracking across our department, we are introducing our official Telegram Task Assistant Bot.\n\nPlease click the link below to initialize and activate your account:\n👉 @TaskOSHBot (or https://t.me/TaskOSHBot)\n\nOnce activated, you can:\n  • View all tasks assigned to you by management\n  • Mark tasks as completed with a single tap\n  • Receive automatic deadline reminders and progress summaries\n\nThank you for your cooperation!",

        # Buttons
        "btn_complete": "Mark as Completed",
        "btn_cancel": "❌ Cancel",
        "wizard_cancelled": "🚫 Operation cancelled.",
        "btn_lang_km": "ភាសាខ្មែរ (Khmer)",
        "btn_lang_en": "English",
        
        # Pinned Keyboard Buttons
        "btn_menu_add_task_boss": "➕ Add To-Do (Self / Staff)",
        "btn_menu_add_task_staff": "➕ Add Personal To-Do",
        "btn_menu_complete_task": "✓ Complete Assigned Task",
        "btn_menu_todos": "📋 Personal To-Dos",
        "btn_menu_mytasks": "📌 Tasks Assigned to Me",
        "btn_menu_member_tasks": "👥 Check Staff Tasks (Boss)",
        "btn_menu_report": "📊 Task Report (Boss)",
        "btn_menu_report_staff": "📊 Task Report (Staff)",
        
        "btn_menu_assign_coworker": "➕ Assign Task to Staff",
        "btn_menu_complete_group": "✓ Complete Group Task",
        "btn_menu_grouptasks": "📋 Active Group Tasks",
    }
}


def t(key: str, lang: str = "km", *args: Any) -> str:
    """
    Retrieve localized string formatted with positional arguments if provided.
    Defaults to Khmer ('km') if specified language key is missing.
    """
    target_lang = lang if lang in TRANSLATIONS else "km"
    template = TRANSLATIONS[target_lang].get(key) or TRANSLATIONS["km"].get(key, key)
    if args:
        try:
            return template % args
        except (TypeError, ValueError):
            return template
    return template
