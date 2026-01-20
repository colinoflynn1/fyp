"""Notification persistence and retrieval helpers."""

from __future__ import annotations

from contextlib import suppress
from datetime import date, timedelta
from typing import Dict, List, Optional

from db import get_conn
from goals import list_goals, build_progress


# Reference: Python docs on MySQL CREATE TABLE + contextlib [NEW]
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


# Reference: CRUD pattern from user.py + goals.py [NEW]
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


# Reference: MySQL Documentation - SELECT with WHERE clauses [NEW]
# https://dev.mysql.com/doc/refman/8.0/en/select.html
# CRUD pattern adapted from user.py and goals.py
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


# Reference: MySQL Documentation - UPDATE statement [NEW]
# https://dev.mysql.com/doc/refman/8.0/en/update.html
# CRUD update pattern adapted from user.py and goals.py
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


# Reference: MySQL Documentation - UPDATE with WHERE clause [NEW]
# https://dev.mysql.com/doc/refman/8.0/en/update.html
# Bulk update pattern for user notifications
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


# Reference: Python datetime documentation - Date arithmetic [NEW]
# https://docs.python.org/3/library/datetime.html#datetime.date
# Based on goals.py build_progress logic for due date calculations
# Notification creation pattern adapted from standard notification systems
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
            # Notify if due today or in the next 3 days
            if days_until_due <= 3 and days_until_due >= 0:
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
                else:
                    title = f"Payment Due Soon: {goal['goal_name']}"
                    message = (
                        f"Your {goal['goal_name']} goal has a payment due in {days_until_due} days. "
                        f"Recommended amount: €{progress['recommended_contribution']:.2f}"
                    )
                
                # Check if notification already exists (avoid duplicates)
                existing = list_notifications(user_id, limit=100)
                if not any(
                    n.get("goal_id") == goal["id"] 
                    and n.get("notification_type") == "payment_due"
                    and n.get("is_read") == False
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


# Reference: Python documentation - Percentage calculations [NEW]
# https://docs.python.org/3/library/functions.html#round
# Based on goals.py build_progress milestone detection logic
# Milestone threshold checking adapted from standard progress tracking patterns
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
    
    milestones = [25, 50, 75, 100]
    
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
