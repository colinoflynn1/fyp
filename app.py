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
from notifications import (
    list_notifications,
    create_notification,
    mark_notification_read,
    mark_all_read,
    check_payment_due_notifications,
    check_milestone_notifications,
)
from email_service import (
    send_password_reset_email,
    send_payment_due_email,
    send_milestone_email,
)


# Reference: Based on Flask Documentation - Application Setup
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#a-minimal-application
# Flask App Setup
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key")
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=7)

# Reference: Based on ItsDangerous Documentation - URL Safe Timed Serializer
# https://itsdangerous.palletsprojects.com/en/2.1.x/serializer/
# Serializer for password reset tokens
serializer = URLSafeTimedSerializer(app.secret_key)


# Reference: Based on Flask-Login Documentation - Initializing the Login Manager
# https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager
#Flask-Login Setup
login_manager = LoginManager(app)
login_manager.login_view = "login"  # redirect here if not logged in


# Reference: Based on Flask-Login Documentation - User Class
# https://flask-login.readthedocs.io/en/latest/#flask_login.UserMixin
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


# Reference: Based on Flask-Login Documentation - User Loader
# https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader
@login_manager.user_loader
def load_user(user_id: str):
    u = get_user_by_id(int(user_id))
    return AuthUser(u) if u else None


# Reference: Based on Flask Documentation - Decorators
# https://flask.palletsprojects.com/en/3.0.x/patterns/viewdecorators/
# Combined with Python functools.wraps pattern
# https://docs.python.org/3/library/functools.html#functools.wraps
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
# Reference: Based on Flask Documentation - Routing [Enhanced dashboard with notifications]
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#routing
# Dashboard route pattern adapted from Flask docs on template rendering
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#rendering-templates
@app.route("/")
def home():
    if current_user.is_authenticated:
        # Get user's goals with progress
        goals = list_user_goals(current_user.id)
        enriched_goals = []
        for goal in goals:
            enriched_goals.append(build_goal_progress(goal))
        
        # Get user preferences
        user = get_user_by_id(current_user.id)
        
        # Get unread notifications (only if dashboard notifications are enabled)
        notifications = []
        if user and user.get("dashboard_notifications", True):
            notifications = list_notifications(current_user.id, limit=10, unread_only=True)
            
            # Check for payment due dates and create notifications
            check_payment_due_notifications(current_user.id)
            
            # Re-fetch notifications after checking
            notifications = list_notifications(current_user.id, limit=10, unread_only=True)
        
        # Calculate summary stats
        total_saved = sum(Decimal(str(g.get("saved_amount", 0))) for g in enriched_goals)
        total_target = sum(Decimal(str(g.get("target_amount", 0))) for g in enriched_goals)
        total_remaining = sum(Decimal(str(g.get("remaining", 0))) for g in enriched_goals)
        goals_due = sum(1 for g in enriched_goals if g.get("is_due"))
        
        # Send email notifications if enabled
        if user and user.get("email_notifications"):
            # Check for payment due dates to email
            for goal in enriched_goals:
                if goal.get("is_due") and goal.get("next_due_date"):
                    send_payment_due_email(
                        current_user.email,
                        current_user.full_name,
                        goal["goal_name"],
                        float(goal["recommended_contribution"]),
                        goal["next_due_date"].strftime("%d %b %Y"),
                    )
        
        return render_template(
            "home.html",
            title="Dashboard",
            goals=enriched_goals,
            notifications=notifications,
            total_saved=float(total_saved),
            total_target=float(total_target),
            total_remaining=float(total_remaining),
            goals_due=goals_due,
        )
    return render_template("home.html", title="Home")


# Reference: Based on Python Decimal docs + Flask request handling.
# Validates decimal form inputs and provides human-friendly errors.
def _parse_decimal_field(value: str, field_name: str):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError(f"Invalid number for {field_name}.")


# Reference: Based on Python datetime strptime patterns.
# Converts YYYY-MM-DD strings into date objects for DB writes.
def _parse_date_field(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError("Please use the YYYY-MM-DD date format.")


# Reference: Based on Flask pattern for reusing template context.
# Centralizes the data required for both create/edit templates.
def _render_goal_form(mode: str, goal: dict | None = None):
    title = "New Goal" if mode == "create" else "Edit Goal"
    return render_template(
        "goal_form.html",
        title=title,
        mode=mode,
        goal=goal,
        freq_options=GOAL_FREQUENCIES,
    )


# Reference: Based on Flask Documentation - HTTP Methods
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#http-methods
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


# Reference: Based on Flask-Login Documentation - Login Example
# https://flask-login.readthedocs.io/en/latest/#login-example
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


# Reference: Based on Flask-Login Documentation - Logout
# https://flask-login.readthedocs.io/en/latest/#flask_login.logout_user
# Log Out
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("home"))


