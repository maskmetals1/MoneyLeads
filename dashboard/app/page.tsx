'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import Link from 'next/link'

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
  tags?: string[]
  created_at: string
  updated_at: string
  completed_at?: string
  metadata?: any
}

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedRow, setExpandedRow] = useState<string | null>(null)
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set())
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const [processing, setProcessing] = useState<Set<string>>(new Set())

  const loadJobs = async () => {
    try {
      const { data, error } = await supabase
        .from('video_jobs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(200)

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

    // Real-time subscription
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
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

  const toggleRowSelection = (jobId: string) => {
    const newSelected = new Set(selectedRows)
    if (newSelected.has(jobId)) {
      newSelected.delete(jobId)
    } else {
      newSelected.add(jobId)
    }
    setSelectedRows(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedRows.size === jobs.length) {
      setSelectedRows(new Set())
    } else {
      setSelectedRows(new Set(jobs.map(j => j.id)))
    }
  }

  const handleAction = async (action: string, jobId?: string) => {
    const jobIds = jobId ? [jobId] : Array.from(selectedRows)
    
    if (jobIds.length === 0) {
      setMessage({ type: 'error', text: 'Please select at least one row' })
      return
    }

    setProcessing(new Set(jobIds))
    setMessage(null)

    try {
      const response = await fetch('/api/job-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, jobIds })
      })

      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || 'Action failed')
      }

      setMessage({ type: 'success', text: data.message || 'Action started successfully' })
      loadJobs()
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to execute action' })
    } finally {
      setProcessing(new Set())
    }
  }

  const createNewIdea = async () => {
    const topic = prompt('Enter a topic/idea for the video:')
    if (!topic) return

    try {
      const { data, error } = await supabase
        .from('video_jobs')
        .insert([{ 
          topic: topic.trim(), 
          status: 'pending',
          metadata: { has_idea: true }
        }])
        .select()
        .single()

      if (error) throw error
      setMessage({ type: 'success', text: 'New idea created!' })
      loadJobs()
    } catch (error: any) {
      setMessage({ type: 'error', text: `Failed to create idea: ${error.message}` })
    }
  }

  const truncateText = (text: string | undefined, maxLength: number = 50) => {
    if (!text) return '-'
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading database...</div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="header">
        <h1>YouTube Automation Dashboard</h1>
        <p>Complete Database View - Spreadsheet Style</p>
        <div style={{ marginTop: '10px', display: 'flex', gap: '10px' }}>
          <Link href="/manual-upload" className="btn btn-secondary">
            Manual Upload Page
          </Link>
          <button onClick={loadJobs} className="btn btn-secondary">
            Refresh
          </button>
        </div>
      </div>

      {message && (
        <div className={message.type === 'error' ? 'error-message' : 'success-message'}>
          {message.text}
        </div>
      )}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '10px' }}>
          <h2 style={{ margin: 0 }}>All Video Jobs ({jobs.length})</h2>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button onClick={createNewIdea} className="btn btn-primary">
              + New Idea
            </button>
            <button 
              onClick={() => handleAction('generate_script')} 
              className="btn btn-primary"
              disabled={selectedRows.size === 0 || processing.size > 0}
            >
              Generate Script
            </button>
            <button 
              onClick={() => handleAction('generate_voiceover')} 
              className="btn btn-primary"
              disabled={selectedRows.size === 0 || processing.size > 0}
            >
              Generate Voiceover
            </button>
            <button 
              onClick={() => handleAction('create_video')} 
              className="btn btn-primary"
              disabled={selectedRows.size === 0 || processing.size > 0}
            >
              Create Video
            </button>
            <button 
              onClick={() => handleAction('run_all')} 
              className="btn btn-primary"
              disabled={selectedRows.size === 0 || processing.size > 0}
            >
              Run All (Script → Video)
            </button>
            <button 
              onClick={() => handleAction('post_to_youtube')} 
              className="btn btn-primary"
              disabled={selectedRows.size === 0 || processing.size > 0}
              style={{ backgroundColor: '#ff0000' }}
            >
              Post to YouTube
            </button>
          </div>
        </div>

        <div style={{ overflowX: 'auto', marginTop: '20px' }}>
          <table className="database-table">
            <thead>
              <tr>
                <th style={{ width: '40px' }}>
                  <input 
                    type="checkbox" 
                    checked={selectedRows.size === jobs.length && jobs.length > 0}
                    onChange={toggleSelectAll}
                  />
                </th>
                <th>ID</th>
                <th>Topic/Idea</th>
                <th>Title</th>
                <th>Status</th>
                <th>Script</th>
                <th>Voiceover</th>
                <th>Video</th>
                <th>YouTube</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job, index) => (
                <>
                  <tr 
                    key={job.id}
                    className={expandedRow === job.id ? 'expanded' : ''}
                    style={{ 
                      backgroundColor: index % 2 === 0 ? '#fff' : '#fafafa',
                      cursor: 'pointer'
                    }}
                    onClick={() => setExpandedRow(expandedRow === job.id ? null : job.id)}
                  >
                    <td onClick={(e) => e.stopPropagation()}>
                      <input 
                        type="checkbox" 
                        checked={selectedRows.has(job.id)}
                        onChange={() => toggleRowSelection(job.id)}
                      />
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '11px' }}>
                      {job.id.substring(0, 8)}...
                    </td>
                    <td>{truncateText(job.topic, 30)}</td>
                    <td>{truncateText(job.title, 30)}</td>
                    <td>
                      <span className={`job-status ${job.status}`}>
                        {getStatusDisplay(job.status)}
                      </span>
                    </td>
                    <td>
                      {job.script ? '✅' : '❌'}
                      {job.script && (
                        <span style={{ marginLeft: '5px', fontSize: '11px' }}>
                          ({job.script.length} chars)
                        </span>
                      )}
                    </td>
                    <td>{job.voiceover_url ? '✅' : '❌'}</td>
                    <td>{job.video_url ? '✅' : '❌'}</td>
                    <td>
                      {job.youtube_url ? (
                        <a href={job.youtube_url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                          ✅
                        </a>
                      ) : '❌'}
                    </td>
                    <td style={{ fontSize: '12px' }}>{formatDate(job.created_at)}</td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                        {!job.script && (
                          <button 
                            onClick={() => handleAction('generate_script', job.id)}
                            className="btn btn-secondary"
                            style={{ fontSize: '11px', padding: '4px 8px' }}
                            disabled={processing.has(job.id)}
                          >
                            Script
                          </button>
                        )}
                        {job.script && !job.voiceover_url && (
                          <button 
                            onClick={() => handleAction('generate_voiceover', job.id)}
                            className="btn btn-secondary"
                            style={{ fontSize: '11px', padding: '4px 8px' }}
                            disabled={processing.has(job.id)}
                          >
                            Voice
                          </button>
                        )}
                        {job.voiceover_url && !job.video_url && (
                          <button 
                            onClick={() => handleAction('create_video', job.id)}
                            className="btn btn-secondary"
                            style={{ fontSize: '11px', padding: '4px 8px' }}
                            disabled={processing.has(job.id)}
                          >
                            Video
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                  {expandedRow === job.id && (
                    <tr>
                      <td colSpan={11} style={{ backgroundColor: '#f9f9f9', padding: '20px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
                          <div>
                            <h4>Topic/Idea</h4>
                            <p>{job.topic}</p>
                          </div>
                          {job.title && (
                            <div>
                              <h4>Title</h4>
                              <p>{job.title}</p>
                            </div>
                          )}
                          {job.description && (
                            <div>
                              <h4>Description</h4>
                              <p style={{ whiteSpace: 'pre-wrap' }}>{job.description}</p>
                            </div>
                          )}
                          {job.script && (
                            <div style={{ gridColumn: '1 / -1' }}>
                              <h4>Script</h4>
                              <textarea 
                                readOnly 
                                value={job.script} 
                                style={{ width: '100%', minHeight: '200px', padding: '10px', fontFamily: 'monospace', fontSize: '12px' }}
                              />
                            </div>
                          )}
                          {job.tags && job.tags.length > 0 && (
                            <div>
                              <h4>Tags</h4>
                              <p>{job.tags.join(', ')}</p>
                            </div>
                          )}
                          <div>
                            <h4>URLs</h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                              {job.voiceover_url && (
                                <a href={job.voiceover_url} target="_blank" rel="noopener noreferrer">
                                  🎤 Voiceover
                                </a>
                              )}
                              {job.video_url && (
                                <a href={job.video_url} target="_blank" rel="noopener noreferrer">
                                  📹 Video
                                </a>
                              )}
                              {job.youtube_url && (
                                <a href={job.youtube_url} target="_blank" rel="noopener noreferrer">
                                  📺 YouTube
                                </a>
                              )}
                            </div>
                          </div>
                          <div>
                            <h4>Metadata</h4>
                            <pre style={{ fontSize: '11px', overflow: 'auto', maxHeight: '200px' }}>
                              {JSON.stringify(job.metadata || {}, null, 2)}
                            </pre>
                          </div>
                          {job.error_message && (
                            <div style={{ gridColumn: '1 / -1', color: '#ff0000' }}>
                              <h4>Error</h4>
                              <p>{job.error_message}</p>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
