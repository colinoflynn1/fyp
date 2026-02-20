"""Savings goal persistence helpers."""

from __future__ import annotations

from contextlib import suppress
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

from db import get_conn


# Reference: Python docs
# Enumerations for user-selectable contribution cadence and the
# approximate number of days used for workload calculations.
FREQUENCIES = ("weekly", "bi-weekly", "monthly")
PERIOD_DAY_MAP = {
    "weekly": 7,
    "bi-weekly": 14,
    "monthly": 30,
}


# Reference: Python docs on Decimal quantize (https://docs.python.org/3/library/decimal.html)
# Helper that ensures every currency input/output is rounded to cents.
def _to_decimal(value: Decimal | float | int) -> Decimal:
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Reference: Official MySQL doc
# Ensures the savings tables exist before the app continues and are updated
def ensure_goal_tables() -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                user_id INT UNSIGNED NOT NULL,
                goal_name VARCHAR(120) NOT NULL,
                target_amount DECIMAL(12,2) NOT NULL,
                target_date DATE NOT NULL,
                frequency ENUM('weekly','bi-weekly','monthly') NOT NULL,
                saved_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
                next_due_date DATE NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_goal_user FOREIGN KEY (user_id)
                  REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS savings_goal_deposits (
                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                goal_id INT UNSIGNED NOT NULL,
                amount DECIMAL(12,2) NOT NULL,
                note VARCHAR(255) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_deposit_goal FOREIGN KEY (goal_id)
                  REFERENCES savings_goals(id) ON DELETE CASCADE
            )
            """
        )
        # Add next_due_date column for legacy tables (ignore duplicate-column errors)
        with suppress(Exception):
            cur.execute(
                """
                ALTER TABLE savings_goals
                ADD COLUMN next_due_date DATE NULL
                """
            )
        # Reference: MySQL ALTER TABLE - https://dev.mysql.com/doc/refman/8.0/en/alter-table.html
        # Add completed_at for archiving completed goals
        with suppress(Exception):
            cur.execute(
                """
                ALTER TABLE savings_goals
                ADD COLUMN completed_at TIMESTAMP NULL
                """
            )
        # Reference: MySQL UPDATE - backfill completed_at for existing 100% goals
        # https://dev.mysql.com/doc/refman/8.0/en/update.html
        cur.execute(
            """
            UPDATE savings_goals
            SET completed_at = COALESCE(updated_at, created_at)
            WHERE completed_at IS NULL AND saved_amount >= target_amount
            """
        )
        # Track skipped periods so suggested amount increases when user skips
        with suppress(Exception):
            cur.execute(
                """
                ALTER TABLE savings_goals
                ADD COLUMN periods_skipped INT UNSIGNED NOT NULL DEFAULT 0
                """
            )
        # Contribution type for insights: on_time (scheduled) vs lump_sum
        with suppress(Exception):
            cur.execute(
                """
                ALTER TABLE savings_goal_deposits
                ADD COLUMN contribution_type VARCHAR(20) NOT NULL DEFAULT 'lump_sum'
                """
            )
        # Backfill: deposits recorded as scheduled contribution (before we had contribution_type) → on_time
        with suppress(Exception):
            cur.execute(
                """
                UPDATE savings_goal_deposits
                SET contribution_type = 'on_time'
                WHERE note LIKE 'Scheduled % contribution'
                """
            )
        cur.execute(
            """
            UPDATE savings_goals
            SET next_due_date = CASE frequency
                WHEN 'weekly' THEN COALESCE(next_due_date, DATE_ADD(CURDATE(), INTERVAL 7 DAY))
                WHEN 'bi-weekly' THEN COALESCE(next_due_date, DATE_ADD(CURDATE(), INTERVAL 14 DAY))
                WHEN 'monthly' THEN COALESCE(next_due_date, DATE_ADD(CURDATE(), INTERVAL 30 DAY))
                ELSE next_due_date
            END
            WHERE next_due_date IS NULL
            """
        )


ensure_goal_tables()


# Reference: CRUD pattern adapted from user.py + MySQL docs.
# Creates a savings goal and records an optional initial deposit.
def create_goal(
    *,
    user_id: int,
    goal_name: str,
    target_amount: Decimal,
    target_date: date,
    frequency: str,
    initial_deposit: Decimal = Decimal("0.00"),
) -> int:
    saved_amount = _to_decimal(initial_deposit)
    target_dec = _to_decimal(target_amount)
    next_due = calculate_next_due_date(date.today(), frequency)
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO savings_goals (
                user_id, goal_name, target_amount, target_date, frequency, saved_amount, next_due_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                goal_name,
                target_dec,
                target_date,
                frequency,
                saved_amount,
                next_due,
            ),
        )
        goal_id = cur.lastrowid
        # Reference: MySQL UPDATE - mark completed on creation if initial deposit meets target
        if saved_amount >= target_dec:
            cur.execute(
                "UPDATE savings_goals SET completed_at = CURRENT_TIMESTAMP WHERE id = %s",
                (goal_id,),
            )
        if saved_amount > 0:
            cur.execute(
                """
                INSERT INTO savings_goal_deposits (goal_id, amount, note, contribution_type)
                VALUES (%s, %s, %s, 'lump_sum')
                """,
                (goal_id, saved_amount, "Initial lump sum"),
            )
        return goal_id


# Reference: Same sources as create_goal.
# Description: Lists active (non-completed) goals for the dashboard view.
def list_goals(user_id: int) -> List[Dict]:
    sql = """
        SELECT id, goal_name, target_amount, target_date, frequency,
               saved_amount, next_due_date, periods_skipped, created_at, updated_at, completed_at
        FROM savings_goals
        WHERE user_id=%s AND completed_at IS NULL
        ORDER BY target_date ASC
    """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()


# Reference: Same CRUD/MySQL sources as list_goals - SELECT with WHERE, ORDER BY, LIMIT
# Description: Lists completed goals for "Previously Completed Goals" section.
def list_completed_goals(user_id: int, limit: int = 50) -> List[Dict]:
    sql = """
        SELECT id, goal_name, target_amount, target_date, frequency,
               saved_amount, next_due_date, periods_skipped, created_at, updated_at, completed_at
        FROM savings_goals
        WHERE user_id=%s AND completed_at IS NOT NULL
        ORDER BY completed_at DESC
        LIMIT %s
    """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (user_id, limit))
        return cur.fetchall()


# Reference: Same CRUD source.
# Description: Fetch a single goal ensuring it belongs to the current user (active or completed).
def get_goal(goal_id: int, user_id: int) -> Optional[Dict]:
    sql = """
        SELECT id, goal_name, target_amount, target_date, frequency,
               saved_amount, next_due_date, periods_skipped, user_id, completed_at, created_at, updated_at
        FROM savings_goals
        WHERE id=%s AND user_id=%s
    """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (goal_id, user_id))
        return cur.fetchone()


# Reference: CRUD update pattern from user.py + MySQL docs.
# Description: Persists edits to a goal's metadata/details.
def update_goal(
    goal_id: int,
    *,
    user_id: int,
    goal_name: str,
    target_amount: Decimal,
    target_date: date,
    frequency: str,
) -> bool:
    new_due = calculate_next_due_date(date.today(), frequency)
    sql = """
        UPDATE savings_goals
        SET goal_name=%s,
            target_amount=%s,
            target_date=%s,
            frequency=%s,
            next_due_date=%s
        WHERE id=%s AND user_id=%s
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            sql,
            (
                goal_name,
                _to_decimal(target_amount),
                target_date,
                frequency,
                new_due,
                goal_id,
                user_id,
            ),
        )
        return cur.rowcount > 0


