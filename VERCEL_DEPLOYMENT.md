# Vercel Deployment Guide for Email Marketing Application

## Prerequisites
- Vercel account (free tier works)
- Supabase account with configured project
- GitHub repository (for deployment)

## Step 1: Prepare Your Repository

1. **Ensure .gitignore is properly configured**
   ```bash
   git status
   # Make sure .env is NOT listed
   ```

2. **Commit all changes**
   ```bash
   git add .
   git commit -m "Production-ready Supabase integration"
   git push origin main
   ```

## Step 2: Deploy to Vercel

### Option A: Via Vercel Dashboard (Recommended)

1. Go to [https://vercel.com/](https://vercel.com/)
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure build settings:
   - **Framework Preset**: None (or Other)
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave empty)
   - **Install Command**: `pip install -r requirements.txt`

### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd f:\autoemailsending_marketing
vercel

# Follow the prompts
```

## Step 3: Configure Environment Variables

In Vercel Dashboard → Your Project → Settings → Environment Variables, add:

### Microsoft Azure/Graph API
```
TENANT_ID = [YOUR_TENANT_ID]
CLIENT_ID = [YOUR_CLIENT_ID]
CLIENT_SECRET = [YOUR_CLIENT_SECRET]
SENDER_EMAIL = support@applywizz.com
```

### Supabase Configuration
```
SUPABASE_URL = [YOUR_SUPABASE_URL]
SUPABASE_KEY = [YOUR_SUPABASE_ANON_KEY]
SUPABASE_SERVICE_KEY = [YOUR_SUPABASE_SERVICE_ROLE_KEY]
SUPABASE_BUCKET_NAME = email-attachments
```

### Flask Secret Key
```
SECRET_KEY = your_random_secret_key_here_change_in_production
```

**IMPORTANT**: Set environment variables for "Production", "Preview", and "Development" environments

## Step 4: Redeploy

After adding environment variables:
1. Go to Deployments tab
2. Click "..." on the latest deployment
3. Click "Redeploy"

OR

```bash
vercel --prod
```

## Step 5: Verify Deployment

1. Visit your Vercel URL (e.g., `https://your-app.vercel.app`)
2. Test file upload:
   - Upload an Excel file
   - Check Supabase Storage to confirm upload
   - Check `uploaded_files` table for metadata
3. Test email sending:
   - Send test emails
   - Check `email_logs` table for records
4. Test logs viewing:
   - Navigate to `/logs`
   - Click on a batch to view details

## Troubleshooting

### Issue: "Application not configured"
- **Solution**: Check that all environment variables are set in Vercel
- Redeploy after adding variables

### Issue: "Error loading files from database"
- **Solution**: Verify Supabase credentials are correct
- Check Supabase project is active and tables exist

### Issue: 500 Internal Server Error
- **Solution**: Check Vercel function logs:
  - Go to Deployments → Click deployment → Functions tab
  - Look for error messages

### Issue: File upload fails
- **Solution**: 
  - Verify storage bucket `email-attachments` exists in Supabase
  - Check bucket permissions allow authenticated uploads

## Production Checklist

- [ ] All Supabase tables created (`uploaded_files`, `email_logs`, `upload_logs`)
- [ ] Storage bucket `email-attachments` created and configured
- [ ] All environment variables set in Vercel
- [ ] `.env` file NOT committed to repository
- [ ] Application deployed successfully
- [ ] File upload tested and working
- [ ] Email sending tested and working
- [ ] Logs viewing tested and working
- [ ] Data persists after redeployment

## Performance Optimization

### Enable Caching (Optional)
Add to `vercel.json`:
```json
{
  "headers": [
    {
      "source": "/static/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

### Monitor Usage
- Check Vercel analytics for performance metrics
- Monitor Supabase dashboard for storage/database usage
- Set up alerts for quota limits

## Scaling Considerations

- **Vercel Free Tier**: 100 GB bandwidth/month
-  **Supabase Free Tier**: 500 MB database, 1 GB storage
- Upgrade plans as needed based on usage

## Security Recommendations

1. **Rotate Service Role Key**: Don't use demo keys in production
2. **Enable RLS**: Configure row-level security in Supabase
3. **Use HTTPS**: Vercel provides this by default
4. **Add User Authentication**: Consider adding login system
5. **Rate Limiting**: Implement rate limiting for uploads

## Support

- Vercel Docs: https://vercel.com/docs
- Supabase Docs: https://supabase.com/docs
- Flask Deployment: https://flask.palletsprojects.com/en/latest/deploying/
