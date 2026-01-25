import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import { writeFile, unlink } from 'fs/promises'
import { join } from 'path'
import { tmpdir } from 'os'
import { existsSync } from 'fs'

const execAsync = promisify(exec)

// Check if we're running locally (for development) or on Vercel
const isLocal = process.env.VERCEL !== '1'

// Handle OPTIONS for CORS
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  })
}

export async function POST(request: NextRequest) {
  try {
    console.log('Voiceover API called')
    const body = await request.json()
    const { script, voice } = body
    console.log('Received request:', { scriptLength: script?.length, voice })

    if (!script || typeof script !== 'string' || script.trim().length === 0) {
      return NextResponse.json(
        { error: 'Script text is required' },
        { status: 400 }
      )
    }

    // Use provided voice or default to en-AU-WilliamNeural
    const selectedVoice = voice || 'en-AU-WilliamNeural'

    // For local development, use Python script directly
    if (isLocal) {
      return await generateWithPython(script, selectedVoice)
    }

    // For Vercel, use Node.js edge-tts package
    return await generateWithNodeTTS(script, selectedVoice)

  } catch (error: any) {
    console.error('Error in generate-voiceover API:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}

async function generateWithNodeTTS(script: string, voice: string) {
  // Use edge-tts-universal package (Node.js version of edge-tts)
  try {
    console.log(`Generating voiceover with voice: ${voice}, script length: ${script.length}`)
    
    // Import the package
    const edgeTTSModule = await import('edge-tts-universal')
    
    // Try UniversalEdgeTTS first (works in all environments)
    let result: any
    
    if (edgeTTSModule.UniversalEdgeTTS) {
      console.log('Using UniversalEdgeTTS...')
      const tts = new edgeTTSModule.UniversalEdgeTTS(script.trim(), voice)
      result = await tts.synthesize()
    } else if (edgeTTSModule.EdgeTTS) {
      console.log('Using EdgeTTS (Node.js)...')
      const tts = new edgeTTSModule.EdgeTTS(script.trim(), voice)
      result = await tts.synthesize()
    } else {
      throw new Error('No compatible TTS class found in edge-tts-universal')
    }
    
    console.log('Synthesize completed, processing audio...')
    
    // Get audio - handle different return types
    let audioBuffer: Buffer
    if (result.audio) {
      if (result.audio instanceof ArrayBuffer) {
        audioBuffer = Buffer.from(result.audio)
      } else if (result.audio.arrayBuffer) {
        const audioArrayBuffer = await result.audio.arrayBuffer()
        audioBuffer = Buffer.from(audioArrayBuffer)
      } else {
        audioBuffer = Buffer.from(result.audio)
      }
    } else if (result instanceof ArrayBuffer) {
      audioBuffer = Buffer.from(result)
    } else {
      throw new Error('Unexpected audio format from TTS')
    }
    
    console.log(`Audio buffer size: ${audioBuffer.length} bytes`)
    
    // Convert to base64
    const base64Audio = audioBuffer.toString('base64')
    const dataUrl = `data:audio/mpeg;base64,${base64Audio}`

    console.log('Voiceover generated successfully')
    return NextResponse.json({
      url: dataUrl,
      message: 'Voiceover generated successfully'
    })

  } catch (error: any) {
    console.error('Edge-TTS Universal error:', error)
    console.error('Error name:', error.name)
    console.error('Error message:', error.message)
    console.error('Error stack:', error.stack)
    
    // Provide more detailed error message
    const errorMessage = error.message || 'Unknown error'
    
    // Check for specific error types
    if (error.message?.includes('timeout') || error.name === 'TimeoutError') {
      throw new Error('Voiceover generation timed out. The script might be too long. Please try a shorter script.')
    }
    
    if (error.message?.includes('network') || error.message?.includes('fetch')) {
      throw new Error('Network error connecting to TTS service. Please check your connection and try again.')
    }
    
    throw new Error(`Failed to generate voiceover: ${errorMessage}`)
  }
}

async function generateWithPython(script: string, voice: string) {
  const tempDir = tmpdir()
  const scriptId = `voiceover_${Date.now()}_${Math.random().toString(36).substring(7)}`
  const scriptFilePath = join(tempDir, `${scriptId}.txt`)
  const outputFilePath = join(tempDir, `${scriptId}.mp3`)

  try {
    // Write script to temporary file
    await writeFile(scriptFilePath, script.trim(), 'utf-8')

    // Path to the voiceover generation script
    const voiceoverScriptPath = '/Users/phill/Desktop/oldProjects/VOICEovers/generate_custom_voice.py'
    const venvPythonPath = '/Users/phill/Desktop/oldProjects/VOICEovers/venv/bin/python3'

    // Check if paths exist
    if (!existsSync(voiceoverScriptPath)) {
      throw new Error('Voiceover script not found. Please ensure the Python script exists.')
    }

    if (!existsSync(venvPythonPath)) {
      throw new Error('Python virtual environment not found. Please ensure venv is set up.')
    }

    // Generate voiceover using the Python script with the selected voice
    const command = `${venvPythonPath} ${voiceoverScriptPath} --file ${scriptFilePath} --voice ${voice} --output ${outputFilePath}`

    console.log('Executing command:', command)

    const { stdout, stderr } = await execAsync(command, {
      timeout: 120000, // 2 minute timeout
      maxBuffer: 10 * 1024 * 1024 // 10MB buffer
    })

    if (stderr && !stderr.includes('Saved:') && !stderr.includes('Generating')) {
      console.error('Command stderr:', stderr)
    }

    console.log('Command stdout:', stdout)

    // Check if output file was created
    if (!existsSync(outputFilePath)) {
      throw new Error('Voiceover file was not created. Check Python script execution.')
    }

    // Read the generated MP3 file
    const fs = require('fs')
    const audioBuffer = await fs.promises.readFile(outputFilePath)

    // Clean up temporary files
    try {
      await unlink(scriptFilePath)
      await unlink(outputFilePath)
    } catch (cleanupError) {
      console.error('Error cleaning up temp files:', cleanupError)
    }

    // Return the audio file as a base64 data URL
    const base64Audio = audioBuffer.toString('base64')
    const dataUrl = `data:audio/mpeg;base64,${base64Audio}`

    return NextResponse.json({
      url: dataUrl,
      message: 'Voiceover generated successfully'
    })

  } catch (error: any) {
    // Clean up temporary files on error
    try {
      await unlink(scriptFilePath).catch(() => {})
      await unlink(outputFilePath).catch(() => {})
    } catch {}

    console.error('Error generating voiceover:', error)
    return NextResponse.json(
      { error: `Failed to generate voiceover: ${error.message || 'Unknown error'}` },
      { status: 500 }
    )
  }
}

