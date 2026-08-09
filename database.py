"""
Database Layer - Firebase Firestore Integration.
Handles database operations for Users, Groups, and Tasks with strict scope separation.
"""

import os
import uuid
import datetime
import pytz
from typing import Dict, Any, List, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from config import FIREBASE_SERVICE_ACCOUNT_PATH, DEFAULT_LANGUAGE, DEFAULT_TIMEZONE

_db: Optional[firestore.Client] = None


def init_db() -> firestore.Client:
    """Initialize Firebase Admin SDK and return Firestore client."""
    global _db
    if _db is not None:
        return _db

    if not firebase_admin._apps:
        json_env = os.environ.get("FIREBASE_CREDENTIALS_JSON")
        if json_env:
            # Clean string and strip UTF-8 BOM (\ufeff) if present from Windows/PowerShell pipes
            json_env = json_env.strip("\ufeff\r\n ")
            try:
                import json
                dict_cred = json.loads(json_env)
                cred = credentials.Certificate(dict_cred)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                try:
                    import base64, json
                    decoded = base64.b64decode(json_env).decode("utf-8-sig")
                    dict_cred = json.loads(decoded)
                    cred = credentials.Certificate(dict_cred)
                    firebase_admin.initialize_app(cred)
                except Exception as inner_e:
                    raise ValueError(f"Failed to parse FIREBASE_CREDENTIALS_JSON: {e} | {inner_e}")
        else:
            target_path = FIREBASE_SERVICE_ACCOUNT_PATH
            if not os.path.exists(target_path) and os.path.exists(f"{FIREBASE_SERVICE_ACCOUNT_PATH}.json"):
                target_path = f"{FIREBASE_SERVICE_ACCOUNT_PATH}.json"

            if os.path.exists(target_path):
                cred = credentials.Certificate(target_path)
                firebase_admin.initialize_app(cred)
            elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                firebase_admin.initialize_app()
            else:
                raise FileNotFoundError(
                    f"\n\n============================================================\n"
                    f"[FIREBASE ERROR] Credentials file '{FIREBASE_SERVICE_ACCOUNT_PATH}' or env var 'FIREBASE_CREDENTIALS_JSON' not found!\n"
                    f"============================================================\n"
                )

    try:
        _db = firestore.client()
        return _db
    except Exception as e:
        raise RuntimeError(
            f"\n\n============================================================\n"
            f"[FIREBASE ERROR] Failed to connect to Firestore: {e}\n"
            f"Please ensure Firestore Database is activated in Firebase Console.\n"
            f"============================================================\n"
        ) from e


def get_db() -> firestore.Client:
    if _db is None:
        return init_db()
    return _db


# ------------------------------------------------------------------
# User & Group Preference Operations
# ------------------------------------------------------------------

