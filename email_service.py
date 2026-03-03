"""Email integration for sending notifications via Gmail SMTP."""

from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    sender_email = os.getenv("GMAIL_SENDER_EMAIL")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender_email or not app_password:
        print(f"Email not configured. Would send to {to_email}: {subject}")
        return False

    try:
        if html_body:
            message = MIMEMultipart('alternative')
            message.attach(MIMEText(body, 'plain'))
            message.attach(MIMEText(html_body, 'html'))
        else:
            message = MIMEText(body)

        message['to'] = to_email
        message['from'] = sender_email
        message['subject'] = subject

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.sendmail(sender_email, to_email, message.as_string())

        print(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_password_reset_email(user_email: str, user_name: str, reset_url: str) -> bool:
    subject = "Password Reset Request"
    body = f"""
Hello {user_name},

You requested a password reset for your account. Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you did not request this reset, please ignore this email.

Best regards,
The ClearSave Team
    """.strip()

    html_body = f"""
    <html>
      <body>
        <h2>Password Reset Request</h2>
        <p>Hello {user_name},</p>
        <p>You requested a password reset for your account. Click the link below to reset your password:</p>
        <p><a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you did not request this reset, please ignore this email.</p>
        <p>Best regards,<br>The ClearSave Team</p>
      </body>
    </html>
    """
    return send_email(user_email, subject, body, html_body)


def send_payment_due_email(user_email: str, user_name: str, goal_name: str, amount: float, due_date: str) -> bool:
    amount_str = f"{float(amount):,.2f}"
    subject = f"Payment Due: {goal_name}"
    body = f"""
Hello {user_name},

This is a reminder that you have a payment due for your savings goal "{goal_name}".

Due Date: {due_date}
Recommended Amount: €{amount_str}

Log in to your account to record your contribution.

Best regards,
The ClearSave Team
    """.strip()

    html_body = f"""
    <html>
      <body>
        <h2>Payment Due Reminder</h2>
        <p>Hello {user_name},</p>
        <p>This is a reminder that you have a payment due for your savings goal <strong>{goal_name}</strong>.</p>
        <ul>
          <li><strong>Due Date:</strong> {due_date}</li>
          <li><strong>Recommended Amount:</strong> €{amount_str}</li>
        </ul>
        <p>Log in to your account to record your contribution.</p>
        <p>Best regards,<br>The ClearSave Team</p>
      </body>
    </html>
    """
    return send_email(user_email, subject, body, html_body)


def send_milestone_email(user_email: str, user_name: str, goal_name: str, percent: float) -> bool:
    subject = f"🎉 Milestone Reached: {goal_name}"
    body = f"""
Hello {user_name},

Congratulations! You've reached {percent:.0f}% of your "{goal_name}" savings goal.

Keep up the great work!

Best regards,
The ClearSave Team
    """.strip()

    html_body = f"""
    <html>
      <body>
        <h2>🎉 Milestone Reached!</h2>
        <p>Hello {user_name},</p>
        <p>Congratulations! You've reached <strong>{percent:.0f}%</strong> of your <strong>{goal_name}</strong> savings goal.</p>
        <p>Keep up the great work!</p>
        <p>Best regards,<br>The ClearSave Team</p>
      </body>
    </html>
    """
    return send_email(user_email, subject, body, html_body)


def send_goal_completed_email(user_email: str, user_name: str, goal_name: str) -> bool:
    subject = f"🎉 Goal Completed: {goal_name}"
    body = f"""
Hello {user_name},

Congratulations! You've completed your "{goal_name}" savings goal.

Well done! You can view it in your Previously Completed Goals section.

Best regards,
The ClearSave Team
    """.strip()

    html_body = f"""
    <html>
      <body>
        <h2>🎉 Goal Completed!</h2>
        <p>Hello {user_name},</p>
        <p>Congratulations! You've completed your <strong>{goal_name}</strong> savings goal.</p>
        <p>Well done! You can view it in your Previously Completed Goals section.</p>
        <p>Best regards,<br>The ClearSave Team</p>
      </body>
    </html>
    """
    return send_email(user_email, subject, body, html_body)