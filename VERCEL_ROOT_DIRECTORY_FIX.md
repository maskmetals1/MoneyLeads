# Critical: Vercel Root Directory Must Be Set

## The Problem

You're still seeing 404 errors because **Vercel doesn't know where your Next.js app is**.

## The Solution (REQUIRED)

### Step 1: Go to Vercel Dashboard

1. Open: https://vercel.com/dashboard
2. Click on your **MoneyLeads** project

### Step 2: Set Root Directory

1. Go to **Settings** → **General**
2. Scroll to **Root Directory** section
3. Click **Edit**
4. **Type exactly**: `dashboard`
   - NOT: `./dashboard`
   - NOT: `/dashboard`
   - NOT: `dashboard/`
   - Just: `dashboard`
5. Click **Save**

### Step 3: Verify Build Settings

While in Settings → General, check **Build & Development Settings**:

- **Framework Preset**: Should show "Next.js" (auto-detected)
- **Build Command**: `npm run build` (or leave default)
- **Output Directory**: `.next` (or leave default)
- **Install Command**: `npm install` (or leave default)

### Step 4: Check Environment Variables

Go to **Settings** → **Environment Variables**:

Make sure these are set:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

Both must be enabled for **Production**, **Preview**, and **Development**.

### Step 5: Redeploy

1. Go to **Deployments** tab
2. Click **⋯** (three dots) on latest deployment
3. Click **Redeploy**
4. Wait for build to complete

## Why This Is Critical

Without Root Directory set:
- ❌ Vercel looks in repo root for `package.json`
- ❌ Can't find Next.js app
- ❌ Returns 404 error
- ❌ Build might succeed but site doesn't work

With Root Directory set to `dashboard`:
- ✅ Vercel looks in `dashboard/` folder
- ✅ Finds `dashboard/package.json` with Next.js
- ✅ Builds correctly
- ✅ Site works!

## Verification

After setting Root Directory and redeploying:

1. **Check Build Logs**:
   - Should see: "Installing dependencies..."
   - Should see: "Building..."
   - Should see: "✓ Compiled successfully"

2. **Check Deployment**:
   - Status should be "Ready" (green)
   - Should NOT be "Error" or "404"

3. **Visit Site**:
   - Go to `money-leads.vercel.app`
   - Should see dashboard (not 404)

## If Still Not Working

1. **Delete and Re-import Project**:
   - Delete project in Vercel
   - Re-import from GitHub
   - Set Root Directory during import

2. **Check File Structure**:
   Make sure GitHub has:
   ```
   dashboard/
     ├── app/
     │   ├── page.tsx
     │   ├── layout.tsx
     │   └── ...
     ├── package.json
     └── next.config.js
   ```

3. **Test Locally First**:
   ```bash
   cd dashboard
   npm install
   npm run build
   npm start
   ```
   If it works locally at `localhost:3000`, it will work on Vercel once Root Directory is set.

## Summary

**THE MOST IMPORTANT STEP**: Set Root Directory to `dashboard` in Vercel Settings.

Without this, nothing else will work!