# Reference: CRUD delete pattern from user.py + MySQL docs.
#Removes a goal and cascades deposits via the FK.
def delete_goal(goal_id: int, *, user_id: int) -> bool:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM savings_goals WHERE id=%s AND user_id=%s",
            (goal_id, user_id),
        )
        return cur.rowcount > 0


#Reference: flask doc + based on chatgpt chat from app.py
# Description: Adds a deposit and increments the saved total atomically.
# contribution_type: 'on_time' for scheduled contribution, 'lump_sum' for manual lump sum.
def add_deposit(
    goal_id: int,
    *,
    user_id: int,
    amount: Decimal,
    note: str = "",
    contribution_type: str = "lump_sum",
) -> bool:
    amount = _to_decimal(amount)
    if amount <= 0:
        return False
    if contribution_type not in ("on_time", "lump_sum"):
        contribution_type = "lump_sum"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, frequency FROM savings_goals WHERE id=%s AND user_id=%s",
            (goal_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            return False
        frequency = row[1]
        next_due = calculate_next_due_date(date.today(), frequency)
        cur.execute(
            """
            INSERT INTO savings_goal_deposits (goal_id, amount, note, contribution_type)
            VALUES (%s, %s, %s, %s)
            """,
            (goal_id, amount, note or "Lump sum deposit", contribution_type),
        )
        cur.execute(
            """
            UPDATE savings_goals
            SET saved_amount = saved_amount + %s,
                next_due_date = %s
            WHERE id=%s
            """,
            (amount, next_due, goal_id),
        )
        return True


# Reference: flask doc + based on chatgpt chat from app.py
# Skips the current contribution period without adding a deposit.
# Also increments periods_skipped so the suggested per-period amount increases.
def skip_next_due(goal_id: int, *, user_id: int) -> Optional[date]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT frequency FROM savings_goals WHERE id=%s AND user_id=%s",
            (goal_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        frequency = row[0]
        next_due = calculate_next_due_date(date.today(), frequency)
        cur.execute(
            """
            UPDATE savings_goals
            SET next_due_date=%s, periods_skipped = COALESCE(periods_skipped, 0) + 1
            WHERE id=%s AND user_id=%s
            """,
            (next_due, goal_id, user_id),
        )
        return next_due


# Reference: flask doc/python docs + based on chatgpt chat from app.py
# Moves the next due date forward based on frequency.
def calculate_next_due_date(start_date: date, frequency: str) -> date:
    days = PERIOD_DAY_MAP.get(frequency, 30)
    return start_date + timedelta(days=days)


# Reference: flask doc/python docs + based on chatgpt chat from app.py
# eturns contextual stats for template rendering incl. due dates.
def list_deposits(goal_id: int, *, user_id: int, limit: int = 50) -> List[Dict]:
    sql = """
        SELECT d.id, d.amount, d.note, d.created_at
        FROM savings_goal_deposits d
        JOIN savings_goals g ON g.id = d.goal_id
        WHERE d.goal_id=%s AND g.user_id=%s
        ORDER BY d.created_at DESC
        LIMIT %s
    """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (goal_id, user_id, limit))
        return cur.fetchall()


# Based on - https://claude.ai/share/caeeec80-5da9-4eb0-bbc6-976de6e0c2a6
# Insights about missed/extra contributions.
# Returns counts of on-time contributions, lump sums, and total skips for pie chart.
def get_contribution_insights(user_id: int) -> Dict:
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(
            """
            SELECT contribution_type, COUNT(*) AS cnt
            FROM savings_goal_deposits d
            JOIN savings_goals g ON g.id = d.goal_id
            WHERE g.user_id = %s
            GROUP BY contribution_type
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    on_time = sum(r["cnt"] for r in rows if (r.get("contribution_type") or "lump_sum") == "on_time")
    lump_sum = sum(r["cnt"] for r in rows if (r.get("contribution_type") or "lump_sum") == "lump_sum")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(periods_skipped), 0) FROM savings_goals WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
    skips = int(row[0]) if row else 0
    return {
        "on_time": on_time,
        "lump_sum": lump_sum,
        "skips": skips,
    }


# Reference: flask doc/python docs + based on chatgpt chat from app.py
# Returns contextual stats for template rendering.
def build_progress(goal: Dict) -> Dict:
    target_amount = _to_decimal(goal["target_amount"])
    saved_amount = _to_decimal(goal["saved_amount"])
    remaining = max(target_amount - saved_amount, Decimal("0.00"))
    percent = 100 if target_amount == 0 else min(
        100, float((saved_amount / target_amount) * 100)
    )

    today = date.today()
    target_date = goal["target_date"]
    days_left = max((target_date - today).days, 0)

    period_days = PERIOD_DAY_MAP.get(goal["frequency"], 30)
    # Contribution opportunities (ceiling): e.g. 26 days = 4 weekly slots, minus any skipped periods
    calendar_periods = (days_left + period_days - 1) // period_days if days_left else 0
    periods_skipped = int(goal.get("periods_skipped") or 0)
    periods_left = max(0, calendar_periods - periods_skipped)
    # Rate-based recommendation: remaining / periods left so each contribution gets you to the goal
    recommended = (
        (remaining / periods_left).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if periods_left > 0
        else remaining
    )

    next_due_date = goal.get("next_due_date")
    is_due = bool(next_due_date and next_due_date <= today)

    return {
        **goal,
        "remaining": remaining,
        "percent_complete": percent,
        "days_left": days_left,
        "periods_left": periods_left,
        "recommended_contribution": recommended,
        "next_due_date": next_due_date,
        "is_due": is_due,
    }


# Reference: CRUD update pattern from user.py + MySQL docs
# https://dev.mysql.com/doc/refman/8.0/en/update.html
# Description: Mark a goal as completed when saved_amount >= target_amount.
# Returns True if the goal was just completed (was not already completed).
def mark_goal_completed_if_done(goal_id: int, user_id: int) -> bool:
    """If goal is at or over target, set completed_at. Returns True if newly completed."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE savings_goals
            SET completed_at = CURRENT_TIMESTAMP
            WHERE id=%s AND user_id=%s AND completed_at IS NULL
              AND saved_amount >= target_amount
            """,
            (goal_id, user_id),
        )
        return cur.rowcount > 0

