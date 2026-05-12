# Email Sender Setup Guide

## Prerequisites
- Python installed
- Google Account (Gmail or Workspace)

## 1. Setup Environment
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `.env` file from example:
   ```bash
   cp .env.example .env
   ```

## 2. Configure Google App Password (Required for Gmail)
If you see error `5.7.9 Application-specific password required`, follows these steps:

1. Go to your **Google Account Settings** > **Security**.
2. Make sure **2-Step Verification** is turned **ON**.
3. Under "2-Step Verification", look for **"App passwords"** (might be at the bottom or search for it in the search bar at the top).
4. Create a new App Password:
   - **App**: Select "Mail"
   - **Device**: Select "Other (Custom name)" -> Name it "Flask Email Sender"
5. Google will generate a 16-character password (e.g., `abcd efgh ijkl mnop`).
6. Copy this password (without spaces is fine, or with spaces, Google handles it).
7. Open your `.env` file.
8. Paste it into `EMAIL_PASSWORD`:
   ```
   EMAIL_PASSWORD=abcdefghijklmnop
   ```

## 3. Run Application
```bash
python app.py
```
- Go to http://127.0.0.1:5000
- Upload your Excel file.
- Click "Send Emails".
