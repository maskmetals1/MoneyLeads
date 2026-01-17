# Vercel Setup Instructions

## Important: Root Directory Must Be Set in Vercel Dashboard

The `rootDirectory` property is **NOT** valid in `vercel.json`. You must set it in Vercel's project settings instead.

## Step-by-Step Setup

### 1. Set Root Directory in Vercel Dashboard

1. Go to https://vercel.com/dashboard
2. Click on your **MoneyLeads** project
3. Go to **Settings** → **General**
4. Scroll down to **Root Directory**
5. Click **Edit**
6. Enter: `dashboard`
7. Click **Save**

**This is the most important step!** Without this, Vercel won't know where your Next.js app is.

### 2. Set Environment Variables

1. In the same project, go to **Settings** → **Environment Variables**
2. Add these two variables:

   **Variable 1:**
   - Name: `NEXT_PUBLIC_SUPABASE_URL`
   - Value: `https://mdyayczcvpkbrdpdtkjb.supabase.co`
   - Environments: ✅ Production, ✅ Preview, ✅ Development

   **Variable 2:**
   - Name: `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - Value: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1keWF5Y3pjdnBrYnJkcGR0a2piIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg2ODI1MDAsImV4cCI6MjA4NDI1ODUwMH0.nS-RpFyLgNPAxg4z23CwWu0jrQQm9wHVICTwTsWYOxU`
   - Environments: ✅ Production, ✅ Preview, ✅ Development

3. Click **Save** for each variable

### 3. Redeploy

1. Go to **Deployments** tab
2. Click the **⋯** (three dots) on the latest deployment
3. Click **Redeploy**
4. Wait for deployment to complete

## What the vercel.json Does

The `vercel.json` file in the root tells Vercel:
- To run build commands in the `dashboard` directory
- Where the output is located
- What framework to use

But the **Root Directory** setting in Vercel Dashboard is what actually tells Vercel where your app lives.

## Verification

After redeploying, you should see:
- ✅ Build succeeds (no errors)
- ✅ Deployment status: "Ready"
- ✅ Site loads at `money-leads.vercel.app`
- ✅ Dashboard UI appears correctly

## Troubleshooting

### Build Still Fails
- Check **Build Logs** in the deployment details
- Make sure `dashboard/package.json` exists
- Verify all dependencies are listed in `package.json`

### Environment Variables Not Working
- Make sure variable names are **exact** (case-sensitive)
- Check that they're enabled for **Production** environment
- Variables must start with `NEXT_PUBLIC_` to be accessible in the browser

### 404 Errors After Deployment
- Verify Root Directory is set to `dashboard` (not `./dashboard` or `/dashboard`)
- Check that `dashboard/app/page.tsx` exists
- Ensure Next.js is properly configured

## Next Steps

Once deployed successfully:
1. Test creating a job
2. Test uploading a video
3. Verify real-time updates work
4. Check that Supabase connection is working

