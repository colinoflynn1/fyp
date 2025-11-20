# app.py
#start
import os
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user, UserMixin
)
from functools import wraps

# Import helpers from user.py
from user import (
    list_users, add_user, get_user_by_id, update_user, delete_user,
    get_user_by_email, create_user, set_password, verify_password
)
from goals import (
    FREQUENCIES as GOAL_FREQUENCIES,
    list_goals as list_user_goals,
    create_goal as create_user_goal,
    get_goal as get_user_goal,
    update_goal as update_user_goal,
    delete_goal as delete_user_goal,
    add_deposit as add_goal_deposit,
    list_deposits as list_goal_deposits,
    build_progress as build_goal_progress,
    skip_next_due,
)


# Flask App Setup
# load .env from project root
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key")
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=7)

# Serializer for password reset tokens
serializer = URLSafeTimedSerializer(app.secret_key)


#Flask-Login Setup
login_manager = LoginManager(app)
login_manager.login_view = "login"  # redirect here if not logged in


class AuthUser(UserMixin):
    """Wraps DB user rows for Flask-Login."""
    def __init__(self, record: dict):
        self.id = record["id"]
        self.email = record["email"]
        self.full_name = record["full_name"]
        self.role = record["role"]

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


@login_manager.user_loader
def load_user(user_id: str):
    u = get_user_by_id(int(user_id))
    return AuthUser(u) if u else None



#Admin-only decorator
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if not getattr(current_user, "is_admin", False):
            flash("Admins only.", "error")
            return redirect(url_for("home"))
        return fn(*args, **kwargs)
    return wrapper



# Routes
# All routes sourced from IS3312, Bill Emerson .

@app.route("/")
def home():
    return render_template("home.html", title="Home")


# Reference: Python Decimal docs + Flask request handling.
# Description: Validates decimal form inputs and provides human-friendly errors.
def _parse_decimal_field(value: str, field_name: str):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid number for {field_name}.")


# Reference: Python datetime strptime patterns.
# Description: Converts YYYY-MM-DD strings into date objects for DB writes.
def _parse_date_field(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError("Please use the YYYY-MM-DD date format.")


# Reference: Flask pattern for reusing template context.
# Description: Centralizes the data required for both create/edit templates.
def _render_goal_form(mode: str, goal: dict | None = None):
    title = "New Goal" if mode == "create" else "Edit Goal"
    return render_template(
        "goal_form.html",
        title=title,
        mode=mode,
        goal=goal,
        freq_options=GOAL_FREQUENCIES,
    )


# Sign Up
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("full_name", "").strip()
        pwd = request.form.get("password", "")
        if not email or not name or not pwd:
            flash("All fields are required.", "error")
            return render_template("signup.html")
        if get_user_by_email(email):
            flash("Email already registered.", "error")
            return render_template("signup.html")
        create_user(email=email, full_name=name, password=pwd)
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("signup.html", title="Sign Up")


# Log In
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pwd = request.form.get("password", "")
        u = get_user_by_email(email)
        if not u or not verify_password(u.get("password_hash"), pwd):
            flash("Invalid email or password.", "error")
            return render_template("login.html")
        login_user(AuthUser(u), remember=True)
        flash("Logged in.", "success")
        return redirect(url_for("home"))
    return render_template("login.html", title="Log In")


# Log Out
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("home"))

# Below is from CHATGPT - https://chatgpt.com/share/690e7fce-042c-800c-9243-f68fbb847eec I included this and my own
#code to get this to work
# Forgot Password
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        u = get_user_by_email(email)
        if not u:
            flash("If the email exists, a reset link will be generated.", "info")
            return redirect(url_for("login"))
        token = serializer.dumps({"uid": u["id"]})
        reset_url = url_for("reset_password", token=token, _external=True)
        # Demo: print reset link to console
        print("\n*** Password reset link:", reset_url, "***\n")
        flash("Reset link generated (see server console in this demo).", "success")
        return redirect(url_for("login"))
    return render_template("forgot.html", title="Forgot Password")



# Reset Password
@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        data = serializer.loads(token, max_age=3600)  # 1 hour validity
    except SignatureExpired:
        flash("Reset link expired.", "error")
        return redirect(url_for("forgot"))
    except BadSignature:
        flash("Invalid reset link.", "error")
        return redirect(url_for("forgot"))

    uid = int(data["uid"])
    if request.method == "POST":
        pwd = request.form.get("password", "")
        if not pwd:
            flash("Password required.", "error")
            return render_template("reset.html")
        set_password(uid, pwd)
        flash("Password updated. You can log in.", "success")
        return redirect(url_for("login"))
    return render_template("reset.html", title="Reset Password")


