# Vercel Deployment Fix

## Issue
404 error on `money-leads.vercel.app` - This happens when Vercel doesn't know the root directory.

## Solution

### Option 1: Configure Root Directory in Vercel Dashboard (Recommended)

1. Go to your Vercel project settings
2. Navigate to **Settings** → **General**
3. Find **Root Directory** section
4. Set it to: `dashboard`
5. Click **Save**
6. Redeploy your project

### Option 2: Move Dashboard to Root

If you prefer to have the dashboard at the root:

```bash
# This would require restructuring, not recommended
```

### Option 3: Use vercel.json (Already Created)

I've created `vercel.json` files that should help. Make sure:

1. **Root `vercel.json`** points to dashboard directory
2. **Dashboard `vercel.json`** has Next.js config

## Environment Variables

Make sure these are set in Vercel:

1. Go to **Settings** → **Environment Variables**
2. Add:
   - `NEXT_PUBLIC_SUPABASE_URL` = `https://mdyayczcvpkbrdpdtkjb.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = (your anon key)

## Steps to Fix

1. **Update Vercel Project Settings:**
   - Root Directory: `dashboard`
   - Framework Preset: `Next.js`
   - Build Command: `npm run build` (or leave default)
   - Output Directory: `.next` (or leave default)

2. **Verify Environment Variables:**
   - Check that both Supabase variables are set
   - Make sure they're available for Production, Preview, and Development

3. **Redeploy:**
   - Go to **Deployments** tab
   - Click **Redeploy** on the latest deployment
   - Or push a new commit to trigger redeploy

## Testing Locally

Before deploying, test locally:

```bash
cd dashboard
npm install
npm run build
npm start
```

Visit `http://localhost:3000` to verify it works.

## Common Issues

### 404 on All Routes
- **Cause**: Root directory not set correctly
- **Fix**: Set Root Directory to `dashboard` in Vercel settings

### Build Fails
- **Cause**: Missing dependencies or TypeScript errors
- **Fix**: Run `npm install` and `npm run build` locally to check for errors

### Environment Variables Not Working
- **Cause**: Variables not set or wrong prefix
- **Fix**: Make sure variables start with `NEXT_PUBLIC_` for client-side access

### API Routes Return 404
- **Cause**: Next.js API routes not properly configured
- **Fix**: Ensure `app/api/` directory structure is correct

## After Fix

Once deployed correctly, you should see:
- ✅ Dashboard loads at `money-leads.vercel.app`
- ✅ Can create jobs
- ✅ Can upload videos
- ✅ Real-time updates work

