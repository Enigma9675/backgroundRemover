# Railway Deployment Guide for Background Removal Service

This guide will help you deploy the Python rembg background removal service to Railway.

## Prerequisites

- GitHub account
- Railway account (sign up at https://railway.app - free tier available)

## Step 1: Create a New GitHub Repository for Python Service

You can either:
- **Option A**: Create a separate repo for just the Python service
- **Option B**: Deploy from the `python-functions` folder in your main repo

### Option A: Separate Repository (Recommended)

1. Create a new GitHub repository called `bg-removal-service`
2. Copy these files to the new repo:
   - `main.py`
   - `requirements.txt`
   - `Procfile`
   - `railway.json`
   - `README.md`

3. Push to GitHub:
```bash
cd python-functions
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/bg-removal-service.git
git push -u origin main
```

### Option B: Deploy from Subfolder

If you want to keep it in your main repo, Railway can deploy from a specific folder.

## Step 2: Deploy to Railway

1. **Go to Railway**: Visit https://railway.app

2. **Sign in with GitHub**

3. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository (either the new one or your main repo)

4. **Configure Service**:
   - If using Option B (subfolder), set the **Root Directory** to `python-functions`
   - Railway will auto-detect Python and install dependencies

5. **Wait for Deployment**:
   - First deployment takes 3-5 minutes (downloading rembg models)
   - Watch the logs for any errors

6. **Get Your Service URL**:
   - Once deployed, Railway will give you a public URL
   - It will look like: `https://your-service.up.railway.app`
   - Click on "Settings" → "Generate Domain" if no URL exists

## Step 3: Test Your Deployment

Test the health endpoint:
```bash
curl https://your-service.up.railway.app/
```

You should see:
```json
{
  "status": "ok",
  "service": "background-removal",
  "rembg_available": true
}
```

## Step 4: Configure Your Frontend

### For Local Development:

Create/update `.env.local` file in your main project:
```env
VITE_BG_REMOVAL_URL=https://your-service.up.railway.app/remove-bg
```

### For Vercel Production:

1. Go to your Vercel project settings
2. Navigate to "Environment Variables"
3. Add a new variable:
   - **Name**: `VITE_BG_REMOVAL_URL`
   - **Value**: `https://your-service.up.railway.app/remove-bg`
   - **Environment**: Production, Preview, Development (select all)
4. Redeploy your Vercel project

## Step 5: Verify Everything Works

1. **Restart your development server**:
```bash
npm run dev
```

2. **Test background removal** in your app:
   - Upload an image
   - Click remove background
   - Should now use Railway service

## Railway Free Tier Limits

- **500 hours/month** of usage (plenty for development)
- **512 MB RAM** (sufficient for rembg)
- **1 GB disk** (enough for models)
- **No credit card required** for starter plan

## Monitoring

- Check Railway dashboard for:
  - Deployment logs
  - Resource usage
  - Request metrics
  - Errors

## Troubleshooting

### Deployment fails
- Check Railway logs for Python errors
- Verify all files are present
- Ensure `requirements.txt` is correct

### Background removal not working
- Verify environment variable is set correctly
- Check browser console for CORS errors
- Verify Railway service is running (check dashboard)

### Slow first request
- First request after idle period takes longer (cold start)
- Subsequent requests are fast
- This is normal for free tier

## Cost Optimization

If you exceed free tier:
- Railway Pro: $5/month for more resources
- Still much cheaper than paid remove.bg API

## Alternative: Run Locally for Development

If you want to run the Python service locally:

```bash
cd python-functions
pip install -r requirements.txt
python main.py
```

Then use:
```env
VITE_BG_REMOVAL_URL=http://localhost:8080/remove-bg
```

## Support

For Railway-specific issues:
- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app

For rembg issues:
- GitHub: https://github.com/danielgatis/rembg
