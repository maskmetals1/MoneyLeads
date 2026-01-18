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

interface WorkerStatus {
  workersRunning: boolean
  statusCounts: Record<string, number>
  pendingJobs: Array<{ id: string; topic: string; action: string }>
  processingJobs: Array<{ id: string; topic: string; status: string }>
  recentActivity: Array<{ id: string; topic: string; status: string; minutesAgo: number }>
  totalJobs: number
  timestamp: string
}

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedRow, setExpandedRow] = useState<string | null>(null)
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set())
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const [processing, setProcessing] = useState<Set<string>>(new Set())
  const [workerStatus, setWorkerStatus] = useState<WorkerStatus | null>(null)
  const [showStatusPanel, setShowStatusPanel] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())

  const loadJobs = async () => {
    try {
      const { data, error } = await supabase
        .from('video_jobs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(200)

      if (error) throw error
      setJobs(data || [])
      setLastRefresh(new Date())
    } catch (error: any) {
      console.error('Error loading jobs:', error)
      setMessage({ type: 'error', text: `Failed to load jobs: ${error.message}` })
    } finally {
      setLoading(false)
    }
  }

  const loadWorkerStatus = async () => {
    try {
      const response = await fetch('/api/worker-status')
      if (response.ok) {
        const data = await response.json()
        setWorkerStatus(data)
        setLastRefresh(new Date())
      }
    } catch (error) {
      console.error('Error loading worker status:', error)
    }
  }

  useEffect(() => {
    loadJobs()
    loadWorkerStatus()

    // Real-time subscription
    const channel = supabase
      .channel('jobs-changes')
      .on('postgres_changes', 
        { event: '*', schema: 'public', table: 'video_jobs' },
        () => {
          loadJobs()
          loadWorkerStatus()
        }
      )
      .subscribe()

    // Auto-refresh both jobs and worker status every 10 seconds
    const refreshInterval = setInterval(() => {
      loadJobs()
      loadWorkerStatus()
    }, 10000)

    return () => {
      supabase.removeChannel(channel)
      clearInterval(refreshInterval)
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

  const isProcessing = (status: string) => {
    return ['generating_script', 'creating_voiceover', 'rendering_video', 'uploading'].includes(status)
  }

  const getEstimatedTime = (job: Job): string | null => {
    if (!isProcessing(job.status) || !job.updated_at) return null
    
    const now = new Date().getTime()
    const updated = new Date(job.updated_at).getTime()
    const elapsedMinutes = (now - updated) / 1000 / 60
    
    // Estimated times for each step (in minutes)
    const estimates: Record<string, number> = {
      generating_script: 2,
      creating_voiceover: 3,
      rendering_video: 5,
      uploading: 2
    }
    
    const estimatedTotal = estimates[job.status] || 3
    const remaining = Math.max(0, estimatedTotal - elapsedMinutes)
    
    if (remaining <= 0) return 'Almost done...'
    if (remaining < 1) return `${Math.round(remaining * 60)}s remaining`
    return `${Math.round(remaining)}m remaining`
  }

  // Check dependencies for each action
  const checkDependencies = (job: Job, action: string): { canRun: boolean, missing: string[] } => {
    const missing: string[] = []
    
    switch (action) {
      case 'generate_script':
        // Script generation needs: topic (always available)
        if (!job.topic) missing.push('topic')
        break
      
      case 'generate_voiceover':
        // Voiceover needs: script
        if (!job.script) missing.push('script')
        break
      
      case 'create_video':
        // Video needs: script, voiceover_url
        if (!job.script) missing.push('script')
        if (!job.voiceover_url) missing.push('voiceover_url')
        break
      
      case 'post_to_youtube':
        // YouTube upload needs: title, description, video_url
        if (!job.title) missing.push('title')
        if (job.description === undefined || job.description === null) missing.push('description')
        if (!job.video_url) missing.push('video_url')
        break
      
      case 'run_all':
        // Run all needs: topic (always available)
        if (!job.topic) missing.push('topic')
        break
    }
    
    return { canRun: missing.length === 0, missing }
  }

  // Get cell highlight class based on missing dependencies
  const getCellHighlight = (job: Job, fieldName: string, action?: string): string => {
    // If no action specified, determine next logical action
    if (!action) {
      if (!job.script) action = 'generate_script'
      else if (!job.voiceover_url) action = 'generate_voiceover'
      else if (!job.video_url) action = 'create_video'
      else if (!job.youtube_url) action = 'post_to_youtube'
      else return ''
    }
    
    const { missing } = checkDependencies(job, action)
    if (missing.includes(fieldName)) {
      return 'missing-dependency'
    }
    return ''
  }
  
  // Get the next logical action for a job
  const getNextAction = (job: Job): string | null => {
    if (!job.script) return 'generate_script'
    if (!job.voiceover_url) return 'generate_voiceover'
    if (!job.video_url) return 'create_video'
    if (!job.youtube_url) return 'post_to_youtube'
    return null
  }
  
  // Check if job is already queued or processing for an action
  const isJobQueuedOrProcessing = (job: Job, action: string): boolean => {
    // Check if already processing (not pending or failed)
    if (job.status !== 'pending' && job.status !== 'failed') {
      return true
    }
    
    // Check if already queued for this action
    const metadata = job.metadata || {}
    const currentAction = metadata.action_needed
    if (currentAction === action) {
      return true
    }
    
    return false
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

    // Check dependencies and if already queued/processing for each job
    const jobsToProcess = jobs.filter(j => jobIds.includes(j.id))
    const missingDeps: string[] = []
    const alreadyQueued: string[] = []
    const alreadyProcessing: string[] = []
    
    for (const job of jobsToProcess) {
      // Check if already processing (not pending)
      if (job.status !== 'pending' && job.status !== 'failed') {
        alreadyProcessing.push(`Job ${job.id.substring(0, 8)}: already ${job.status}`)
        continue
      }
      
      // Check if already queued for this action
      const metadata = job.metadata || {}
      const currentAction = metadata.action_needed
      if (currentAction === action) {
        alreadyQueued.push(`Job ${job.id.substring(0, 8)}: already queued for ${action}`)
        continue
      }
      
      // Check dependencies
      const { canRun, missing } = checkDependencies(job, action)
      if (!canRun) {
        missingDeps.push(`Job ${job.id.substring(0, 8)}: missing ${missing.join(', ')}`)
      }
    }
    
    // Show errors if any
    if (alreadyProcessing.length > 0) {
      setMessage({ 
        type: 'error', 
        text: `Jobs already processing:\n${alreadyProcessing.join('\n')}` 
      })
      return
    }
    
    if (alreadyQueued.length > 0) {
      setMessage({ 
        type: 'error', 
        text: `Jobs already queued:\n${alreadyQueued.join('\n')}\n\nPlease wait for them to complete.` 
      })
      return
    }
    
    if (missingDeps.length > 0) {
      setMessage({ 
        type: 'error', 
        text: `Missing dependencies:\n${missingDeps.join('\n')}\n\nHighlighted cells show what's needed.` 
      })
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

  const deleteJobs = async (jobIds: string[]) => {
    if (jobIds.length === 0) {
      setMessage({ type: 'error', text: 'Please select at least one row to delete' })
      return
    }

    const confirmed = window.confirm(
      `Are you sure you want to delete ${jobIds.length} job(s)?\n\nThis will permanently delete:\n- The job record\n- Associated files (voiceovers, videos, scripts)\n- YouTube video records\n\nThis action cannot be undone.`
    )

    if (!confirmed) return

    setProcessing(new Set(jobIds))
    setMessage(null)

    try {
      const response = await fetch(`/api/delete-job?ids=${jobIds.join(',')}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      // Check if response is OK before parsing JSON
      if (!response.ok) {
        // Try to get error message from response
        let errorMessage = 'Delete failed'
        try {
          const errorData = await response.json()
          errorMessage = errorData.error || errorMessage
        } catch {
          // If response isn't JSON, get text
          const text = await response.text()
          errorMessage = text || `Server error: ${response.status} ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      const data = await response.json()
      setMessage({ type: 'success', text: data.message || 'Jobs deleted successfully' })
      setSelectedRows(new Set()) // Clear selection
      loadJobs()
    } catch (error: any) {
      console.error('Delete error:', error)
      setMessage({ type: 'error', text: error.message || 'Failed to delete jobs' })
    } finally {
      setProcessing(new Set())
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
        <div style={{ marginTop: '10px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <Link href="/manual-upload" className="btn btn-secondary">
            Manual Upload Page
          </Link>
          <button onClick={() => {
            loadJobs()
            loadWorkerStatus()
          }} className="btn btn-secondary">
            Refresh
          </button>
          <button 
            onClick={() => {
              setShowStatusPanel(!showStatusPanel)
              if (!showStatusPanel) loadWorkerStatus()
            }} 
            className="btn btn-secondary"
            style={{ backgroundColor: showStatusPanel ? '#4a90e2' : undefined, color: showStatusPanel ? 'white' : undefined }}
          >
            {showStatusPanel ? '▼' : '▶'} Worker Status
          </button>
        </div>
      </div>

      {showStatusPanel && workerStatus && (
        <div className="card" style={{ marginBottom: '20px', backgroundColor: '#f9f9f9' }}>
          <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ 
              width: '12px', 
              height: '12px', 
              borderRadius: '50%', 
              backgroundColor: workerStatus.workersRunning ? '#00aa00' : '#ff0000',
              display: 'inline-block',
              animation: workerStatus.workersRunning ? 'pulse 2s infinite' : 'none'
            }}></span>
            Worker Status {workerStatus.workersRunning ? '(Running)' : '(Not Detected)'}
          </h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '15px' }}>
            <div>
              <strong>Job Status Summary:</strong>
              <div style={{ marginTop: '5px', fontSize: '14px' }}>
                {Object.entries(workerStatus.statusCounts).map(([status, count]) => {
                  const emoji = {
                    pending: '⏳',
                    generating_script: '📝',
                    creating_voiceover: '🎤',
                    rendering_video: '🎬',
                    uploading: '📤',
                    completed: '✅',
                    failed: '❌'
                  }[status] || '📋'
                  return (
                    <div key={status} style={{ marginBottom: '3px' }}>
                      {emoji} {status}: {count}
                    </div>
                  )
                })}
              </div>
            </div>
            
            <div>
              <strong>Pending Jobs:</strong> {workerStatus.pendingJobs.length}
              {workerStatus.pendingJobs.length > 0 && (
                <div style={{ marginTop: '5px', fontSize: '12px', maxHeight: '100px', overflowY: 'auto' }}>
                  {workerStatus.pendingJobs.slice(0, 5).map((job, idx) => (
                    <div key={idx} style={{ marginBottom: '2px' }}>
                      • {job.id}... - {job.topic.substring(0, 20)} (needs: {job.action})
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div>
              <strong>Processing:</strong> {workerStatus.processingJobs.length}
              {workerStatus.processingJobs.length > 0 && (
                <div style={{ marginTop: '5px', fontSize: '12px', maxHeight: '100px', overflowY: 'auto' }}>
                  {workerStatus.processingJobs.map((job, idx) => (
                    <div key={idx} style={{ marginBottom: '2px' }}>
                      • {job.id}... - {job.topic.substring(0, 20)} ({job.status})
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div>
              <strong>Recent Activity (Last 10 min):</strong> {workerStatus.recentActivity.length}
              {workerStatus.recentActivity.length > 0 && (
                <div style={{ marginTop: '5px', fontSize: '12px', maxHeight: '100px', overflowY: 'auto' }}>
                  {workerStatus.recentActivity.map((activity, idx) => (
                    <div key={idx} style={{ marginBottom: '2px' }}>
                      • {activity.id}... - {activity.status} ({activity.minutesAgo}m ago)
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {!workerStatus.workersRunning && workerStatus.pendingJobs.length > 0 && (
            <div style={{ 
              padding: '10px', 
              backgroundColor: '#fff3cd', 
              border: '1px solid #ffc107', 
              borderRadius: '4px',
              marginTop: '10px'
            }}>
              ⚠️ <strong>Warning:</strong> You have {workerStatus.pendingJobs.length} pending job(s) but no workers detected. 
              Start workers to process jobs: <code>./start_workers.sh</code>
            </div>
          )}
          
          <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
            Last updated: {lastRefresh.toLocaleTimeString()} | 
            Total jobs: {workerStatus.totalJobs} | 
            Auto-refreshes every 10 seconds
          </div>
        </div>
      )}

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
            <button 
              onClick={() => deleteJobs(Array.from(selectedRows))} 
              className="btn btn-secondary"
              disabled={selectedRows.size === 0 || processing.size > 0}
              style={{ backgroundColor: '#dc3545', color: 'white', borderColor: '#dc3545' }}
            >
              🗑️ Delete Selected ({selectedRows.size})
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
                    <td className={getCellHighlight(job, 'topic')}>
                      {truncateText(job.topic, 30)}
                    </td>
                    <td className={getCellHighlight(job, 'title')}>
                      {truncateText(job.title, 30)}
                    </td>
                    <td>
                      <span 
                        className={`job-status ${job.status}`}
                        style={isProcessing(job.status) ? {
                          backgroundColor: '#fff3cd',
                          color: '#856404',
                          border: '1px solid #ffc107'
                        } : {}}
                      >
                        {getStatusDisplay(job.status)}
                      </span>
                      {isProcessing(job.status) && getEstimatedTime(job) && (
                        <span style={{ 
                          marginLeft: '8px', 
                          fontSize: '10px', 
                          color: '#856404',
                          fontStyle: 'italic',
                          fontWeight: '500'
                        }}>
                          ({getEstimatedTime(job)})
                        </span>
                      )}
                      {job.status === 'pending' && job.metadata?.action_needed && (
                        <span style={{ 
                          marginLeft: '8px', 
                          fontSize: '10px', 
                          color: '#666',
                          fontStyle: 'italic'
                        }}>
                          (queued: {job.metadata.action_needed.replace('_', ' ')})
                        </span>
                      )}
                    </td>
                    <td className={getCellHighlight(job, 'script')}>
                      {job.script ? '✅' : '❌'}
                      {job.script && (
                        <span style={{ marginLeft: '5px', fontSize: '11px' }}>
                          ({job.script.length} chars)
                        </span>
                      )}
                    </td>
                    <td className={getCellHighlight(job, 'voiceover_url')}>
                      {job.voiceover_url ? '✅' : '❌'}
                    </td>
                    <td className={getCellHighlight(job, 'video_url')}>
                      {job.video_url ? '✅' : '❌'}
                    </td>
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
                            disabled={processing.has(job.id) || isJobQueuedOrProcessing(job, 'generate_script')}
                            title={isJobQueuedOrProcessing(job, 'generate_script') ? 'Already queued or processing' : ''}
                          >
                            Script
                          </button>
                        )}
                        {job.script && !job.voiceover_url && (
                          <button 
                            onClick={() => handleAction('generate_voiceover', job.id)}
                            className="btn btn-secondary"
                            style={{ fontSize: '11px', padding: '4px 8px' }}
                            disabled={processing.has(job.id) || isJobQueuedOrProcessing(job, 'generate_voiceover')}
                            title={isJobQueuedOrProcessing(job, 'generate_voiceover') ? 'Already queued or processing' : ''}
                          >
                            Voice
                          </button>
                        )}
                        {job.voiceover_url && !job.video_url && (
                          <button 
                            onClick={() => handleAction('create_video', job.id)}
                            className="btn btn-secondary"
                            style={{ fontSize: '11px', padding: '4px 8px' }}
                            disabled={processing.has(job.id) || isJobQueuedOrProcessing(job, 'create_video')}
                            title={isJobQueuedOrProcessing(job, 'create_video') ? 'Already queued or processing' : ''}
                          >
                            Video
                          </button>
                        )}
                        {job.video_url && !job.youtube_url && (
                          <button 
                            onClick={() => handleAction('post_to_youtube', job.id)}
                            className="btn btn-secondary"
                            style={{ fontSize: '11px', padding: '4px 8px', backgroundColor: '#ff0000', color: 'white' }}
                            disabled={processing.has(job.id) || isJobQueuedOrProcessing(job, 'post_to_youtube')}
                            title={isJobQueuedOrProcessing(job, 'post_to_youtube') ? 'Already queued or processing' : ''}
                          >
                            Post
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
