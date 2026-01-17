# Quick Fix for Vercel 404 Error

## The Problem
Vercel is showing a 404 because it doesn't know your Next.js app is in the `dashboard` folder.

## Quick Fix (2 minutes)

### Step 1: Update Vercel Project Settings

1. Go to https://vercel.com/dashboard
2. Click on your **MoneyLeads** project
3. Go to **Settings** → **General**
4. Scroll to **Root Directory**
5. Click **Edit**
6. Enter: `dashboard`
7. Click **Save**

### Step 2: Verify Environment Variables

1. Still in Settings, go to **Environment Variables**
2. Make sure these are set:
   - `NEXT_PUBLIC_SUPABASE_URL` = `https://mdyayczcvpkbrdpdtkjb.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` = (your anon key from Supabase)

### Step 3: Redeploy

1. Go to **Deployments** tab
2. Click the **⋯** (three dots) on the latest deployment
3. Click **Redeploy**
4. Wait for deployment to complete

## That's It!

After redeploying, your site should work at `money-leads.vercel.app`

## If It Still Doesn't Work

### Check Build Logs
1. Go to **Deployments** tab
2. Click on the latest deployment
3. Check the **Build Logs** for errors

### Common Issues:

**"Cannot find module"**
- Make sure `dashboard/package.json` exists
- Vercel should auto-detect Next.js

**"Environment variables missing"**
- Double-check variable names (case-sensitive)
- Make sure they're set for **Production**

**"Build failed"**
- Check if TypeScript errors exist
- Run `cd dashboard && npm run build` locally first

## Test Locally First

Before redeploying, test locally:

```bash
cd dashboard
npm install
npm run build
npm start
```

Visit `http://localhost:3000` - if it works locally, it will work on Vercel!

