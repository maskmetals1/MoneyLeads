'use client'

import { useState, useEffect } from 'react'

// Available voices
const VOICES = [
  { value: 'en-AU-WilliamNeural', label: 'William (Australian, Male)' },
  { value: 'en-US-SteffanNeural', label: 'Steffan (US, Male)' },
]

export default function Home() {
  const [script, setScript] = useState('')
  const [selectedVoice, setSelectedVoice] = useState('en-AU-WilliamNeural')
  const [loading, setLoading] = useState(false)
  const [voiceoverUrl, setVoiceoverUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [elapsedTime, setElapsedTime] = useState(0)
  const [estimatedTime, setEstimatedTime] = useState(0)

  // Calculate estimated time based on script length
  // Roughly 1.5 seconds per 100 characters (conservative estimate)
  const calculateEstimatedTime = (text: string): number => {
    const charCount = text.trim().length
    // Base time: 3 seconds + 1.5 seconds per 100 characters
    return Math.max(3, 3 + (charCount / 100) * 1.5)
  }

  // Timer for loading state
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null
    
    if (loading) {
      setElapsedTime(0)
      const estimated = calculateEstimatedTime(script)
      setEstimatedTime(estimated)
      
      interval = setInterval(() => {
        setElapsedTime((prev) => {
          const newTime = prev + 0.1
          return newTime
        })
      }, 100)
    } else {
      setElapsedTime(0)
      setEstimatedTime(0)
    }

    return () => {
      if (interval) {
        clearInterval(interval)
      }
    }
  }, [loading, script])

  // Calculate progress percentage
  const progress = estimatedTime > 0 
    ? Math.min(95, (elapsedTime / estimatedTime) * 100) 
    : 0

  // Calculate remaining time
  const remainingTime = Math.max(0, estimatedTime - elapsedTime)

  const handleGenerateVoiceover = async () => {
    if (!script.trim()) {
      setError('Please enter a script')
      return
    }

    setLoading(true)
    setError(null)
    setVoiceoverUrl(null)

    try {
      const response = await fetch('/api/generate-voiceover', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          script: script.trim(),
          voice: selectedVoice
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to generate voiceover')
      }

      setVoiceoverUrl(data.url)
    } catch (err: any) {
      setError(err.message || 'Failed to generate voiceover')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    if (voiceoverUrl) {
      const link = document.createElement('a')
      link.href = voiceoverUrl
      link.download = 'voiceover.mp3'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px',
      backgroundColor: '#f5f5f5'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '800px',
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '40px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}>
        <h1 style={{
          fontSize: '32px',
          fontWeight: 'bold',
          marginBottom: '10px',
          textAlign: 'center',
          color: '#333'
        }}>
          Voiceover Generator
        </h1>
        <p style={{
          fontSize: '16px',
          color: '#666',
          textAlign: 'center',
          marginBottom: '30px'
        }}>
          Enter your YouTube video script and generate a professional voiceover
        </p>

        <div style={{ marginBottom: '20px' }}>
          <label style={{
            display: 'block',
            fontSize: '14px',
            fontWeight: '600',
            marginBottom: '8px',
            color: '#333'
          }}>
            Voice
          </label>
          <select
            value={selectedVoice}
            onChange={(e) => setSelectedVoice(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '16px',
              border: '2px solid #ddd',
              borderRadius: '8px',
              fontFamily: 'inherit',
              backgroundColor: 'white',
              cursor: 'pointer',
              boxSizing: 'border-box',
              marginBottom: '20px'
            }}
          >
            {VOICES.map((voice) => (
              <option key={voice.value} value={voice.value}>
                {voice.label}
              </option>
            ))}
          </select>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{
            display: 'block',
            fontSize: '14px',
            fontWeight: '600',
            marginBottom: '8px',
            color: '#333'
          }}>
            Script Text
          </label>
          <textarea
            value={script}
            onChange={(e) => setScript(e.target.value)}
            placeholder="Enter your video script here..."
            style={{
              width: '100%',
              minHeight: '300px',
              padding: '15px',
              fontSize: '16px',
              border: '2px solid #ddd',
              borderRadius: '8px',
              fontFamily: 'inherit',
              resize: 'vertical',
              boxSizing: 'border-box'
            }}
          />
        </div>

        <button
          onClick={handleGenerateVoiceover}
          disabled={loading || !script.trim()}
          style={{
            width: '100%',
            padding: '15px',
            fontSize: '18px',
            fontWeight: '600',
            color: 'white',
            backgroundColor: loading ? '#999' : '#4a90e2',
            border: 'none',
            borderRadius: '8px',
            cursor: loading || !script.trim() ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.2s',
            marginBottom: '20px'
          }}
        >
          {loading ? 'Generating Voiceover...' : 'Create Voiceover'}
        </button>

        {loading && (
          <div style={{
            marginBottom: '20px',
            padding: '20px',
            backgroundColor: '#f9f9f9',
            borderRadius: '8px',
            border: '1px solid #ddd'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '10px'
            }}>
              <span style={{
                fontSize: '14px',
                fontWeight: '600',
                color: '#333'
              }}>
                Generating voiceover...
              </span>
              <span style={{
                fontSize: '14px',
                color: '#666',
                fontFamily: 'monospace'
              }}>
                {remainingTime > 0 
                  ? `~${Math.ceil(remainingTime)}s remaining`
                  : 'Almost done...'}
              </span>
            </div>
            
            {/* Progress bar */}
            <div style={{
              width: '100%',
              height: '8px',
              backgroundColor: '#e0e0e0',
              borderRadius: '4px',
              overflow: 'hidden',
              marginBottom: '8px'
            }}>
              <div style={{
                width: `${progress}%`,
                height: '100%',
                backgroundColor: '#4a90e2',
                borderRadius: '4px',
                transition: 'width 0.1s linear',
                background: 'linear-gradient(90deg, #4a90e2 0%, #357abd 100%)'
              }} />
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '12px',
              color: '#666'
            }}>
              <span>Progress: {Math.round(progress)}%</span>
              <span>Elapsed: {elapsedTime.toFixed(1)}s</span>
            </div>
          </div>
        )}

        {error && (
          <div style={{
            padding: '15px',
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            borderRadius: '8px',
            color: '#c33',
            marginBottom: '20px'
          }}>
            {error}
          </div>
        )}

        {voiceoverUrl && (
          <div style={{
            padding: '20px',
            backgroundColor: '#f0f8ff',
            border: '2px solid #4a90e2',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <p style={{
              fontSize: '16px',
              fontWeight: '600',
              marginBottom: '15px',
              color: '#333'
            }}>
              Voiceover Generated Successfully! 🎉
            </p>
            <audio
              controls
              src={voiceoverUrl}
              style={{
                width: '100%',
                marginBottom: '15px'
              }}
            />
            <button
              onClick={handleDownload}
              style={{
                padding: '12px 24px',
                fontSize: '16px',
                fontWeight: '600',
                color: 'white',
                backgroundColor: '#4a90e2',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#357abd'}
              onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#4a90e2'}
            >
              Download Voiceover
            </button>
          </div>
        )}

      </div>
    </div>
  )
}

