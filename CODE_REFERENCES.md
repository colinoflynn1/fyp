# Code References Documentation

This document lists all references and sources for code sections in this project, organized by file and section. These references are also included as comments in the code files themselves.

## app.py

### Flask Application Setup
- **Reference**: Based on Flask Documentation - Application Setup
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#a-minimal-application

### Password Reset Token Serialization
- **Reference**: Based on ItsDangerous Documentation - URL Safe Timed Serializer
  - URL: https://itsdangerous.palletsprojects.com/en/2.1.x/serializer/

### Flask-Login Setup
- **Reference**: Based on Flask-Login Documentation - Initializing the Login Manager
  - URL: https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager

### User Class (AuthUser)
- **Reference**: Based on Flask-Login Documentation - User Class
  - URL: https://flask-login.readthedocs.io/en/latest/#flask_login.UserMixin

### User Loader
- **Reference**: Based on Flask-Login Documentation - User Loader
  - URL: https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader

### Admin Decorator
- **Reference**: Based on Flask Documentation - Decorators
  - URL: https://flask.palletsprojects.com/en/3.0.x/patterns/viewdecorators/
- **Reference**: Python functools.wraps
  - URL: https://docs.python.org/3/library/functools.html#functools.wraps

### Routes
- **Reference**: Based on Flask Documentation - Routing
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#routing
- **Reference**: Based on Flask Documentation - Template Rendering
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#rendering-templates

### HTTP Methods
- **Reference**: Based on Flask Documentation - HTTP Methods
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#http-methods

### Login/Logout
- **Reference**: Based on Flask-Login Documentation - Login Example
  - URL: https://flask-login.readthedocs.io/en/latest/#login-example
- **Reference**: Based on Flask-Login Documentation - Logout
  - URL: https://flask-login.readthedocs.io/en/latest/#flask_login.logout_user

### Password Reset
- **Reference**: Based on ItsDangerous Documentation - URL Safe Timed Serializer
  - URL: https://itsdangerous.palletsprojects.com/en/2.1.x/serializer/
- **Reference**: Based on ItsDangerous Documentation - Loading Tokens
  - URL: https://itsdangerous.palletsprojects.com/en/2.1.x/serializer/#loading

### Form Handling
- **Reference**: Based on Flask Documentation - Request Data
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#accessing-request-data

### Variable Rules
- **Reference**: Based on Flask Documentation - Variable Rules
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#variable-rules

### Request Referrer
- **Reference**: Based on Flask Documentation - Request Referrer
  - URL: https://flask.palletsprojects.com/en/3.0.x/api/#flask.Request.referrer

### Decimal Parsing
- **Reference**: Based on Python Decimal docs + Flask request handling
  - URL: https://docs.python.org/3/library/decimal.html

### Date Parsing
- **Reference**: Based on Python datetime strptime patterns
  - URL: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior

### Dashboard & Notifications
- **Reference**: Based on Flask docs on login_required dashboards + personal design
- **Reference**: Based on Flask form handling docs
  - URL: https://flask.palletsprojects.com/patterns/wtforms/

## user.py

### Database Table Alteration
- **Reference**: Based on Similar pattern to goals.py ensure_goal_tables
- **Reference**: Based on MySQL Documentation - ALTER TABLE
  - URL: https://dev.mysql.com/doc/refman/8.0/en/alter-table.html

### CRUD Operations
- **Reference**: Based on MySQL Documentation - INSERT statement
  - URL: https://dev.mysql.com/doc/refman/8.0/en/insert.html
- **Reference**: Based on MySQL Documentation - UPDATE statement
  - URL: https://dev.mysql.com/doc/refman/8.0/en/update.html
- **Reference**: Based on MySQL Documentation - DELETE statement
  - URL: https://dev.mysql.com/doc/refman/8.0/en/delete.html
- **Reference**: Based on MySQL Documentation - SELECT statement
  - URL: https://dev.mysql.com/doc/refman/8.0/en/select.html
- **Reference**: Based on MySQL Documentation - SELECT with LIMIT
  - URL: https://dev.mysql.com/doc/refman/8.0/en/select.html#select-limit
- **Reference**: Based on MySQL Documentation - SELECT with WHERE clause
  - URL: https://dev.mysql.com/doc/refman/8.0/en/select.html#select-where

### Password Hashing
- **Reference**: Based on Werkzeug Security Documentation - Password Hashing
  - URL: https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.generate_password_hash
- **Reference**: Based on Werkzeug Security Documentation - Password Checking
  - URL: https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.check_password_hash

### Dynamic SQL Construction
- **Pattern**: Adapted from Flask-SQLAlchemy patterns

## notifications.py

### Table Creation
- **Reference**: Based on ensure_goal_tables() in goals.py
- **Reference**: Based on MySQL Documentation - CREATE TABLE
  - URL: https://dev.mysql.com/doc/refman/8.0/en/create-table.html
