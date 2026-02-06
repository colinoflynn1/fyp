"""Notification persistence and retrieval helpers."""

from __future__ import annotations

from contextlib import suppress
from datetime import date, timedelta
from typing import Dict, List, Optional

from db import get_conn
from goals import list_goals, build_progress


# Reference: Based on ensure_goal_tables() in goals.py (line 34)
# Python docs on MySQL CREATE TABLE: https://dev.mysql.com/doc/refman/8.0/en/create-table.html
# contextlib.suppress: https://docs.python.org/3/library/contextlib.html#contextlib.suppress
# Ensures the notifications table exists before the app continues
def ensure_notification_tables() -> None:
    """Create notifications table if it doesn't exist."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_notifications (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id INT UNSIGNED NOT NULL,
                notification_type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                goal_id INT UNSIGNED NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_notification_user FOREIGN KEY (user_id)
                  REFERENCES users(id) ON DELETE CASCADE,
                CONSTRAINT fk_notification_goal FOREIGN KEY (goal_id)
                  REFERENCES savings_goals(id) ON DELETE CASCADE,
                INDEX idx_user_read (user_id, is_read),
                INDEX idx_user_created (user_id, created_at DESC)
            )
            """
        )
        # Add goal_id column for legacy tables if needed
        with suppress(Exception):
            cur.execute(
                """
                ALTER TABLE user_notifications
                ADD COLUMN goal_id INT UNSIGNED NULL
                """
            )
            cur.execute(
                """
                ALTER TABLE user_notifications
                ADD CONSTRAINT fk_notification_goal 
                FOREIGN KEY (goal_id) REFERENCES savings_goals(id) ON DELETE CASCADE
                """
            )


# Call on import to ensure table exists
ensure_notification_tables()


# Reference: Based on create_user() in user.py (line 124) and create_goal() in goals.py (line 94)
# MySQL INSERT: https://dev.mysql.com/doc/refman/8.0/en/insert.html
# Creates a dashboard notification for a user
def create_notification(
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    goal_id: Optional[int] = None,
) -> int:
    """
    Create a dashboard notification.
    
    Args:
        user_id: The user who should receive the notification
        notification_type: Type of notification (e.g., 'payment_due', 'milestone', 'goal_created')
        title: Short title for the notification
        message: Full message text
        goal_id: Optional goal ID if notification is goal-related
    
    Returns:
        The ID of the created notification
    """
    sql = """
        INSERT INTO user_notifications (user_id, notification_type, title, message, goal_id)
        VALUES (%s, %s, %s, %s, %s)
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (user_id, notification_type, title, message, goal_id))
        return cur.lastrowid


# Reference: Based on list_users() in user.py (line 97) and list_goals() in goals.py (line 136)
# MySQL SELECT with WHERE: https://dev.mysql.com/doc/refman/8.0/en/select.html
# Lists unread notifications for a user
def list_notifications(user_id: int, limit: int = 50, unread_only: bool = False) -> List[Dict]:
    """
    Get notifications for a user.
    
    Args:
        user_id: The user's ID
        limit: Maximum number of notifications to return
        unread_only: If True, only return unread notifications
    
    Returns:
        List of notification dictionaries
    """
    if unread_only:
        sql = """
            SELECT id, notification_type, title, message, goal_id, is_read, created_at
            FROM user_notifications
            WHERE user_id=%s AND is_read=FALSE
            ORDER BY created_at DESC
            LIMIT %s
        """
    else:
        sql = """
            SELECT id, notification_type, title, message, goal_id, is_read, created_at
            FROM user_notifications
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT %s
        """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (user_id, limit))
        return cur.fetchall()


# Reference: Based on update_user() in user.py (line 47) and update_goal() in goals.py (line 165)
# MySQL UPDATE: https://dev.mysql.com/doc/refman/8.0/en/update.html
# Marks a notification as read
def mark_notification_read(notification_id: int, user_id: int) -> bool:
    """Mark a notification as read."""
    sql = """
        UPDATE user_notifications
        SET is_read=TRUE
        WHERE id=%s AND user_id=%s
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (notification_id, user_id))
        return cur.rowcount > 0


