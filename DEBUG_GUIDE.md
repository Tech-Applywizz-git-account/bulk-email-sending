# 🔍 Debugging Production Deployment Issues

## What We Added

I've added **comprehensive logging** throughout your application to diagnose what's happening in your Vercel deployment. The logs will now show:

### 1. **Environment Variable Loading** (`app.py` startup)
- ✅ Which environment variables are loaded
- ✅ Python version
- ✅ All credential checks (TENANT_ID, CLIENT_ID, etc.)
- ✅ Supabase configuration status

### 2. **Supabase Initialization** (`supabase_service.py`)
- ✅ Supabase URL and Service Key status
- ✅ Bucket name configuration
- ✅ Client creation success/failure
- ✅ Detailed error messages if initialization fails

### 3. **File Upload Process**
- ✅ Supabase enabled status
- ✅ Storage upload progress
- ✅ Database insertion status
- ✅ Full error tracebacks if upload fails

### 4. **Email Sending Process**
- ✅ Azure credential verification
- ✅ Token acquisition status
- ✅ Email processing progress (shows first 3 and last email)
- ✅ Supabase logging status for each email
- ✅ Detailed error messages

---

## How to View Logs in Vercel

### Step 1: Go to Your Vercel Dashboard
1. Visit: https://vercel.com/dashboard
2. Click on your project: **bulk_email_sending_marketing_UI_best**

### Step 2: View Real-Time Logs
1. Click on the **"Deployments"** tab (or latest deployment)
2. Click on **"Functions"** or **"Runtime Logs"**
3. You'll see all the `print()` statements with emojis like:
   ```
   🚀 FLASK APPLICATION INITIALIZATION
   ============================================================
   Python version: 3.x.x
   Environment check:
     SECRET_KEY loaded: True/False
     TENANT_ID loaded: True/False
     ...
   ```

### Step 3: Check for Missing Variables
Look for these key indicators:

#### ✅ **Good Signs:**
```
SUPABASE_URL loaded: True
   URL: https://[YOUR_PROJECT_ID].supabase.co
SUPABASE_SERVICE_KEY loaded: True
   Key length: 200+ chars
✅ Supabase client initialized successfully
```

#### ❌ **Problem Signs:**
```
❌ SUPABASE_URL is missing!
❌ SUPABASE_SERVICE_KEY is missing!
⚠️ WARNING: Supabase credentials not found in environment variables
```

---

## Common Issues and Solutions

### Issue 1: Environment Variables Not Loaded
**Symptom:**
```
TENANT_ID loaded: False
SUPABASE_SERVICE_KEY loaded: False
```

**Solution:**
1. Go to Vercel → Settings → Environment Variables
2. Add each variable with the **exact name** from your `.env` file
3. Make sure to select: ✅ Production, ✅ Preview, ✅ Development
4. **Redeploy** after adding variables

---

### Issue 2: Wrong Variable Names
**Symptom:**
```
⚠️ WARNING: Supabase credentials not found
```

**Check:** Your Vercel environment variables must match exactly:
- ✅ `SUPABASE_SERVICE_KEY` (correct)
- ❌ `SUPABASE_KEY` (wrong - this is for frontend)
- ❌ `SUPABASE_SUPPORT_KEY` (wrong - doesn't exist in code)

---

### Issue 3: Duplicate Data (The Original Problem)
**Possible Causes:**

1. **Multiple Vercel Deployments Writing to Same DB**
   - Check if you have multiple preview/production branches
   - All deployments share the same Supabase database
   - Solution: Use different Supabase projects for preview vs production

2. **User Clicking Send Button Multiple Times**
   - Add frontend button disable logic
   - Show loading state during send

3. **Azure API Retries**
   - Check Azure logs for duplicate sends
   - Email might be sent but API returns error, causing retry

---

## Required Environment Variables Checklist

Make sure ALL of these are in Vercel:

| Variable Name | Where to Get It | Status |
|--------------|----------------|--------|
| `SECRET_KEY` | Generate with `python -c "import secrets; print(secrets.token_hex(32))"` | |
| `TENANT_ID` | Azure Portal → Azure AD → App Registration | |
| `CLIENT_ID` | Azure Portal → Azure AD → App Registration | |
| `CLIENT_SECRET` | Azure Portal → Azure AD → Certificates & Secrets | |
| `SENDER_EMAIL` | Your Microsoft 365 email with Graph API permission | |
| `SUPABASE_URL` | Supabase Dashboard → Project Settings → API | |
| `SUPABASE_SERVICE_KEY` | Supabase Dashboard → Project Settings → API (service_role key) | |
| `SUPABASE_BUCKET_NAME` | Usually `email-attachments` | |

---

## Next Steps

1. **Push Code to GitHub** ✅ (Done - just pushed)
2. **Wait for Vercel Auto-Deploy** (2-3 minutes)
3. **Check Vercel Function Logs:**
   - Go to your deployment → Functions → Runtime Logs
   - Look for the initialization messages
4. **Share the logs** with me if you see any errors
5. **Verify Environment Variables** in Vercel Settings

---

## What to Look For in Logs

When you view the Vercel logs, send me a screenshot or copy-paste of:

1. The **initialization section** (🚀 FLASK APPLICATION INITIALIZATION)
2. The **Supabase initialization** (🔍 SUPABASE SERVICE INITIALIZATION)
3. Any **error messages** marked with ❌
4. The section where the issue occurs (upload/send emails)

With these detailed logs, we'll be able to pinpoint **exactly** what's wrong! 🎯