- **Reference**: Based on Python contextlib.suppress
  - URL: https://docs.python.org/3/library/contextlib.html#contextlib.suppress

### CRUD Operations
- **Reference**: Based on create_user() in user.py and create_goal() in goals.py
  - MySQL INSERT: https://dev.mysql.com/doc/refman/8.0/en/insert.html
- **Reference**: Based on list_users() in user.py and list_goals() in goals.py
  - MySQL SELECT with WHERE: https://dev.mysql.com/doc/refman/8.0/en/select.html
- **Reference**: Based on update_user() in user.py and update_goal() in goals.py
  - MySQL UPDATE: https://dev.mysql.com/doc/refman/8.0/en/update.html
- **Reference**: Based on update_user() pattern in user.py
  - MySQL UPDATE with WHERE: https://dev.mysql.com/doc/refman/8.0/en/update.html

### Payment Due Notifications
- **Reference**: Based on build_progress() in goals.py for date calculations
- **Reference**: Based on Python datetime.date
  - URL: https://docs.python.org/3/library/datetime.html#datetime.date
- **Uses**: list_goals() from goals.py and build_progress() for due date logic

### Milestone Notifications
- **Reference**: Based on build_progress() in goals.py for percentage calculations
- **Reference**: Based on Python percentage calculations
  - URL: https://docs.python.org/3/library/functions.html#round
- **Uses**: list_goals() from goals.py and build_progress() for milestone detection

## email_service.py

### Gmail API Authentication
- **Reference**: Based on Gmail API Python Quickstart
  - URL: https://developers.google.com/gmail/api/quickstart/python
- **Reference**: Based on Google Auth Library Documentation
  - URL: https://google-auth.readthedocs.io/

### Email Sending
- **Reference**: All send email functions based on YouTube walkthrough
  - URL: https://www.youtube.com/watch?v=p7cn1n1kx3I
- **Reference**: Based on Gmail API Python Client Library - Sending Messages
  - URL: https://developers.google.com/gmail/api/guides/sending
- **Reference**: Based on Python email.mime Documentation
  - URL: https://docs.python.org/3/library/email.mime.html
- **Reference**: Based on Python base64 Documentation
  - URL: https://docs.python.org/3/library/base64.html

### Email Templates
- **Password Reset Email**: Based on standard email template pattern for password reset
- **Payment Due Email**: Based on notification email template pattern
- **Milestone Email**: Based on achievement notification email pattern

## goals.py

### Decimal Handling
- **Reference**: Based on Python docs on Decimal quantize
  - URL: https://docs.python.org/3/library/decimal.html

### MySQL Table Creation
- **Reference**: Based on Official MySQL Documentation
  - URL: https://dev.mysql.com/doc/refman/8.0/en/create-table.html

### CRUD Patterns
- **Reference**: Based on CRUD pattern adapted from user.py + MySQL docs
- **Reference**: Based on MySQL Documentation
  - URL: https://dev.mysql.com/doc/refman/8.0/en/

### Completed Goals Feature
- **completed_at column**: MySQL ALTER TABLE
  - URL: https://dev.mysql.com/doc/refman/8.0/en/alter-table.html
- **Backfill migration**: MySQL UPDATE for existing 100% goals
  - URL: https://dev.mysql.com/doc/refman/8.0/en/update.html
- **list_completed_goals**: Same CRUD/MySQL sources as list_goals (SELECT, WHERE, ORDER BY, LIMIT)
- **mark_goal_completed_if_done**: CRUD update pattern from user.py + MySQL UPDATE
- **Completion on create_goal**: MySQL UPDATE when initial deposit >= target

## app.py – Completed Goals

### goal_view Route
- **Reference**: Flask variable rules
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#variable-rules
- **Uses**: get_user_goal, build_goal_progress, list_goal_deposits from goals.py

### Completion Notifications (goal_new, goal_deposit, goal_auto_contribute)
- **Reference**: create_notification from notifications.py
- **Reference**: send_goal_completed_email from email_service.py
- **Reference**: mark_goal_completed_if_done from goals.py
- **User preferences**: dashboard_notifications, email_notifications from user settings

## email_service.py – Goal Completed Email

### send_goal_completed_email
- **Reference**: Goal completion celebration email pattern
- **Reference**: Adapted from milestone and payment due email templates
- **Reference**: Python email.mime and send_email (see Email Templates above)

## notifications.py – Milestone Adjustment

### 100% Milestone Exclusion
- **Reference**: 100% milestone removed from check_milestone_notifications
- **Reason**: Handled by goal completion flow (app.py goal_deposit, goal_auto_contribute)

## templates/goal_view.html

- **Reference**: Jinja2 template inheritance
  - URL: https://jinja.palletsprojects.com/en/3.1.x/templates/#template-inheritance
- **Reference**: Jinja2 conditionals and for loops
- **Reference**: Reuses goal-card, goal-stats, progress-track styles from goals.html

## templates/goals.html & home.html – Completed Goals Section

