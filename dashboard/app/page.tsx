'use client'

import { useState } from 'react'

export default function Home() {
  const [script, setScript] = useState('')
  const [loading, setLoading] = useState(false)
  const [voiceoverUrl, setVoiceoverUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

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
        body: JSON.stringify({ script: script.trim() }),
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

        <div style={{
          marginTop: '30px',
          paddingTop: '20px',
          borderTop: '1px solid #ddd',
          textAlign: 'center'
        }}>
          <a
            href="/dashboard"
            style={{
              color: '#4a90e2',
              textDecoration: 'none',
              fontSize: '14px'
            }}
          >
            Go to Dashboard →
          </a>
        </div>
      </div>
    </div>
  )
}

