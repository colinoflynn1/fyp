"""Gmail API integration for sending email notifications."""

from __future__ import annotations

import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv

# Try to import Gmail API, but make it optional if not installed
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    # Create dummy classes for type hints
    class Request: pass
    class Credentials: pass
    class InstalledAppFlow: pass
    class HttpError: pass

load_dotenv()

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def get_gmail_service():
    """
    Get authenticated Gmail service instance.
    
    Reference: Gmail API Python Quickstart [NEW]
    https://developers.google.com/gmail/api/quickstart/python
    
    Returns:
        Gmail service instance or None if authentication fails
    """
    if not GMAIL_AVAILABLE:
        print("Warning: Gmail API libraries not installed. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return None
    
    creds = None
    token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")
    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    
    # Check if token.json exists (for existing auth)
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"Error loading credentials: {e}")
    
    # If there are no valid credentials, try to get them
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                creds = None
        
        if not creds:
            if not os.path.exists(credentials_path):
                print(f"Warning: {credentials_path} not found. Email sending will be disabled.")
                print("To enable email notifications:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a project and enable Gmail API")
                print("3. Create OAuth 2.0 credentials")
                print("4. Download credentials.json to the project root")
                return None
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"Error during OAuth flow: {e}")
                return None
        
        # Save credentials for next run
        try:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            print(f"Warning: Could not save token: {e}")
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building Gmail service: {e}")
        return None


# Reference: Gmail API Python Client Library - Sending Messages [NEW]
# https://developers.google.com/gmail/api/guides/sending
# Python email.mime documentation for MIME message construction
# https://docs.python.org/3/library/email.mime.html
# Base64 encoding for email messages: https://docs.python.org/3/library/base64.html
def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """
    Send an email using Gmail API.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    service = get_gmail_service()
    if not service:
        print(f"Email service not available. Would send to {to_email}: {subject}")
        return False
    
    sender_email = os.getenv("GMAIL_SENDER_EMAIL")
    if not sender_email:
        print("Warning: GMAIL_SENDER_EMAIL not set in .env. Using default sender.")
        sender_email = os.getenv("GMAIL_USER") or "noreply@example.com"
    
    try:
        # Create message
        if html_body:
            message = MIMEMultipart('alternative')
            message.attach(MIMEText(body, 'plain'))
            message.attach(MIMEText(html_body, 'html'))
        else:
            message = MIMEText(body)
        
        message['to'] = to_email
        message['from'] = sender_email
        message['subject'] = subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send message
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"Email sent successfully. Message ID: {send_message.get('id')}")
        return True
        
    except HttpError as error:
        print(f"An error occurred while sending email: {error}")
        return False
    except Exception as e:
        print(f"Unexpected error sending email: {e}")
        return False


# Reference: Standard email template pattern for password reset [NEW]
# Adapted from common password reset email implementations
# HTML email formatting based on email best practices
def send_password_reset_email(user_email: str, user_name: str, reset_url: str) -> bool:
    """
    Send password reset email.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        reset_url: Password reset URL
    
    Returns:
        True if email was sent successfully
    """
    subject = "Password Reset Request"
    body = f"""
Hello {user_name},

You requested a password reset for your account. Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you did not request this reset, please ignore this email.

Best regards,
The FYP Team
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
        <p>Best regards,<br>The FYP Team</p>
      </body>
    </html>
    """
    
    return send_email(user_email, subject, body, html_body)


# Reference: Notification email template pattern [NEW]
# Standard reminder email format adapted from common notification systems
# Email formatting follows HTML email best practices
def send_payment_due_email(user_email: str, user_name: str, goal_name: str, amount: float, due_date: str) -> bool:
    """
    Send payment due notification email.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        goal_name: Name of the goal
        amount: Recommended contribution amount
        due_date: Due date as string
    
    Returns:
        True if email was sent successfully
    """
    subject = f"Payment Due: {goal_name}"
    body = f"""
Hello {user_name},

This is a reminder that you have a payment due for your savings goal "{goal_name}".

Due Date: {due_date}
Recommended Amount: €{amount:.2f}

Log in to your account to record your contribution.

Best regards,
The FYP Team
    """.strip()
    
    html_body = f"""
    <html>
      <body>
        <h2>Payment Due Reminder</h2>
        <p>Hello {user_name},</p>
        <p>This is a reminder that you have a payment due for your savings goal <strong>{goal_name}</strong>.</p>
        <ul>
          <li><strong>Due Date:</strong> {due_date}</li>
          <li><strong>Recommended Amount:</strong> €{amount:.2f}</li>
        </ul>
        <p>Log in to your account to record your contribution.</p>
        <p>Best regards,<br>The FYP Team</p>
      </body>
    </html>
    """
    
    return send_email(user_email, subject, body, html_body)


# Reference: Achievement notification email pattern [NEW]
# Milestone celebration email format adapted from gamification patterns
# HTML email formatting for milestone notifications
def send_milestone_email(user_email: str, user_name: str, goal_name: str, percent: float) -> bool:
    """
    Send milestone achievement email.
    
    Args:
        user_email: User's email address
        user_name: User's full name
        goal_name: Name of the goal
        percent: Percentage achieved
    
    Returns:
        True if email was sent successfully
    """
    subject = f"🎉 Milestone Reached: {goal_name}"
    body = f"""
Hello {user_name},

Congratulations! You've reached {percent:.0f}% of your "{goal_name}" savings goal.

Keep up the great work! You're making excellent progress toward your target.

Best regards,
The FYP Team
    """.strip()
    
    html_body = f"""
    <html>
      <body>
        <h2>🎉 Milestone Reached!</h2>
        <p>Hello {user_name},</p>
        <p>Congratulations! You've reached <strong>{percent:.0f}%</strong> of your <strong>{goal_name}</strong> savings goal.</p>
        <p>Keep up the great work! You're making excellent progress toward your target.</p>
        <p>Best regards,<br>The FYP Team</p>
      </body>
    </html>
    """
    
    return send_email(user_email, subject, body, html_body)
