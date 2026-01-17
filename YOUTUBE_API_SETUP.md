# YouTube Data API v3 Setup Guide

**Yes, you need to set it up in Google Cloud Console!** Here's the complete step-by-step guide.

## Quick Answer

1. ✅ Go to [Google Cloud Console](https://console.cloud.google.com/projectselector2/auth/overview?supportedpurview=project)
2. ✅ Create a project
3. ✅ Enable YouTube Data API v3
4. ✅ Create OAuth 2.0 credentials (Desktop app)
5. ✅ Download credentials JSON file

## Detailed Steps

### Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console:**
   ```
   https://console.cloud.google.com/projectselector2/auth/overview?supportedpurview=project
   ```

2. **Sign in** with your Google account (the one you want to use for YouTube)

3. **Create a new project:**
   - Click "Select a project" dropdown at the top
   - Click "New Project"
   - Project name: `YouTube Automation` (or your choice)
   - Click "Create"
   - Wait ~30 seconds for project to be created

### Step 2: Enable YouTube Data API v3

1. **Go to APIs & Services → Library:**
   ```
   https://console.cloud.google.com/apis/library
   ```
   Or: Click ☰ menu → "APIs & Services" → "Library"

2. **Search for "YouTube Data API v3"**

3. **Click on "YouTube Data API v3"**

4. **Click the blue "Enable" button**

5. **Wait for API to be enabled** (~10 seconds)

### Step 3: Configure OAuth Consent Screen

1. **Go to APIs & Services → OAuth consent screen:**
   ```
   https://console.cloud.google.com/apis/credentials/consent
   ```

2. **Select User Type:**
   - Choose **External** (unless you have Google Workspace)
   - Click "Create"

3. **Fill in App Information:**
   - App name: `YouTube Automation`
   - User support email: (select your email)
   - Developer contact: (your email)
   - Click "Save and Continue"

4. **Scopes:**
   - Click "Add or Remove Scopes"
   - Search for "youtube.upload"
   - Check the box for `https://www.googleapis.com/auth/youtube.upload`
   - Click "Update" → "Save and Continue"

5. **Test Users:**
   - Click "Add Users"
   - Add your Google account email (the one you'll use for YouTube)
   - Click "Add" → "Save and Continue"

6. **Summary:**
   - Review and click "Back to Dashboard"

### Step 4: Create OAuth 2.0 Credentials

1. **Go to APIs & Services → Credentials:**
   ```
   https://console.cloud.google.com/apis/credentials
   ```

2. **Click "Create Credentials" → "OAuth client ID"**

3. **Select Application type:**
   - Choose **Desktop app**

4. **Fill in details:**
   - Name: `YouTube Automation Client`
   - Click "Create"

5. **Download credentials:**
   - A popup will show your Client ID and Client Secret
   - **Click the download icon (⬇️)** to download JSON file
   - **OR** copy the Client ID and Client Secret manually

6. **Save the credentials file:**
   ```bash
   # Move downloaded file to home directory
   mv ~/Downloads/client_secret_*.json ~/.youtube_credentials.json
   
   # Or if you know the exact filename:
   mv ~/Downloads/client_secret_123456789-abcdefg.apps.googleusercontent.com.json ~/.youtube_credentials.json
   ```

### Step 5: Update Configuration

You have two options:

#### Option A: Using Credentials File (Recommended)

The `youtube_uploader.py` automatically looks for `~/.youtube_credentials.json`

Just make sure the file is in the right place:
```bash
ls ~/.youtube_credentials.json
# Should show the file
```

#### Option B: Using Environment Variables

If you prefer to use `.env` file:

1. **Copy Client ID and Client Secret** from the OAuth client page

2. **Update `.env` file:**
   ```bash
   YOUTUBE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
   YOUTUBE_CLIENT_SECRET=GOCSPX-your-secret-here
   ```

### Step 6: Authorize the Application

The first time you run the worker, it will:

1. **Open a browser window** automatically
2. **Ask you to sign in** to your Google account
3. **Show a consent screen** asking for permission to manage your YouTube account
4. **Click "Allow"** or "Continue"
5. **Save the token** to `~/.youtube_token.pickle`

**You only need to do this once!** After that, the token will be reused automatically.

### Step 7: Test the Setup

```bash
cd /Users/phill/Desktop/youtube_automation
source venv/bin/activate

# Test YouTube uploader (this will open browser for first-time auth)
python3 -c "
from youtube_uploader import YouTubeUploader
uploader = YouTubeUploader()
print('✅ YouTube API setup successful!')
print('✅ Token saved to ~/.youtube_token.pickle')
"
```

## Important Notes

### API Quotas

- **Free tier:** 10,000 units per day
- **Video upload:** ~1,600 units per request
- **You can upload ~6 videos per day** on free tier
- **Quota resets:** Daily at midnight Pacific Time

### Privacy Settings

By default, videos are uploaded as **private**. You can change this in the worker or after upload in YouTube Studio.

### File Format

The credentials JSON file should look like this:
```json
{
  "installed": {
    "client_id": "123456789-abcdefg.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-your-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

Note: The official example shows `"web"` but for Desktop apps it should be `"installed"`.

## Troubleshooting

### "OAuth credentials file not found"
- Make sure `~/.youtube_credentials.json` exists
- Check the file path: `ls -la ~/.youtube_credentials.json`
- The file should be named exactly `.youtube_credentials.json` in your home directory

### "YouTube Data API v3 has not been used"
- Make sure you enabled the API in Step 2
- Wait a few minutes for the API to be fully enabled
- Check: https://console.cloud.google.com/apis/dashboard

### "Access blocked: This app's request is invalid"
- Make sure you added your email as a test user in OAuth consent screen
- If using External user type, you MUST add test users
- Go back to OAuth consent screen and add your email

### "The request cannot be completed because you have exceeded your quota"
- You've hit the daily quota limit (10,000 units)
- Wait until midnight Pacific Time for quota reset
- Or request a quota increase in Google Cloud Console

### Browser doesn't open for authorization
- Make sure you're running the script locally (not on a server)
- The script uses `run_local_server()` which requires local access
- If on a remote server, you'll need to use a different OAuth flow

## What's Different from the Official Example?

The official YouTube example uses the **deprecated** `oauth2client` library. Our implementation uses the **modern** `google-auth` and `google-auth-oauthlib` libraries, which are:

- ✅ Still maintained by Google
- ✅ More secure
- ✅ Better error handling
- ✅ Recommended for new projects

The functionality is the same, just using updated libraries.

## Next Steps

Once setup is complete:

1. ✅ Test the connection (see Step 7)
2. ✅ Add your OpenAI API key to `.env`
3. ✅ Run the worker: `python worker.py`
4. ✅ Create a test job via the dashboard
5. ✅ Watch it upload to YouTube! 🎬

## References

- [YouTube Data API v3 Documentation](https://developers.google.com/youtube/v3)
- [OAuth 2.0 Setup Guide](https://developers.google.com/youtube/v3/guides/auth)
- [API Quotas](https://developers.google.com/youtube/v3/getting-started#quota)
- [Official Upload Example](https://developers.google.com/youtube/v3/guides/uploading_a_video)
