# Fix Vercel Next.js Detection Error

## The Problem

Vercel error: "No Next.js version detected"

This happens when Vercel can't find the `package.json` with Next.js, usually because:
1. Root Directory is not set correctly in Vercel
2. `vercel.json` is interfering with auto-detection

## Solution

### Step 1: Remove vercel.json (Already Done)

The root `vercel.json` file has been removed. Vercel should auto-detect Next.js when Root Directory is set correctly.

### Step 2: Set Root Directory in Vercel Dashboard

**This is the critical step:**

1. Go to: https://vercel.com/dashboard
2. Click on your **MoneyLeads** project
3. Go to **Settings** → **General**
4. Find **Root Directory** section
5. Click **Edit**
6. Enter: `dashboard` (exactly this, no slash, no quotes)
7. Click **Save**

### Step 3: Verify package.json Location

Make sure Vercel can see:
- `dashboard/package.json` exists ✅
- `dashboard/package.json` has `"next"` in dependencies ✅
- Root Directory is set to `dashboard` ✅

### Step 4: Redeploy

1. Go to **Deployments** tab
2. Click **Redeploy** on latest deployment
3. Or push a new commit to trigger redeploy

## Why This Happens

- Vercel auto-detects Next.js by looking for `package.json` with `next` dependency
- If Root Directory isn't set, it looks in the repo root (wrong location)
- `vercel.json` can sometimes interfere with auto-detection
- Setting Root Directory to `dashboard` tells Vercel where to look

## Verification

After setting Root Directory and redeploying, you should see:
- ✅ Build detects Next.js
- ✅ `npm install` runs in `dashboard/` directory
- ✅ `npm run build` succeeds
- ✅ Deployment completes successfully

## If It Still Fails

1. **Check Root Directory**:
   - Must be exactly: `dashboard`
   - Not: `./dashboard` or `/dashboard` or `dashboard/`

2. **Check package.json**:
   ```bash
   cd dashboard
   cat package.json | grep next
   ```
   Should show: `"next": "^14.0.0"`

3. **Check Vercel Logs**:
   - Look at Build Logs in deployment
   - Check if it's running commands in the right directory

4. **Try Manual Build Command** (if needed):
   - In Vercel Settings → General → Build & Development Settings
   - Build Command: `npm run build` (should auto-detect)
   - Output Directory: `.next` (should auto-detect)

