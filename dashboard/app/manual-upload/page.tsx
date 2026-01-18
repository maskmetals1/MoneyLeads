'use client'

import { useState } from 'react'
import { supabase } from '@/lib/supabase'
import Link from 'next/link'

export default function ManualUpload() {
  const [uploading, setUploading] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadDescription, setUploadDescription] = useState('')
  const [uploadTags, setUploadTags] = useState('')
  const [uploadPrivacy, setUploadPrivacy] = useState('private')
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 2 * 1024 * 1024 * 1024) {
        setMessage({ type: 'error', text: 'File size must be less than 2GB' })
        return
      }
      setUploadFile(file)
      if (!uploadTitle.trim()) {
        setUploadTitle(file.name.replace(/\.[^/.]+$/, ''))
      }
    }
  }

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!uploadFile || !uploadTitle.trim()) {
      setMessage({ type: 'error', text: 'Please select a video file and enter a title' })
      return
    }

    setUploading(true)
    setMessage(null)

    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      formData.append('title', uploadTitle.trim())
      formData.append('description', uploadDescription.trim())
      formData.append('tags', uploadTags.trim())
      formData.append('privacyStatus', uploadPrivacy)

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Upload failed')
      }

      setMessage({ type: 'success', text: data.message || 'Video uploaded successfully! Worker will process it shortly.' })
      
      setUploadFile(null)
      setUploadTitle('')
      setUploadDescription('')
      setUploadTags('')
      setUploadPrivacy('private')
      
      const fileInput = document.getElementById('video-file') as HTMLInputElement
      if (fileInput) fileInput.value = ''
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to upload video' })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="container">
      <div className="header">
        <h1>Manual Video Upload</h1>
        <p>Upload an existing video file to post directly to YouTube</p>
        <div style={{ marginTop: '10px' }}>
          <Link href="/" className="btn btn-secondary">
            ← Back to Dashboard
          </Link>
        </div>
      </div>

      {message && (
        <div className={message.type === 'error' ? 'error-message' : 'success-message'}>
          {message.text}
        </div>
      )}

      <div className="card">
        <h2>Upload & Post Video</h2>
        <form onSubmit={handleFileUpload}>
          <div className="form-group">
            <label htmlFor="video-file">Video File</label>
            <input
              type="file"
              id="video-file"
              accept="video/*"
              onChange={handleFileSelect}
              disabled={uploading}
              required
            />
            {uploadFile && (
              <p style={{ marginTop: '8px', fontSize: '13px', color: '#666' }}>
                Selected: {uploadFile.name} ({(uploadFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="upload-title">Title *</label>
            <input
              type="text"
              id="upload-title"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              placeholder="Video title"
              disabled={uploading}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="upload-description">Description</label>
            <textarea
              id="upload-description"
              value={uploadDescription}
              onChange={(e) => setUploadDescription(e.target.value)}
              placeholder="Video description"
              disabled={uploading}
              rows={4}
            />
          </div>

          <div className="form-group">
            <label htmlFor="upload-tags">Tags (comma-separated)</label>
            <input
              type="text"
              id="upload-tags"
              value={uploadTags}
              onChange={(e) => setUploadTags(e.target.value)}
              placeholder="tag1, tag2, tag3"
              disabled={uploading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="upload-privacy">Privacy Status</label>
            <select
              id="upload-privacy"
              value={uploadPrivacy}
              onChange={(e) => setUploadPrivacy(e.target.value)}
              disabled={uploading}
            >
              <option value="private">Private</option>
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
            </select>
          </div>

          <button type="submit" className="btn btn-primary" disabled={uploading || !uploadFile}>
            {uploading ? 'Uploading & Posting...' : 'Upload & Post to YouTube'}
          </button>
        </form>
      </div>
    </div>
  )
}

