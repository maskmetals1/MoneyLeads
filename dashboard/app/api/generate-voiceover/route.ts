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

export async function POST(request: NextRequest) {
  try {
    const { script } = await request.json()

    if (!script || typeof script !== 'string' || script.trim().length === 0) {
      return NextResponse.json(
        { error: 'Script text is required' },
        { status: 400 }
      )
    }

    // For local development, use Python script directly
    if (isLocal) {
      return await generateWithPython(script)
    }

    // For Vercel, use Node.js edge-tts package
    return await generateWithNodeTTS(script)

  } catch (error: any) {
    console.error('Error in generate-voiceover API:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}

async function generateWithNodeTTS(script: string) {
  // Use edge-tts-universal package (Node.js version of edge-tts)
  try {
    const { UniversalEdgeTTS } = await import('edge-tts-universal')
    
    // Use en-AU-WilliamNeural voice (Australian William - matches your preference)
    const tts = new UniversalEdgeTTS(script.trim(), 'en-AU-WilliamNeural')
    const result = await tts.synthesize()
    
    // Get audio as buffer
    const audioArrayBuffer = await result.audio.arrayBuffer()
    const audioBuffer = Buffer.from(audioArrayBuffer)
    
    // Convert to base64
    const base64Audio = audioBuffer.toString('base64')
    const dataUrl = `data:audio/mpeg;base64,${base64Audio}`

    return NextResponse.json({
      url: dataUrl,
      message: 'Voiceover generated successfully'
    })

  } catch (error: any) {
    console.error('Edge-TTS Universal error:', error)
    throw new Error(`Failed to generate voiceover: ${error.message}`)
  }
}

async function generateWithPython(script: string) {
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

    // Generate voiceover using the Python script
    const command = `${venvPythonPath} ${voiceoverScriptPath} --file ${scriptFilePath} --voice en-AU-WilliamNeural --output ${outputFilePath}`

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

