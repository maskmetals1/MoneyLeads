'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'

interface Job {
  id: string
  topic: string
  status: string
  title?: string
  description?: string
  script?: string
  voiceover_url?: string
  video_url?: string
  youtube_url?: string
  youtube_video_id?: string
  error_message?: string
  created_at: string
  updated_at: string
  completed_at?: string
}

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [topic, setTopic] = useState('')
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  
  // Manual upload state
  const [uploading, setUploading] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadDescription, setUploadDescription] = useState('')
  const [uploadTags, setUploadTags] = useState('')
  const [uploadPrivacy, setUploadPrivacy] = useState('private')

  const loadJobs = async () => {
    try {
      const { data, error } = await supabase
        .from('video_jobs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(50)

      if (error) throw error
      setJobs(data || [])
    } catch (error: any) {
      console.error('Error loading jobs:', error)
      setMessage({ type: 'error', text: `Failed to load jobs: ${error.message}` })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadJobs()

    // Set up real-time subscription
    const channel = supabase
      .channel('jobs-changes')
      .on('postgres_changes', 
        { event: '*', schema: 'public', table: 'video_jobs' },
        () => {
          loadJobs()
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim()) {
      setMessage({ type: 'error', text: 'Please enter a topic' })
      return
    }

    setSubmitting(true)
    setMessage(null)

    try {
      const { data, error } = await supabase
        .from('video_jobs')
        .insert([{ topic: topic.trim(), status: 'pending' }])
        .select()
        .single()

      if (error) throw error

      setMessage({ type: 'success', text: 'Job created successfully! The worker will process it shortly.' })
      setTopic('')
      loadJobs()
    } catch (error: any) {
      console.error('Error creating job:', error)
      setMessage({ type: 'error', text: `Failed to create job: ${error.message}` })
    } finally {
      setSubmitting(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
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
      
      // Reset form
      setUploadFile(null)
      setUploadTitle('')
      setUploadDescription('')
      setUploadTags('')
      setUploadPrivacy('private')
      
      // Reset file input
      const fileInput = document.getElementById('video-file') as HTMLInputElement
      if (fileInput) fileInput.value = ''
      
      // Reload jobs
      loadJobs()
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to upload video' })
    } finally {
      setUploading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 2 * 1024 * 1024 * 1024) { // 2GB limit
        setMessage({ type: 'error', text: 'File size must be less than 2GB' })
        return
      }
      setUploadFile(file)
      // Auto-fill title from filename if empty
      if (!uploadTitle.trim()) {
        setUploadTitle(file.name.replace(/\.[^/.]+$/, ''))
      }
    }
  }

  const getStatusDisplay = (status: string) => {
    const statusMap: Record<string, string> = {
      pending: 'Pending',
      generating_script: 'Generating Script',
      creating_voiceover: 'Creating Voiceover',
      rendering_video: 'Rendering Video',
      uploading: 'Uploading to YouTube',
      completed: 'Completed',
      failed: 'Failed'
    }
    return statusMap[status] || status
  }

  return (
    <div className="container">
      <div className="header">
        <h1>YouTube Automation Dashboard</h1>
        <p>Create and manage automated YouTube videos</p>
      </div>

      {message && (
        <div className={message.type === 'error' ? 'error-message' : 'success-message'}>
          {message.text}
        </div>
      )}

      <div className="card">
        <h2>Create New Video (AI Generated)</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="topic">Video Topic</label>
            <input
              type="text"
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., How to start a side hustle"
              disabled={submitting}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Creating...' : 'Create Video Job'}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Upload & Post Video</h2>
        <p style={{ marginBottom: '20px', color: '#666', fontSize: '14px' }}>
          Upload an existing video file to post directly to YouTube
        </p>
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

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ margin: 0 }}>Video Jobs</h2>
          <button onClick={loadJobs} className="btn btn-secondary">
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="loading">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="loading">No jobs yet. Create one above!</div>
        ) : (
          <div className="jobs-list">
            {jobs.map((job) => (
              <div key={job.id} className={`job-card ${job.status}`}>
                <div className="job-header">
                  <div>
                    <div className="job-title">{job.title || job.topic}</div>
                    <div className="job-topic">Topic: {job.topic}</div>
                  </div>
                  <span className={`job-status ${job.status}`}>
                    {getStatusDisplay(job.status)}
                  </span>
                </div>

                <div className="job-details">
                  <p><strong>Created:</strong> {formatDate(job.created_at)}</p>
                  {job.updated_at && (
                    <p><strong>Last Updated:</strong> {formatDate(job.updated_at)}</p>
                  )}
                  {job.completed_at && (
                    <p><strong>Completed:</strong> {formatDate(job.completed_at)}</p>
                  )}
                  {job.error_message && (
                    <p style={{ color: '#ff0000' }}><strong>Error:</strong> {job.error_message}</p>
                  )}
                </div>

                {(job.voiceover_url || job.video_url || job.youtube_url) && (
                  <div className="job-links">
                    {job.youtube_url && (
                      <a href={job.youtube_url} target="_blank" rel="noopener noreferrer">
                        📺 View on YouTube
                      </a>
                    )}
                    {job.video_url && (
                      <a href={job.video_url} target="_blank" rel="noopener noreferrer">
                        📹 Download Video
                      </a>
                    )}
                    {job.voiceover_url && (
                      <a href={job.voiceover_url} target="_blank" rel="noopener noreferrer">
                        🎤 Download Voiceover
                      </a>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

