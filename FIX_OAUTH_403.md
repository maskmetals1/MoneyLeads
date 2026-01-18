# Fix OAuth 403 Error: Access Denied

## The Problem

You're seeing: **"Access blocked: MoneyLeads has not completed the Google verification process"**

This happens because your OAuth app is in **Testing** mode and your email isn't added as a test user.

## Quick Fix (2 minutes)

### Step 1: Go to OAuth Consent Screen

1. Open: https://console.cloud.google.com/apis/credentials/consent
2. Make sure your project **moneyleadyt** is selected
3. You should see the OAuth consent screen configuration

### Step 2: Add Test Users

1. Scroll down to **"Test users"** section
2. Click **"+ ADD USERS"**
3. Add your email: **maskmetals1@gmail.com**
4. Click **"ADD"**
5. Click **"SAVE"** at the bottom of the page

### Step 3: Try Again

1. Go back to your terminal
2. Run the test command again:
   ```bash
   python3 -c "from youtube_uploader import YouTubeUploader; u = YouTubeUploader(); print('✅ Ready!')"
   ```
3. It should now work!

## Alternative: Publish the App (Not Recommended Yet)

If you want to allow any user to access (not just test users):

1. Go to OAuth Consent Screen
2. Click **"PUBLISH APP"**
3. **Warning**: This requires Google verification which can take days/weeks
4. For now, just add test users (much faster!)

## Why This Happens

- Google requires OAuth apps to be verified before public use
- During development, apps are in "Testing" mode
- Only explicitly added test users can access testing apps
- This is a security feature to prevent unauthorized access

## After Adding Test User

Once you add yourself as a test user:
- ✅ You can authorize the app
- ✅ OAuth flow will complete
- ✅ Token will be saved
- ✅ Future runs won't need browser authorization (until token expires)

## Verification

After adding yourself as a test user, you should see:
- ✅ No more "Access blocked" error
- ✅ OAuth consent screen shows your app
- ✅ You can click "Allow" to grant permissions
- ✅ Token saved to `~/.youtube_token.pickle`

