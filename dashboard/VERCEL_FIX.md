# Fix Vercel 404 Error

## Quick Fix Steps

### 1. Verify Root Directory in Vercel

1. Go to your Vercel project: https://vercel.com/dashboard
2. Click on your project (money-leads)
3. Go to **Settings** → **General**
4. Scroll to **Root Directory**
5. **IMPORTANT**: Set it to `dashboard` (not the root folder)
6. Click **Save**

### 2. Verify Build Settings

In Vercel Settings → General:
- **Framework Preset**: Next.js
- **Root Directory**: `dashboard`
- **Build Command**: `npm run build` (or leave empty - auto-detected)
- **Output Directory**: `.next` (or leave empty - auto-detected)

### 3. Redeploy

After changing Root Directory:
1. Go to **Deployments** tab
2. Click the **3 dots** on the latest deployment
3. Click **Redeploy**

Or push a new commit to trigger a new deployment.

### 4. Verify Environment Variables

In Vercel Settings → Environment Variables, make sure you have:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### 5. Check Build Logs

If still getting 404:
1. Go to **Deployments** tab
2. Click on the latest deployment
3. Check **Build Logs** for errors
4. Look for:
   - "No Next.js version detected" → Check package.json has "next"
   - "Cannot find module" → Check dependencies are installed
   - Build errors → Fix them

## Common Issues

### Issue: "No Next.js version detected"
**Fix**: Make sure `package.json` in `dashboard/` folder has `"next"` in dependencies

### Issue: Root Directory not set
**Fix**: Set Root Directory to `dashboard` in Vercel project settings

### Issue: Build succeeds but 404
**Fix**: 
1. Check `vercel.json` exists in `dashboard/` folder (it does now)
2. Verify `next.config.js` is correct
3. Make sure `app/` folder structure is correct

### Issue: Environment variables missing
**Fix**: Add them in Vercel Settings → Environment Variables

## Verification

After fixing, your site should:
1. Load at `money-leads.vercel.app`
2. Show the dashboard with jobs
3. Have working API routes (`/api/job-action`, `/api/worker-status`)

## Current Configuration

✅ `vercel.json` created in `dashboard/` folder
✅ `next.config.js` configured correctly
✅ `package.json` has Next.js dependency
✅ API routes in `app/api/` folder

The issue is most likely the **Root Directory** not being set to `dashboard` in Vercel settings.