- **Reference**: Same Jinja2 patterns as existing goals sections
- **Reference**: Reuses goal-preview-card, goal-grid patterns
- **Reference**: url_for goal_view for completed goal links

## static/style.css – Completed Goals Styles

- **Reference**: CSS variables (--success, --accent) from existing theme
- **Reference**: W3Schools CSS
  - URL: https://www.w3schools.com/css/default.asp
- **Pattern**: Mirrors milestone and payment-due notification styling

## chatbot_service.py (AI Chatbot)

### Gemini API Integration
- **Reference**: Based on Google Gen AI SDK Documentation
  - URL: https://googleapis.github.io/python-genai/
- **Reference**: Gemini API Quickstart
  - URL: https://ai.google.dev/gemini-api/docs/quickstart
- **Reference**: Gemini API Text Generation (generate_content, system instructions, multi-turn)
  - URL: https://ai.google.dev/gemini-api/docs/text-generation
- **Reference**: Gemini API Models (model names, fallback chain)
  - URL: https://ai.google.dev/gemini-api/docs/models

### Client Initialization
- **Reference**: Based on Google Gen AI SDK - Client and API key
  - URL: https://ai.google.dev/gemini-api/docs/api-key
- **Pattern**: Lazy import to avoid startup failure when GEMINI_API_KEY is missing

### System Prompt and Context
- **Reference**: Gemini API System Instructions
  - URL: https://ai.google.dev/gemini-api/docs/text-generation#system_instructions
- **Uses**: list_goals and build_progress from goals.py for user context

### JSON Parsing
- **Reference**: Based on Python re module
  - URL: https://docs.python.org/3/library/re.html
- **Reference**: Based on Python json module
  - URL: https://docs.python.org/3/library/json.html

### Goal Validation
- **Reference**: Based on goal_new route and create_goal validation in goals.py (project-internal)
- **Reference**: Python Decimal
  - URL: https://docs.python.org/3/library/decimal.html
- **Reference**: Python datetime
  - URL: https://docs.python.org/3/library/datetime.html

## app.py – AI Chatbot Routes

### Chat Page
- **Reference**: Based on Flask Documentation - Routing and Template Rendering
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#routing
- **Reference**: Flask Session (chat_history, pending_goal)
  - URL: https://flask.palletsprojects.com/en/3.0.x/api/#sessions

### Chat Message
- **Reference**: Based on Flask Request get_json
  - URL: https://flask.palletsprojects.com/en/3.0.x/api/#flask.Request.get_json
- **Reference**: Based on Flask jsonify
  - URL: https://flask.palletsprojects.com/en/3.0.x/api/#flask.json.jsonify

### Confirm Goal / Cancel Goal / Clear Chat
- **Reference**: Based on goal_new route pattern - uses create_user_goal from goals.py
- **Reference**: Flask Session for chat_history updates

## templates/chat.html (AI Chatbot UI)

- **Reference**: Jinja2 Template Inheritance
  - URL: https://jinja.palletsprojects.com/en/3.1.x/templates/#template-inheritance
- **Reference**: Jinja2 for loop and escape filter
  - URL: https://jinja.palletsprojects.com/en/3.1.x/templates/
- **Reference**: W3Schools HTML structure
  - URL: https://www.w3schools.com/html/default.asp
- **Reference**: Fetch API for async chat messages
  - URL: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API
- **Reference**: DOM manipulation and addEventListener
  - URL: https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model

## static/style.css – Chat Page Styles

- **Reference**: W3Schools CSS
  - URL: https://www.w3schools.com/css/default.asp
- **Reference**: Flexbox and CSS Grid
  - URL: https://www.w3schools.com/css/css3_flexbox.asp

## Database Connection (db.py)

- **Reference**: Based on MySQL Connector/Python Documentation
  - URL: https://dev.mysql.com/doc/connector-python/en/
- **Reference**: Based on Python contextlib.contextmanager
  - URL: https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager

## Summary

All code sections have been referenced to:
- **Completed Goals (goals.py, app.py, email_service.py, notifications.py, goal_view.html, goals.html, home.html, style.css)**: MySQL ALTER TABLE/UPDATE, CRUD patterns, create_notification, send_goal_completed_email, Flask variable rules, Jinja2, W3Schools
- **AI Chatbot (chatbot_service.py, app.py, chat.html, style.css)**: Google Gen AI SDK, Gemini API (quickstart, text generation, models, system instructions), Python re/json, Fetch API, Jinja2, W3Schools
1. Official documentation (Flask, MySQL, Python, Werkzeug, Gmail API)
2. Standard library patterns (datetime, decimal, contextlib)
3. Common design patterns (CRUD, form handling, authentication)
4. Best practices (email templates, notification systems, password security)
5. **Code reuse patterns within the project** (notifications.py based on user.py and goals.py functions)

These references ensure:
- Code is properly attributed
- Sources are verifiable
- Patterns follow established best practices
- All dependencies are documented
- **Code reuse within the project is clearly documented for audit purposes**
