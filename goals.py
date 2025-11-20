"""Savings goal persistence helpers."""

from __future__ import annotations

from contextlib import suppress
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

from db import get_conn


# Reference: Personal research + Monzo budgeting articles.
# Description: Enumerations for user-selectable contribution cadence and the
# approximate number of days used for workload calculations.
FREQUENCIES = ("weekly", "bi-weekly", "monthly")
PERIOD_DAY_MAP = {
    "weekly": 7,
    "bi-weekly": 14,
    "monthly": 30,
}


# Reference: Python docs on Decimal quantize (https://docs.python.org/3/library/decimal.html)
# Description: Helper that ensures every currency input/output is rounded to cents.
def _to_decimal(value: Decimal | float | int) -> Decimal:
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Reference: Official MySQL doc on CREATE TABLE/ALTER TABLE + FK constraints.
# Description: Ensures the savings tables exist before the app continues and are updated
# with newer columns (like next_due_date) when we deploy new features.
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
# Description: Creates a savings goal and records an optional initial deposit.
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
                _to_decimal(target_amount),
                target_date,
                frequency,
                saved_amount,
                next_due,
            ),
        )
        goal_id = cur.lastrowid
        if saved_amount > 0:
            cur.execute(
                """
                INSERT INTO savings_goal_deposits (goal_id, amount, note)
                VALUES (%s, %s, %s)
                """,
                (goal_id, saved_amount, "Initial lump sum"),
            )
        return goal_id


# Reference: Same sources as create_goal.
# Description: Lists all goals for the dashboard view.
def list_goals(user_id: int) -> List[Dict]:
    sql = """
        SELECT id, goal_name, target_amount, target_date, frequency,
               saved_amount, next_due_date, created_at, updated_at
        FROM savings_goals
        WHERE user_id=%s
        ORDER BY target_date ASC
    """
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(sql, (user_id,))
        return cur.fetchall()


# Reference: Same CRUD source.
# Description: Fetch a single goal ensuring it belongs to the current user.
def get_goal(goal_id: int, user_id: int) -> Optional[Dict]:
    sql = """
        SELECT id, goal_name, target_amount, target_date, frequency,
               saved_amount, next_due_date, user_id
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
# Description: Removes a goal and cascades deposits via the FK.
def delete_goal(goal_id: int, *, user_id: int) -> bool:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM savings_goals WHERE id=%s AND user_id=%s",
            (goal_id, user_id),
        )
        return cur.rowcount > 0


# Reference: Double-entry style update based on fintech blogs (e.g. YNAB) + MySQL docs.
# Description: Adds a lump-sum deposit and increments the saved total atomically.
def add_deposit(goal_id: int, *, user_id: int, amount: Decimal, note: str = "") -> bool:
    amount = _to_decimal(amount)
    if amount <= 0:
        return False
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
            INSERT INTO savings_goal_deposits (goal_id, amount, note)
            VALUES (%s, %s, %s)
            """,
            (goal_id, amount, note or "Lump sum deposit"),
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


# Reference: Habit tracking UX patterns for grace periods.
# Description: Skips the current contribution period without adding a deposit.
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
            SET next_due_date=%s
            WHERE id=%s AND user_id=%s
            """,
            (next_due, goal_id, user_id),
        )
        return next_due


# Reference: Goal scheduling helper derived from PERIOD_DAY_MAP logic.
# Description: Moves the next due date forward based on frequency.
def calculate_next_due_date(start_date: date, frequency: str) -> date:
    days = PERIOD_DAY_MAP.get(frequency, 30)
    return start_date + timedelta(days=days)


# Reference: Summary card maths inspired by NerdWallet savings calculators
# and habit tracking UX patterns.
# Description: Returns contextual stats for template rendering incl. due dates.
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


# Reference: Summary card maths inspired by NerdWallet savings calculators.
# Description: Returns contextual stats for template rendering.
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
    periods_left = (days_left + period_days - 1) // period_days if days_left else 0
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

