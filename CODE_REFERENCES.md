# Code References Documentation

This document lists all references and sources for code sections in this project, organized by file and section. These references are also included as comments in the code files themselves.

## app.py

### Flask Application Setup
- **Reference**: Flask Documentation - Application Setup
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#a-minimal-application

### Password Reset Token Serialization
- **Reference**: ItsDangerous Documentation - URL Safe Timed Serializer
  - URL: https://itsdangerous.palletsprojects.com/en/2.1.x/serializer/

### Flask-Login Setup
- **Reference**: Flask-Login Documentation - Initializing the Login Manager
  - URL: https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager

### User Class (AuthUser)
- **Reference**: Flask-Login Documentation - User Class
  - URL: https://flask-login.readthedocs.io/en/latest/#flask_login.UserMixin

### User Loader
- **Reference**: Flask-Login Documentation - User Loader
  - URL: https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader

### Admin Decorator
- **Reference**: Flask Documentation - Decorators
  - URL: https://flask.palletsprojects.com/en/3.0.x/patterns/viewdecorators/
- **Reference**: Python functools.wraps
  - URL: https://docs.python.org/3/library/functools.html#functools.wraps

### Routes
- **Reference**: Flask Documentation - Routing
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#routing
- **Reference**: Flask Documentation - Template Rendering
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#rendering-templates

### HTTP Methods
- **Reference**: Flask Documentation - HTTP Methods
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#http-methods

### Login/Logout
- **Reference**: Flask-Login Documentation - Login Example
  - URL: https://flask-login.readthedocs.io/en/latest/#login-example
- **Reference**: Flask-Login Documentation - Logout
  - URL: https://flask-login.readthedocs.io/en/latest/#flask_login.logout_user

### Password Reset
- **Reference**: ItsDangerous Documentation - URL Safe Timed Serializer
  - URL: https://itsdangerous.palletsprojects.com/en/2.1.x/serializer/
- **Reference**: ItsDangerous Documentation - Loading Tokens
  - URL: https://itsdangerous.palletsprojects.com/en/2.1.x/serializer/#loading

### Form Handling
- **Reference**: Flask Documentation - Request Data
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#accessing-request-data

### Variable Rules
- **Reference**: Flask Documentation - Variable Rules
  - URL: https://flask.palletsprojects.com/en/3.0.x/quickstart/#variable-rules

### Request Referrer
- **Reference**: Flask Documentation - Request Referrer
  - URL: https://flask.palletsprojects.com/en/3.0.x/api/#flask.Request.referrer

### Decimal Parsing
- **Reference**: Python Decimal Documentation
  - URL: https://docs.python.org/3/library/decimal.html
- **Reference**: Flask Request Handling

### Date Parsing
- **Reference**: Python datetime strptime
  - URL: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior

## user.py

### Database Table Alteration
- **Reference**: MySQL Documentation - ALTER TABLE
  - URL: https://dev.mysql.com/doc/refman/8.0/en/alter-table.html
- **Pattern**: Similar to goals.py ensure_goal_tables

### CRUD Operations
- **Reference**: MySQL Documentation - INSERT
  - URL: https://dev.mysql.com/doc/refman/8.0/en/insert.html
- **Reference**: MySQL Documentation - UPDATE
  - URL: https://dev.mysql.com/doc/refman/8.0/en/update.html
- **Reference**: MySQL Documentation - DELETE
  - URL: https://dev.mysql.com/doc/refman/8.0/en/delete.html
- **Reference**: MySQL Documentation - SELECT
  - URL: https://dev.mysql.com/doc/refman/8.0/en/select.html

### Password Hashing
- **Reference**: Werkzeug Security Documentation
  - URL: https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.generate_password_hash
  - URL: https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.check_password_hash

### Dynamic SQL Construction
- **Pattern**: Adapted from Flask-SQLAlchemy patterns

## notifications.py

### Table Creation
- **Reference**: MySQL Documentation - CREATE TABLE
  - URL: https://dev.mysql.com/doc/refman/8.0/en/create-table.html
- **Reference**: Python contextlib.suppress
  - URL: https://docs.python.org/3/library/contextlib.html#contextlib.suppress

### CRUD Operations
- **Reference**: MySQL Documentation - INSERT
  - URL: https://dev.mysql.com/doc/refman/8.0/en/insert.html
- **Reference**: MySQL Documentation - SELECT with WHERE
  - URL: https://dev.mysql.com/doc/refman/8.0/en/select.html#select-where
- **Reference**: MySQL Documentation - UPDATE
  - URL: https://dev.mysql.com/doc/refman/8.0/en/update.html
- **Pattern**: Adapted from user.py and goals.py CRUD patterns

### Payment Due Notifications
- **Reference**: Python datetime Documentation - Date Arithmetic
  - URL: https://docs.python.org/3/library/datetime.html#datetime.date
- **Pattern**: Based on goals.py build_progress logic

### Milestone Notifications
- **Reference**: Python Documentation - Percentage Calculations
  - URL: https://docs.python.org/3/library/functions.html#round
- **Pattern**: Based on goals.py build_progress milestone detection
- **Pattern**: Standard progress tracking patterns

## email_service.py

### Gmail API Authentication
- **Reference**: Gmail API Python Quickstart
  - URL: https://developers.google.com/gmail/api/quickstart/python
- **Reference**: Google Auth Library Documentation
  - URL: https://google-auth.readthedocs.io/

### Email Sending
- **Reference**: Gmail API Python Client Library - Sending Messages
  - URL: https://developers.google.com/gmail/api/guides/sending
- **Reference**: Python email.mime Documentation
  - URL: https://docs.python.org/3/library/email.mime.html
- **Reference**: Python base64 Documentation
  - URL: https://docs.python.org/3/library/base64.html

### Email Templates
- **Pattern**: Standard password reset email implementations
- **Pattern**: Common notification email formats
- **Pattern**: HTML email best practices
- **Pattern**: Gamification patterns for milestone emails

## goals.py

(References already exist in goals.py - see file comments)

### Decimal Handling
- **Reference**: Python Decimal Documentation
  - URL: https://docs.python.org/3/library/decimal.html

### MySQL Table Creation
- **Reference**: Official MySQL Documentation

### CRUD Patterns
- **Reference**: CRUD pattern adapted from user.py
- **Reference**: MySQL Documentation

## Database Connection (db.py)

(References should be in db.py file)

- **Reference**: MySQL Connector/Python Documentation
- **Reference**: Python contextlib.contextmanager
  - URL: https://docs.python.org/3/library/contextlib.html#contextlib.contextmanager

## Summary

All code sections have been referenced to:
1. Official documentation (Flask, MySQL, Python, Werkzeug, Gmail API)
2. Standard library patterns (datetime, decimal, contextlib)
3. Common design patterns (CRUD, form handling, authentication)
4. Best practices (email templates, notification systems, password security)

These references ensure:
- Code is properly attributed
- Sources are verifiable
- Patterns follow established best practices
- All dependencies are documented
