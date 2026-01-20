# Gmail API Setup Guide

This application uses the Gmail API to send email notifications for password resets, payment reminders, and milestone achievements.

## Prerequisites

1. A Google account with access to Google Cloud Console
2. Python packages installed (see `requirements.txt`)

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" (unless you have a Google Workspace account)
   - Fill in the required fields (app name, user support email, etc.)
   - Add your email as a test user
4. Create OAuth client ID:
   - Application type: "Desktop app"
   - Name: "FYP Savings App" (or any name you prefer)
   - Click "Create"
5. Download the credentials JSON file
6. Save it as `credentials.json` in the project root directory

### 4. Configure Environment Variables

Add these to your `.env` file:

```env
# Gmail API Configuration
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
GMAIL_SENDER_EMAIL=your-email@gmail.com
```

**Note:** `GMAIL_SENDER_EMAIL` should be the email address associated with your Google account (the one you're sending from).

### 5. First-Time Authorization

When you first run the application and try to send an email:

1. A browser window will open for Google OAuth authorization
2. Sign in with your Google account
3. Grant permissions to the application
4. A `token.json` file will be created automatically (this stores your access token)

### 6. Token Refresh

The token will automatically refresh when it expires. If you encounter issues:

- Delete `token.json` and re-authenticate
- Check that the OAuth consent screen is properly configured
- Ensure your email is added as a test user (if the app is in testing mode)

## Troubleshooting

### "Email service not available"
- Check that `credentials.json` exists in the project root
- Verify the file name matches `GMAIL_CREDENTIALS_PATH` in `.env`

### "Access denied" or OAuth errors
- Make sure you've added your email as a test user in the OAuth consent screen
- Check that the Gmail API is enabled in your Google Cloud project

### Token expires frequently
- The token should auto-refresh, but if issues persist:
  - Delete `token.json` and re-authenticate
  - Ensure `google-auth-httplib2` is installed

## Email Notifications

Once configured, the app will send:
- **Password Reset Emails**: When users request a password reset
- **Payment Due Reminders**: When a savings goal payment is due (if email notifications are enabled)
- **Milestone Achievements**: When users reach 25%, 50%, 75%, or 100% of a goal (if email notifications are enabled)

## Note on Dashboard Notifications

Dashboard notifications work immediately without any API setup - they're stored in the database and displayed when users visit the website. They work perfectly as a website-based feature.
