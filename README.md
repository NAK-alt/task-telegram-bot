# Production Telegram Executive Assistant & Group Task Delegator Bot

A production-ready Telegram Bot built with Python (`python-telegram-bot` v20+), Firebase Firestore, and APScheduler / JobQueue. Designed specifically for executives and team managers to manage personal To-Dos with strict scope isolation while delegating group tasks to team members.

---

## Key Features

1. **Private Chat Scope (Boss Persona)**
   - **Personal To-Do & Reminders**: Add, view, complete, and schedule alerts for meetings and deadlines.
   - **Strict Isolation**: Personal tasks carry `scope: "private"` in database and are visible strictly to the creator.
   - **Daily Briefing**: Automated morning summary sent to private chat at a scheduled time (`08:00` by default).

2. **Group Chat Scope (Team Delegation)**
   - **Task Delegation**: `/assign @username <task description> <YYYY-MM-DD HH:MM>`
   - **Targeted Mentions & Alerts**: `@username` is mentioned upon task assignment and prior to deadline expiry.
   - **Group Task List**: `/grouptasks` displays all pending group assignments.
   - **Member Private View**: `/mytasks` in private chat allows team members to view all tasks assigned to them across all groups without leaking other members' private data.

3. **Bilingual Localization & Executive Persona**
   - **Strict Formal Tone**: Professional, direct, executive assistant tone.
   - **Languages**: Default is Khmer (`km`), with English (`en`) support toggleable via `/language`.

---

## Project Structure

```
.
├── bot.py                  # Application entrypoint & handler registration
├── config.py               # Environment configuration & settings
├── database.py             # Firebase Firestore operations & scope filtering
├── i18n.py                 # Khmer & English translations (Executive tone)
├── scheduler.py            # APScheduler / JobQueue for alerts & daily briefing
├── handlers/
│   ├── __init__.py
│   ├── common.py           # /start, /help, /language, error handling
│   ├── private.py          # /todo, /todos, /mytasks, private done handlers
│   └── group.py            # /assign, /grouptasks, /complete, admin checks
├── requirements.txt        # Python package dependencies
├── Dockerfile              # Docker container setup
├── docker-compose.yml      # Isolated co-hosting orchestration
├── .env.example            # Environment variable template
└── firebase_credentials.json.example # Firebase Admin SDK template
```

---

## Firebase Firestore Database Schema

### Collection `users`
```json
{
  "user_id": 123456789,
  "username": "executive_boss",
  "first_name": "Executive",
  "language": "km",
  "timezone": "Asia/Phnom_Penh",
  "last_updated": "2026-08-08T09:40:00Z"
}
```

### Collection `groups`
```json
{
  "group_id": -1001234567890,
  "language": "km"
}
```

### Collection `tasks`
```json
{
  "task_id": "a1b2c3d4",
  "scope": "private", // "private" or "group"
  "title": "Review Q3 Budget Proposal",
  "user_id": 123456789,
  "group_id": null, // Group ID if scope is group
  "assigned_to_id": null,
  "assigned_to_username": "team_lead",
  "assigned_by_id": 123456789,
  "assigned_by_username": "executive_boss",
  "status": "pending", // "pending" or "completed"
  "deadline": "2026-08-10T14:00:00Z",
  "created_at": "2026-08-08T09:40:00Z",
  "reminded": false
}
```

---

## Setup & Deployment Guide

### Option 1: Docker Container Co-Hosting (Recommended)

When running alongside an existing Telegram bot on the same server, Docker containers isolate process environments, python packages, and network threads cleanly so neither bot interferes with the other.

1. **Clone repository and enter directory**:
   ```bash
   cd Assignment&ToDoList
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your unique Telegram `BOT_TOKEN`:
   ```ini
   BOT_TOKEN=7890123456:AA...YOUR_TOKEN...
   DEFAULT_LANGUAGE=km
   DEFAULT_TIMEZONE=Asia/Phnom_Penh
   DAILY_BRIEFING_TIME=08:00
   FIREBASE_SERVICE_ACCOUNT_PATH=firebase_credentials.json
   ```

3. **Add Firebase Credentials**:
   Obtain service account JSON key file from Firebase Console (`Project Settings > Service Accounts > Generate New Private Key`) and save as `firebase_credentials.json` in the root directory.

4. **Build and Launch Container**:
   ```bash
   docker-compose up -d --build
   ```

5. **Verify Running Logs**:
   ```bash
   docker-compose logs -f
   ```

---

### Option 2: Systemd Service Co-Hosting

If co-hosting on a Linux system (Ubuntu/Debian) using Python Virtual Environments and Systemd:

1. **Setup Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create Systemd Service File** `/etc/systemd/system/executive-task-bot.service`:
   ```ini
   [Unit]
   Description=Executive Assistant & Group Task Delegator Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/var/www/executive-task-bot
   ExecStart=/var/www/executive-task-bot/venv/bin/python bot.py
   Restart=always
   RestartSec=10
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable & Start Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable executive-task-bot
   sudo systemctl start executive-task-bot
   sudo systemctl status executive-task-bot
   ```

---

## Co-Hosting Safety Rules

To ensure this bot runs seamlessly alongside existing bots on your server:

1. **Unique Bot Tokens**: Never share Telegram Bot tokens between bot processes.
2. **Polling vs Webhook Isolation**:
   - If this bot uses Long Polling (`run_polling`), ensure no other process uses the same `BOT_TOKEN` for webhook.
   - If using Webhooks in the future, allocate a distinct port (e.g., Bot 1 on port 8080, Bot 2 on port 8081) and reverse proxy via Nginx.
3. **Database Isolation**: Keep Firestore collections or Firebase projects isolated per bot application.
4. **Log & PID Isolation**: Ensure each bot writes logs to its own directory or stdout inside Docker containers.

---

## Command Reference

| Scope | Command | Description | Syntax / Example |
|---|---|---|---|
| Both | `/start` | Initialize interaction | `/start` |
| Both | `/help` | View system documentation | `/help` |
| Both | `/language` | Change language (Khmer / English) | `/language` |
| Private | `/todo add` | Add personal task | `/todo add Review strategy document 2026-08-10 14:00` |
| Private | `/todos` | View pending personal tasks | `/todos` |
| Private | `/mytasks` | View tasks assigned to you across groups | `/mytasks` |
| Group | `/assign` | Assign group task with mention | `/assign @john Review project milestone 2026-08-12 17:00` |
| Group | `/grouptasks` | View pending tasks for current group | `/grouptasks` |
| Both | `/complete` | Mark task completed | `/complete a1b2c3d4` |