# Admin: List Users
@app.route("/users")
@login_required
@admin_required
def users():
    return render_template("users.html", users=list_users(), title="Users")


# Admin: Add User
@app.route("/users/new", methods=["GET", "POST"])
@login_required
@admin_required
def users_new():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("full_name", "").strip()
        role = request.form.get("role", "user")
        if not email or not name:
            flash("Email and Full Name are required.", "error")
            return render_template("user_form.html", mode="create", user=None)
        if get_user_by_email(email):
            flash("Email already exists.", "error")
            return render_template("user_form.html", mode="create", user=None)
        add_user(email=email, full_name=name, role=role)
        flash("User created.", "success")
        return redirect(url_for("users"))
    return render_template("user_form.html", mode="create", user=None, title="Add User")


# Admin: Edit User
@app.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def users_edit(user_id: int):
    if request.method == "POST":
        updated = update_user(
            user_id,
            email=request.form.get("email"),
            full_name=request.form.get("full_name"),
            role=request.form.get("role"),
        )
        flash("User updated." if updated else "No changes.", "success")
        return redirect(url_for("users"))
    user = get_user_by_id(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("users"))
    return render_template("user_form.html", mode="edit", user=user, title="Edit User")


# Admin: Delete User
@app.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def users_delete(user_id: int):
    if delete_user(user_id):
        flash("User deleted.", "success")
    else:
        flash("Nothing deleted.", "info")
    return redirect(url_for("users"))


# Savings Goals ----------------------------------------------------
# Reference: Flask docs on login_required dashboards + personal design.
# Description: Renders the overview page with progress maths and deposit history.
@app.route("/goals")
@login_required
def goals_dashboard():
    raw_goals = list_user_goals(current_user.id)
    enriched = []
    for goal in raw_goals:
        progress = build_goal_progress(goal)
        deposits = list_goal_deposits(goal["id"], user_id=current_user.id, limit=5)
        progress["recent_deposits"] = deposits
        enriched.append(progress)
    return render_template(
        "goals.html",
        title="Savings Goals",
        goals=enriched,
    )


# Reference: Flask form handling docs (https://flask.palletsprojects.com/patterns/wtforms/)
# Description: Handles creation of a new savings goal with validation feedback.
@app.route("/goals/new", methods=["GET", "POST"])
@login_required
def goal_new():
    if request.method == "POST":
        form_goal = {
            "goal_name": request.form.get("goal_name", "").strip(),
            "target_amount": request.form.get("target_amount", "0").strip(),
            "initial_deposit": request.form.get("initial_deposit", "0").strip(),
            "frequency": request.form.get("frequency", ""),
            "target_date": request.form.get("target_date", ""),
        }
        goal_name = form_goal["goal_name"]
        target_amount_raw = form_goal["target_amount"]
        lump_sum_raw = form_goal["initial_deposit"]
        frequency = form_goal["frequency"]
        target_date_raw = form_goal["target_date"]

        if not goal_name:
            flash("Goal name is required.", "error")
            return _render_goal_form("create", goal=form_goal)
        if frequency not in GOAL_FREQUENCIES:
            flash("Please choose a valid frequency.", "error")
            return _render_goal_form("create", goal=form_goal)
        try:
            target_amount = _parse_decimal_field(target_amount_raw, "target amount")
            lump_sum = _parse_decimal_field(lump_sum_raw, "initial deposit")
            target_date = _parse_date_field(target_date_raw)
        except ValueError as exc:
            flash(str(exc), "error")
            return _render_goal_form("create", goal=form_goal)

        if target_amount <= 0:
            flash("Target amount must be positive.", "error")
            return _render_goal_form("create", goal=form_goal)
        if target_date <= datetime.utcnow().date():
            flash("Target date must be in the future.", "error")
            return _render_goal_form("create", goal=form_goal)
        if lump_sum < 0:
            flash("Initial deposit cannot be negative.", "error")
            return _render_goal_form("create", goal=form_goal)

        create_user_goal(
            user_id=current_user.id,
            goal_name=goal_name,
            target_amount=target_amount,
            target_date=target_date,
            frequency=frequency,
            initial_deposit=lump_sum,
        )
        flash("Savings goal created.", "success")
        return redirect(url_for("goals_dashboard"))

    return _render_goal_form("create")


