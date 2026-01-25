"""
Vercel Serverless Function for Voiceover Generation
This function runs on Vercel's Python runtime
"""
import json
import sys
import os
import asyncio
from pathlib import Path
import tempfile
import base64

try:
    import edge_tts
except ImportError:
    # If edge-tts is not available, we'll handle it gracefully
    edge_tts = None


async def generate_voiceover_async(text: str, voice: str = "en-AU-WilliamNeural") -> bytes:
    """
    Generate voiceover using edge-tts
    
    Args:
        text: Script text to convert to speech
        voice: Voice name (default: en-AU-WilliamNeural)
    
    Returns:
        bytes: MP3 audio data
    """
    if not edge_tts:
        raise ImportError("edge-tts is not installed")
    
    # Create a temporary file for output
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        # Generate voiceover
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate="+0%",
            pitch="+0Hz",
            volume="+0%"
        )
        
        await communicate.save(output_path)
        
        # Read the generated file
        with open(output_path, 'rb') as f:
            audio_data = f.read()
        
        return audio_data
    finally:
        # Clean up temp file
        if os.path.exists(output_path):
            os.unlink(output_path)


def handler(request):
    """
    Vercel serverless function handler
    
    Vercel passes a request object with:
    - request.method: HTTP method
    - request.body: Request body (string or dict)
    - request.headers: Request headers
    
    Returns:
        dict: Response with statusCode, headers, and body
    """
    # Handle CORS preflight
    if hasattr(request, 'method') and request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': ''
        }
    
    # Check method
    method = getattr(request, 'method', 'POST')
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': 'Method not allowed. Use POST.'})
        }
    
    try:
        # Parse request body
        body = getattr(request, 'body', {})
        if isinstance(body, str):
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}
        elif isinstance(body, dict):
            data = body
        else:
            data = {}
        
        script = data.get('script', '')
        
        if not script or not script.strip():
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps({'error': 'Script text is required'})
            }
        
        # Generate voiceover
        voice = data.get('voice', 'en-AU-WilliamNeural')
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            audio_data = loop.run_until_complete(
                generate_voiceover_async(script.strip(), voice)
            )
        finally:
            loop.close()
        
        # Convert to base64
        base64_audio = base64.b64encode(audio_data).decode('utf-8')
        data_url = f'data:audio/mpeg;base64,{base64_audio}'
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'url': data_url,
                'message': 'Voiceover generated successfully'
            })
        }
    
    except ImportError as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'error': f'Missing dependency: {str(e)}. Please ensure edge-tts is installed.'
            })
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error: {error_details}", file=sys.stderr)
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'error': f'Failed to generate voiceover: {str(e)}'
            })
        }


# Vercel serverless function entry point
# Vercel looks for a function named after the file (generate_voiceover)
# or a default handler
def generate_voiceover(request):
    """Vercel-compatible handler - this is what Vercel calls"""
    return handler(request)