# Reference: Based on update_user() pattern in user.py (line 47)
# MySQL UPDATE with WHERE: https://dev.mysql.com/doc/refman/8.0/en/update.html
# Marks all notifications for a user as read
def mark_all_read(user_id: int) -> int:
    """Mark all notifications for a user as read. Returns count of updated rows."""
    sql = """
        UPDATE user_notifications
        SET is_read=TRUE
        WHERE user_id=%s AND is_read=FALSE
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (user_id,))
        return cur.rowcount


# Reference: Based on build_progress() in goals.py (line 295) for date calculations
# Python datetime.date: https://docs.python.org/3/library/datetime.html#datetime.date
# Uses list_goals() from goals.py (line 136) and build_progress() for due date logic
# Checks for upcoming payment due dates and creates notifications
def check_payment_due_notifications(user_id: int) -> List[int]:
    """
    Check for goals with upcoming or due payments and create notifications.
    
    Returns:
        List of created notification IDs
    """
    created_ids = []
    goals = list_goals(user_id)
    today = date.today()
    
    for goal in goals:
        progress = build_progress(goal)
        next_due_date = progress.get("next_due_date")
        
        if next_due_date:
            days_until_due = (next_due_date - today).days
            # Notify at 7 days, 2 days, 1 day (tomorrow), and today
            if days_until_due in [7, 2, 1, 0]:
                if days_until_due == 0:
                    title = f"Payment Due Today: {goal['goal_name']}"
                    message = (
                        f"Your {goal['goal_name']} goal has a payment due today. "
                        f"Recommended amount: €{progress['recommended_contribution']:.2f}"
                    )
                elif days_until_due == 1:
                    title = f"Payment Due Tomorrow: {goal['goal_name']}"
                    message = (
                        f"Your {goal['goal_name']} goal has a payment due tomorrow. "
                        f"Recommended amount: €{progress['recommended_contribution']:.2f}"
                    )
                elif days_until_due == 2:
                    title = f"Payment Due in 2 Days: {goal['goal_name']}"
                    message = (
                        f"Your {goal['goal_name']} goal has a payment due in 2 days. "
                        f"Recommended amount: €{progress['recommended_contribution']:.2f}"
                    )
                else:  # days_until_due == 7
                    title = f"Payment Due in 7 Days: {goal['goal_name']}"
                    message = (
                        f"Your {goal['goal_name']} goal has a payment due in 7 days. "
                        f"Recommended amount: €{progress['recommended_contribution']:.2f}"
                    )
                
                # Check if notification already exists for this specific day (avoid duplicates)
                # Check ALL notifications (read and unread) to prevent recreating after marking as read
                existing = list_notifications(user_id, limit=100, unread_only=False)
                if not any(
                    n.get("goal_id") == goal["id"] 
                    and n.get("notification_type") == "payment_due"
                    and f"{days_until_due} day" in n.get("message", "").lower()
                    for n in existing
                ):
                    notif_id = create_notification(
                        user_id,
                        "payment_due",
                        title,
                        message,
                        goal_id=goal["id"],
                    )
                    created_ids.append(notif_id)
    
    return created_ids


# Reference: Based on build_progress() in goals.py (line 295) for percentage calculations
# Python percentage calculations: https://docs.python.org/3/library/functions.html#round
# Uses list_goals() from goals.py (line 136) and build_progress() for milestone detection
# Checks for milestone achievements and creates notifications
def check_milestone_notifications(user_id: int, goal_id: Optional[int] = None) -> List[int]:
    """
    Check for goal milestones (25%, 50%, 75%, 100%) and create notifications.
    
    Args:
        user_id: The user's ID
        goal_id: Optional specific goal to check. If None, checks all goals.
    
    Returns:
        List of created notification IDs
    """
    created_ids = []
    goals = list_goals(user_id)
    
    if goal_id:
        goals = [g for g in goals if g["id"] == goal_id]
    
    # Reference: 100% excluded - handled by goal completion flow (app.py goal_deposit/goal_auto_contribute)
    milestones = [25, 50, 75]
    for goal in goals:
        progress = build_progress(goal)
        percent = progress.get("percent_complete", 0)
        
        # Check which milestone was just reached
        for milestone in milestones:
            # Check if we've crossed this milestone threshold (at or just past)
            # We check >= milestone to ensure we've reached it, but not way past
            if percent >= milestone and percent < milestone + 1:
                title = f"🎉 Milestone Reached: {goal['goal_name']}"
                message = (
                    f"Congratulations! You've reached {milestone}% of your "
                    f"{goal['goal_name']} goal. Keep up the great work!"
                )
                
                # Check if this milestone notification already exists
                existing = list_notifications(user_id, limit=100)
                milestone_key = f"{milestone}%"
                if not any(
                    n.get("goal_id") == goal["id"]
                    and n.get("notification_type") == "milestone"
                    and milestone_key in n.get("message", "")
                    for n in existing
                ):
                    notif_id = create_notification(
                        user_id,
                        "milestone",
                        title,
                        message,
                        goal_id=goal["id"],
                    )
                    created_ids.append(notif_id)
                    break  # Only create one notification per check
    
    return created_ids