# Reference: Same as goal_new (Flask form handling).
# Description: Allows the user to update target numbers, timeline, or cadence.
@app.route("/goals/<int:goal_id>/edit", methods=["GET", "POST"])
@login_required
def goal_edit(goal_id: int):
    goal = get_user_goal(goal_id, current_user.id)
    if not goal:
        flash("Goal not found.", "error")
        return redirect(url_for("goals_dashboard"))

    if request.method == "POST":
        form_goal = {
            **goal,
            "goal_name": request.form.get("goal_name", "").strip(),
            "target_amount": request.form.get("target_amount", "0").strip(),
            "frequency": request.form.get("frequency", ""),
            "target_date": request.form.get("target_date", ""),
        }
        goal_name = form_goal["goal_name"]
        target_amount_raw = form_goal["target_amount"]
        frequency = form_goal["frequency"]
        target_date_raw = form_goal["target_date"]

        if not goal_name:
            flash("Goal name is required.", "error")
            return _render_goal_form("edit", goal=form_goal)
        if frequency not in GOAL_FREQUENCIES:
            flash("Please choose a valid frequency.", "error")
            return _render_goal_form("edit", goal=form_goal)
        try:
            target_amount = _parse_decimal_field(target_amount_raw, "target amount")
            target_date = _parse_date_field(target_date_raw)
        except ValueError as exc:
            flash(str(exc), "error")
            return _render_goal_form("edit", goal=form_goal)

        if target_amount <= 0:
            flash("Target amount must be positive.", "error")
            return _render_goal_form("edit", goal=form_goal)

        update_user_goal(
            goal_id,
            user_id=current_user.id,
            goal_name=goal_name,
            target_amount=target_amount,
            target_date=target_date,
            frequency=frequency,
        )
        flash("Goal updated.", "success")
        return redirect(url_for("goals_dashboard"))

    return _render_goal_form("edit", goal=goal)


# Reference: REST-style delete endpoint pattern + Flask docs.
# Description: Removes a goal and cascades deposits using DB foreign keys.
@app.route("/goals/<int:goal_id>/delete", methods=["POST"])
@login_required
def goal_delete(goal_id: int):
    if delete_user_goal(goal_id, user_id=current_user.id):
        flash("Goal deleted.", "success")
    else:
        flash("Could not delete goal.", "error")
    return redirect(url_for("goals_dashboard"))


# Reference: Double-entry deposit pattern inspired by budgeting apps.
# Description: Adds a lump-sum payment to an existing goal and updates totals.
@app.route("/goals/<int:goal_id>/deposit", methods=["POST"])
@login_required
def goal_deposit(goal_id: int):
    amount_raw = request.form.get("amount", "0").strip()
    note = request.form.get("note", "").strip()
    try:
        amount = _parse_decimal_field(amount_raw, "deposit amount")
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("goals_dashboard"))

    if amount <= 0:
        flash("Deposit must be positive.", "error")
        return redirect(url_for("goals_dashboard"))

    if add_goal_deposit(goal_id, user_id=current_user.id, amount=amount, note=note):
        flash("Deposit recorded.", "success")
    else:
        flash("Could not add deposit.", "error")
    return redirect(url_for("goals_dashboard"))


# Reference: Guided contribution workflow inspired by budgeting apps.
# Description: Records the recommended amount when the user confirms they paid.
@app.route("/goals/<int:goal_id>/auto-contribute", methods=["POST"])
@login_required
def goal_auto_contribute(goal_id: int):
    goal = get_user_goal(goal_id, current_user.id)
    if not goal:
        flash("Goal not found.", "error")
        return redirect(url_for("goals_dashboard"))
    progress = build_goal_progress(goal)
    next_due = progress.get("next_due_date")
    if not next_due or not progress.get("is_due"):
        flash("This contribution is not due yet.", "info")
        return redirect(url_for("goals_dashboard"))
    amount = progress.get("recommended_contribution")
    if not amount or amount <= 0:
        flash("No contribution recommended for this period.", "info")
        return redirect(url_for("goals_dashboard"))
    if add_goal_deposit(
        goal_id,
        user_id=current_user.id,
        amount=amount,
        note=f"Scheduled {goal.get('frequency', 'periodic')} contribution",
    ):
        flash(f"Recorded €{amount} towards {goal['goal_name']}.", "success")
    else:
        flash("Could not record contribution.", "error")
    return redirect(url_for("goals_dashboard"))


# Reference: Habit tracking UX patterns for defer/skip actions.
# Description: Moves the next contribution date forward without adding funds.
@app.route("/goals/<int:goal_id>/skip-period", methods=["POST"])
@login_required
def goal_skip_period(goal_id: int):
    next_due = skip_next_due(goal_id, user_id=current_user.id)
    if not next_due:
        flash("Goal not found.", "error")
    else:
        flash(
            f"Next contribution moved to {next_due.strftime('%d %b %Y')}.",
            "info",
        )
    return redirect(url_for("goals_dashboard"))



#Run the app

if __name__ == "__main__":
    app.run(debug=True)