# Combined with Flask email sending pattern from email_service.py
# Password reset token generation adapted from standard Flask patterns
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
        
        # Send password reset email
        email_sent = send_password_reset_email(u["email"], u["full_name"], reset_url)
        if email_sent:
            flash("Password reset link sent to your email.", "success")
        else:
            # Fallback: print to console if email fails
            print("\n*** Password reset link:", reset_url, "***\n")
            flash("Reset link generated (see server console). Email service unavailable.", "info")
        return redirect(url_for("login"))
    return render_template("forgot.html", title="Forgot Password")



# Reference: Based on ItsDangerous Documentation - Loading Tokens
# https://itsdangerous.palletsprojects.com/en/2.1.x/serializer/#loading
# Token validation with max_age parameter
# Reset Password
@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        data = serializer.loads(token, max_age=3600) # use loads to verify 1 hour validity
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


# Savings Goals
# Reference: Based on Flask docs on login_required dashboards + personal design.
# Renders the overview page with progress maths and deposit history.
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


# Reference: Based on Flask form handling docs (https://flask.palletsprojects.com/patterns/wtforms/)
# Handles creation of a new savings goal with validation feedback.
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


# Reference: Based on Flask form handling docs (https://flask.palletsprojects.com/patterns/wtforms/)
# Allows the user to update target numbers, timeline, or cadence.
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



# Removes a goal and cascades deposits using DB foreign keys.
@app.route("/goals/<int:goal_id>/delete", methods=["POST"])
@login_required
def goal_delete(goal_id: int):
    if delete_user_goal(goal_id, user_id=current_user.id):
        flash("Goal deleted.", "success")
    else:
        flash("Could not delete goal.", "error")
    return redirect(url_for("goals_dashboard"))


# Reference: Based on Flask Documentation - Form Data Handling
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#the-request-object
# Adds a lump-sum payment to an existing goal and updates totals.
# Milestone checking integrated after deposit recording
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
        # Check for milestone achievements
        milestone_ids = check_milestone_notifications(current_user.id, goal_id=goal_id)
        
        # Send email if milestone reached and email notifications enabled
        user = get_user_by_id(current_user.id)
        if milestone_ids and user and user.get("email_notifications"):
            goal = get_user_goal(goal_id, current_user.id)
            if goal:
                progress = build_goal_progress(goal)
                percent = progress.get("percent_complete", 0)
                send_milestone_email(
                    current_user.email,
                    current_user.full_name,
                    goal["goal_name"],
                    percent,
                )
        
        flash("Deposit recorded.", "success")
    else:
        flash("Could not add deposit.", "error")
    return redirect(url_for("goals_dashboard"))


# Reference: Based on Flask Documentation - POST Request Handling 
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#http-methods
# Records the recommended amount when the user confirms they paid.
# Integrated milestone notification checking after contribution
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
        # Check for milestone achievements
        milestone_ids = check_milestone_notifications(current_user.id, goal_id=goal_id)
        
        # Send email if milestone reached and email notifications enabled
        user = get_user_by_id(current_user.id)
        if milestone_ids and user and user.get("email_notifications"):
            progress = build_goal_progress(goal)
            percent = progress.get("percent_complete", 0)
            send_milestone_email(
                current_user.email,
                current_user.full_name,
                goal["goal_name"],
                percent,
            )
        
        flash(f"Recorded €{amount} towards {goal['goal_name']}.", "success")
    else:
        flash("Could not record contribution.", "error")
    return redirect(url_for("goals_dashboard"))


# Reference: Based on Flask doc + based on chatgpt chat in documentation.
# Moves the next contribution date forward without adding funds.
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


# Reference: Based on Flask Documentation - Request Data 
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#accessing-request-data
# Standard form handling pattern for user preferences
# User Settings / Notification Preferences
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        email_notifications = request.form.get("email_notifications") == "on"
        dashboard_notifications = request.form.get("dashboard_notifications") == "on"
        
        if update_user(
            current_user.id,
            email_notifications=email_notifications,
            dashboard_notifications=dashboard_notifications,
        ):
            flash("Notification preferences updated.", "success")
            # Redirect to home so user can see notifications appear/disappear immediately
            return redirect(url_for("home"))
        else:
            flash("Could not update preferences.", "error")
        return redirect(url_for("settings"))
    
    user = get_user_by_id(current_user.id)
    return render_template(
        "settings.html",
        title="Settings",
        user=user,
    )


# Reference: Based on Flask Documentation - Variable Rules 
# https://flask.palletsprojects.com/en/3.0.x/quickstart/#variable-rules
# RESTful route pattern for notification updates
# Mark notification as read
@app.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read_route(notification_id: int):
    if mark_notification_read(notification_id, current_user.id):
        flash("Notification marked as read.", "success")
    return redirect(request.referrer or url_for("home"))


# Reference: Based on Flask Documentation - Request Referrer 
# https://flask.palletsprojects.com/en/3.0.x/api/#flask.Request.referrer
# Bulk update pattern for notifications
# Mark all notifications as read
@app.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    count = mark_all_read(current_user.id)
    flash(f"Marked {count} notification(s) as read.", "success")
    return redirect(request.referrer or url_for("home"))


#Run the app

if __name__ == "__main__":
    app.run(debug=True)
