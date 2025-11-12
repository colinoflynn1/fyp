# app.py
#start
import os
from datetime import timedelta
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



#Run the app

if __name__ == "__main__":
    app.run(debug=True)