def register_or_update_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> Dict[str, Any]:
    """Ensure user profile exists in Firestore and update metadata."""
    db = get_db()
    user_ref = db.collection("users").document(str(user_id))
    doc = user_ref.get()

    user_data = {
        "user_id": user_id,
        "username": username.lower() if username else "",
        "first_name": first_name or "",
        "last_updated": datetime.datetime.now(pytz.utc)
    }

    if doc.exists:
        existing = doc.to_dict()
        user_ref.update(user_data)
        existing.update(user_data)
        return existing
    else:
        user_data["language"] = DEFAULT_LANGUAGE
        user_data["timezone"] = DEFAULT_TIMEZONE
        user_ref.set(user_data)
        return user_data


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Lookup registered user profile in Firestore by Telegram @username."""
    if not username:
        return None
    clean_username = username.lstrip("@").lower().strip()
    db = get_db()
    docs = db.collection("users").where("username", "==", clean_username).limit(1).stream()
    for doc in docs:
        return doc.to_dict()
    return None


def get_user_role(user_id: int) -> Optional[str]:
    """Retrieve user role: 'boss' (ប្រធានការិយាល័យ) or 'staff' (មន្ត្រី)."""
    db = get_db()
    doc = db.collection("users").document(str(user_id)).get()
    if doc.exists:
        return doc.to_dict().get("role")
    return None


def set_user_role(user_id: int, role: str) -> None:
    """Set user role: 'boss' or 'staff'."""
    db = get_db()
    db.collection("users").document(str(user_id)).set({"role": role}, merge=True)


ADMIN_USER_ID = 1079885088


def is_boss(user_id: int) -> bool:
    """Check if user has boss (ប្រធាន) role."""
    role = get_user_role(user_id)
    return role == "boss"


def is_admin_or_boss(user_id: int) -> bool:
    """Check if user is Telegram ID 1079885088 or has Boss (ប្រធាន) role."""
    return user_id == ADMIN_USER_ID or is_boss(user_id)


def delete_task(task_id: str, requesting_user_id: int) -> bool:
    """
    Permanently delete a task from Firestore.
    Allowed ONLY for Boss (ប្រធាន) or Telegram Admin ID 1079885088.
    Removes task completely from all task lists and reports for both Boss and Officers.
    """
    if not is_admin_or_boss(requesting_user_id):
        return False
    db = get_db()
    doc_ref = db.collection("tasks").document(task_id)
    doc = doc_ref.get()
    if not doc.exists:
        return False
    doc_ref.delete()
    return True


def delete_all_tasks(requesting_user_id: int) -> int:
    """
    Permanently delete ALL tasks from Firestore database.
    Restricted strictly to Telegram Admin ID 1079885088.
    Returns count of deleted task documents.
    """
    if requesting_user_id != ADMIN_USER_ID:
        return 0
    db = get_db()
    docs = db.collection("tasks").stream()
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    return count


def get_all_system_tasks() -> List[Dict[str, Any]]:
    """Get every single task in the database (for Admin master management)."""
    db = get_db()
    docs = db.collection("tasks").stream()
    return [doc.to_dict() for doc in docs]


def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a task document by ID."""
    db = get_db()
    doc = db.collection("tasks").document(task_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def update_task_title(task_id: str, new_title: str, requesting_user_id: int) -> bool:
    """Update task title. Restricted to Boss or Admin."""
    if not is_admin_or_boss(requesting_user_id):
        return False
    db = get_db()
    doc_ref = db.collection("tasks").document(task_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.update({"title": new_title})
    return True


def update_task_deadline(task_id: str, new_deadline: Optional[datetime.datetime], requesting_user_id: int) -> bool:
    """Update task deadline. Restricted to Boss or Admin."""
    if not is_admin_or_boss(requesting_user_id):
        return False
    db = get_db()
    doc_ref = db.collection("tasks").document(task_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.update({"deadline": new_deadline, "reminded": False})
    return True


def get_user_language(user_id: int) -> str:
    """Retrieve user preferred language."""
    db = get_db()
    doc = db.collection("users").document(str(user_id)).get()
    if doc.exists:
        return doc.to_dict().get("language", DEFAULT_LANGUAGE)
    return DEFAULT_LANGUAGE


def set_user_language(user_id: int, lang: str) -> None:
    """Set language preference for user."""
    db = get_db()
    db.collection("users").document(str(user_id)).set({"language": lang}, merge=True)


def get_chat_language(chat_id: int) -> str:
    """Retrieve chat (group or private) language preference."""
    db = get_db()
    if chat_id > 0:
        return get_user_language(chat_id)
    doc = db.collection("groups").document(str(chat_id)).get()
    if doc.exists:
        return doc.to_dict().get("language", DEFAULT_LANGUAGE)
    return DEFAULT_LANGUAGE


def set_group_language(group_id: int, lang: str) -> None:
    """Set language preference for a group chat."""
    db = get_db()
    db.collection("groups").document(str(group_id)).set({"language": lang, "group_id": group_id}, merge=True)


# ------------------------------------------------------------------
# Task Operations (Private & Group Scopes)
# ------------------------------------------------------------------

def create_task(
    scope: str,
    title: str,
    user_id: int,
    group_id: Optional[int] = None,
    assigned_to_id: Optional[int] = None,
    assigned_to_username: Optional[str] = None,
    assigned_by_id: Optional[int] = None,
    assigned_by_username: Optional[str] = None,
    deadline: Optional[datetime.datetime] = None
) -> Dict[str, Any]:
    """Create a new task with strict scope flag ('private' or 'group')."""
    db = get_db()
    short_id = str(uuid.uuid4())[:8]

    task_doc = {
        "task_id": short_id,
        "scope": scope,  # 'private' or 'group'
        "title": title,
        "user_id": user_id,  # Owner / Creator ID
        "group_id": group_id,  # None for private
        "assigned_to_id": assigned_to_id,
        "assigned_to_username": assigned_to_username.lower().lstrip("@") if assigned_to_username else "",
        "assigned_by_id": assigned_by_id or user_id,
        "assigned_by_username": assigned_by_username or "",
        "status": "pending",
        "deadline": deadline,
        "created_at": datetime.datetime.now(pytz.utc),
        "reminded": False
    }

    db.collection("tasks").document(short_id).set(task_doc)
    return task_doc


def get_private_tasks(user_id: int) -> List[Dict[str, Any]]:
    """Get all pending private to-dos for a specific user."""
    db = get_db()
    query = (
        db.collection("tasks")
        .where(filter=FieldFilter("scope", "==", "private"))
        .where(filter=FieldFilter("user_id", "==", user_id))
        .where(filter=FieldFilter("status", "==", "pending"))
    )
    docs = query.stream()
    return [doc.to_dict() for doc in docs]


def get_all_personal_tasks(user_id: int) -> List[Dict[str, Any]]:
    """Get all private to-dos (both pending and completed) for a user."""
    db = get_db()
    query = (
        db.collection("tasks")
        .where(filter=FieldFilter("scope", "==", "private"))
        .where(filter=FieldFilter("user_id", "==", user_id))
    )
    return [doc.to_dict() for doc in query.stream()]


def get_all_assigned_by_boss(boss_id: int) -> List[Dict[str, Any]]:
    """Get all group tasks assigned by a boss (both pending and completed)."""
    db = get_db()
    query = (
        db.collection("tasks")
        .where(filter=FieldFilter("scope", "==", "group"))
        .where(filter=FieldFilter("assigned_by_id", "==", boss_id))
    )
    return [doc.to_dict() for doc in query.stream()]


def get_all_tasks_for_staff(user_id: int, username: str = "") -> List[Dict[str, Any]]:
    """
    Get all tasks (both private to-dos and assigned group tasks, pending and completed) for a staff member.
    """
    db = get_db()
    results = []

    # 1. Private to-dos
    q_priv = (
        db.collection("tasks")
        .where(filter=FieldFilter("scope", "==", "private"))
        .where(filter=FieldFilter("user_id", "==", user_id))
    )
    results.extend([doc.to_dict() for doc in q_priv.stream()])

    # 2. Assigned group tasks
    clean_username = username.lower().lstrip("@")
    if clean_username:
        q_user = (
            db.collection("tasks")
            .where(filter=FieldFilter("scope", "==", "group"))
            .where(filter=FieldFilter("assigned_to_username", "==", clean_username))
        )
        for doc in q_user.stream():
            d = doc.to_dict()
            if d not in results:
                results.append(d)

    q_id = (
        db.collection("tasks")
        .where(filter=FieldFilter("scope", "==", "group"))
        .where(filter=FieldFilter("assigned_to_id", "==", user_id))
    )
    for doc in q_id.stream():
        d = doc.to_dict()
        if d not in results:
            results.append(d)

    return results


def get_group_tasks(group_id: int) -> List[Dict[str, Any]]:
    """Get pending tasks assigned within a specific group."""
    db = get_db()
    query = (
        db.collection("tasks")
        .where(filter=FieldFilter("scope", "==", "group"))
        .where(filter=FieldFilter("group_id", "==", group_id))
        .where(filter=FieldFilter("status", "==", "pending"))
    )
    docs = query.stream()
    return [doc.to_dict() for doc in docs]


def get_tasks_assigned_to_user(username: str, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get all group tasks assigned to a specific user across all groups.
    Excludes private tasks of other users to maintain data isolation.
    """
    db = get_db()
    clean_username = username.lower().lstrip("@")
    
    tasks = []
    # Query by username match
    if clean_username:
        q_user = (
            db.collection("tasks")
            .where(filter=FieldFilter("scope", "==", "group"))
            .where(filter=FieldFilter("assigned_to_username", "==", clean_username))
            .where(filter=FieldFilter("status", "==", "pending"))
        )
        tasks.extend([doc.to_dict() for doc in q_user.stream()])

    # Query by user ID match if provided
    if user_id:
        q_id = (
            db.collection("tasks")
            .where(filter=FieldFilter("scope", "==", "group"))
            .where(filter=FieldFilter("assigned_to_id", "==", user_id))
            .where(filter=FieldFilter("status", "==", "pending"))
        )
        for doc in q_id.stream():
            d = doc.to_dict()
            if d not in tasks:
                tasks.append(d)

    return tasks


def complete_task(task_id: str, requesting_user_id: int, is_admin: bool = False) -> Optional[Dict[str, Any]]:
    """
    Mark task as completed. Checks ownership/permissions before updating.
    """
    db = get_db()
    doc_ref = db.collection("tasks").document(task_id)
    doc = doc_ref.get()

    if not doc.exists:
        return None

    data = doc.to_dict()
    if data.get("status") == "completed":
        return None

    # Verification: Private task must belong to user; Group task can be completed by assignee, assigner, or admin.
    if data.get("scope") == "private":
        if data.get("user_id") != requesting_user_id:
            return None
    else:
        # Group task permission
        is_assignee = (data.get("assigned_to_id") == requesting_user_id)
        is_assigner = (data.get("assigned_by_id") == requesting_user_id)
        if not (is_assignee or is_assigner or is_admin):
            return None

    completed_at = datetime.datetime.now(pytz.utc)
    doc_ref.update({
        "status": "completed",
        "completed_at": completed_at,
        "completed_by_id": requesting_user_id
    })
    data["status"] = "completed"
    data["completed_at"] = completed_at
    return data


def get_upcoming_reminders() -> List[Dict[str, Any]]:
    """Fetch tasks with pending deadlines that require alert dispatch."""
    db = get_db()
    now = datetime.datetime.now(pytz.utc)

    query = (
        db.collection("tasks")
        .where(filter=FieldFilter("status", "==", "pending"))
        .where(filter=FieldFilter("reminded", "==", False))
    )
    
    due_tasks = []
    for doc in query.stream():
        data = doc.to_dict()
        deadline = data.get("deadline")
        if deadline:
            # Handle firestore timestamp conversion if necessary
            if hasattr(deadline, "to_datetime"):
                deadline = deadline.to_datetime()
            if deadline.tzinfo is None:
                deadline = pytz.utc.localize(deadline)
            
            # Trigger reminder if deadline is within next 60 minutes or overdue
            if deadline <= (now + datetime.timedelta(minutes=60)):
                due_tasks.append(data)
    return due_tasks


def mark_task_reminded(task_id: str) -> None:
    """Flag task as reminded to avoid duplicate alerts."""
    db = get_db()
    db.collection("tasks").document(task_id).update({"reminded": True})


def get_all_registered_users() -> List[Dict[str, Any]]:
    """Retrieve all users registered in the database for daily briefings."""
    db = get_db()
    docs = db.collection("users").stream()
    return [doc.to_dict() for doc in docs]
