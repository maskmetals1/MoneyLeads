# Vercel Python Serverless Functions - Explained Simply

## What is This?

**Vercel Serverless Functions** are pieces of code that run in the cloud when someone visits a URL. Think of them like mini-servers that only run when needed.

**Python Runtime** means Vercel will execute your Python code (instead of JavaScript/TypeScript).

## How It Works

### 1. File Structure
```
dashboard/
├── api/                          ← Vercel looks here for serverless functions
│   ├── generate-voiceover.py     ← Your Python function
│   └── requirements.txt          ← Python packages to install
├── app/                          ← Next.js app (TypeScript)
│   └── api/
│       └── generate-voiceover/
│           └── route.ts          ← This calls the Python function
└── vercel.json                   ← Configuration
```

### 2. The Flow

```
User types script → Frontend (page.tsx)
    ↓
Clicks "Create Voiceover" → Calls /api/generate-voiceover (TypeScript route)
    ↓
TypeScript route → Calls /api/generate-voiceover.py (Python function)
    ↓
Python function → Uses edge-tts to generate audio
    ↓
Returns audio → Frontend displays and allows download
```

## What I Created

1. **`/api/generate-voiceover.py`** - Python function that:
   - Takes script text as input
   - Uses `edge-tts` to generate voiceover
   - Returns audio as base64 data URL

2. **`/api/requirements.txt`** - Lists `edge-tts` package

3. **Updated `vercel.json`** - Tells Vercel to use Python 3.9

4. **Updated TypeScript route** - Now tries to call the Python function on Vercel

## How to Use It

### Option 1: Deploy to Vercel (Recommended)

1. **Push to GitHub** (if not already):
   ```bash
   git add .
   git commit -m "Add Python voiceover function"
   git push
   ```

2. **Vercel will auto-deploy** - It detects the Python function and installs dependencies

3. **Test it** - Visit your Vercel URL and try generating a voiceover

### Option 2: Test Locally First

The Python function won't work locally with `npm run dev` because:
- Next.js dev server doesn't execute Python functions
- You'd need to run Vercel CLI: `vercel dev`

## Important Notes

⚠️ **Vercel Python Functions:**
- Have timeout limits (10s on Hobby, 60s on Pro)
- May have cold starts (first request after inactivity is slower)
- Need to be in `/api/` folder (not `/app/api/`)

⚠️ **Current Status:**
- ✅ Files created and configured
- ⚠️ Needs testing on Vercel (can't test locally easily)
- ⚠️ May need adjustments based on Vercel's Python runtime version

## If It Doesn't Work

**Alternative Solutions:**

1. **Use a TTS API Service** (Easier):
   - ElevenLabs API
   - Google Cloud Text-to-Speech
   - Azure Cognitive Services
   - These work from any environment

2. **Separate Backend Service**:
   - Run Python script on a separate server (Railway, Render, etc.)
   - Call that server from Vercel

3. **Node.js TTS Library**:
   - Use a JavaScript TTS library instead
   - Works natively in Vercel

## Testing

After deployment, test the endpoint:
```bash
curl -X POST https://your-app.vercel.app/api/generate-voiceover \
  -H "Content-Type: application/json" \
  -d '{"script": "Hello, this is a test voiceover."}'
```

You should get back a JSON response with a `url` field containing the audio data.

