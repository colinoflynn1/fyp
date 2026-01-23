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

## Database Connection (db.py)

- **Reference**: Based on MySQL Connector/Python Documentation
  - URL: https://dev.mysql.com/doc/connector-python/en/
- **Reference**: Based on Python contextlib.contextmanager
  - URL: https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager

## Summary

All code sections have been referenced to:
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
