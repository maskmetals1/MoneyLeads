# Vercel Python Serverless Function Setup

## What is a Vercel Serverless Function with Python Runtime?

Vercel serverless functions are small pieces of code that run on-demand in the cloud. When you use Python runtime, Vercel will:
1. Execute your Python code when the API endpoint is called
2. Automatically handle scaling, deployment, and infrastructure
3. Install dependencies from `requirements.txt`

## How It Works

1. **Python Function Location**: `/api/generate-voiceover.py`
   - This is a standalone Python file (not in the Next.js `app/` directory)
   - Vercel automatically detects Python files in the `api/` folder

2. **Dependencies**: `/api/requirements.txt`
   - Lists Python packages needed (edge-tts)
   - Vercel installs these automatically during deployment

3. **Configuration**: `vercel.json`
   - Specifies Python 3.9 runtime for the function
   - Tells Vercel how to handle the function

## Current Setup

✅ **Created Files:**
- `/api/generate-voiceover.py` - Python serverless function
- `/api/requirements.txt` - Python dependencies
- Updated `vercel.json` - Runtime configuration

## How to Deploy

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm i -g vercel
   ```

2. **Deploy to Vercel**:
   ```bash
   cd dashboard
   vercel
   ```

3. **Or push to GitHub** (if connected):
   - Vercel will automatically deploy on push
   - Make sure `api/` folder is included in your repo

## Testing Locally

To test the Python function locally before deploying:

1. **Install Python dependencies**:
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. **Test the function** (you'll need to simulate Vercel's environment):
   ```python
   # This is complex - better to test after deployment
   ```

## Important Notes

⚠️ **Limitations:**
- Vercel Python functions have a **10-second timeout** on Hobby plan, **60 seconds** on Pro
- Maximum function size limits apply
- Cold starts can add latency (first request after inactivity)

⚠️ **Current Issue:**
The Python function tries to import from `/Users/phill/Desktop/oldProjects/VOICEovers` which won't exist on Vercel. We need to either:
1. Bundle the edge-tts code directly
2. Use edge-tts as a package (already in requirements.txt)
3. Remove the sys.path modification

## Next Steps

1. **Fix the import path** - The function should work with just `edge-tts` from requirements.txt
2. **Test deployment** - Deploy and test the endpoint
3. **Update frontend** - The frontend should already work once the Python function is deployed

## Alternative: Use Node.js TTS

If Python on Vercel is too complex, consider:
- Using a Node.js TTS library
- Calling an external TTS API (ElevenLabs, Google Cloud TTS, etc.)
- Running a separate backend service for voiceover generation

