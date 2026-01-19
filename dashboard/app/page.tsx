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
  pendingJobs: Array<{ id: string; topic: string; action: string; fullId?: string }>
  processingJobs: Array<{ id: string; topic: string; title?: string; status: string; subStatus?: string | null; workerType?: string; updatedAt?: string; startedAt?: string; fullId?: string }>
  jobsByWorker?: Record<string, Array<{ id: string; topic: string; title?: string; status: string; subStatus?: string | null; updatedAt?: string; startedAt?: string }>>
  recentActivity: Array<{ id: string; topic: string; status: string; minutesAgo: number; updatedAt?: string }>
  totalJobs: number
  timestamp: string
}

interface WorkerProcess {
  name: string
  file: string
  emoji: string
  running: boolean
  pid?: string
  instanceCount: number
  activeJobs?: number
  pendingJobs?: number
  lastHeartbeat?: string | null
  info?: string
  error?: string
}

interface WorkerProcesses {
  workers: WorkerProcess[]
  summary: {
    running: number
    total: number
    allRunning: boolean
  }
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
  const [workerProcesses, setWorkerProcesses] = useState<WorkerProcesses | null>(null)
  const [showStatusPanel, setShowStatusPanel] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date())
  const [editingJob, setEditingJob] = useState<string | null>(null)
  const [editValues, setEditValues] = useState<{ [jobId: string]: { title?: string; description?: string; script?: string; tags?: string } }>({})
  const [saving, setSaving] = useState<Set<string>>(new Set())
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState<{
    hasTopic?: boolean | null
    hasTitle?: boolean | null
    hasScript?: boolean | null
    hasVoiceover?: boolean | null
    hasVideo?: boolean | null
    hasYouTube?: boolean | null
    status?: string
    dateFrom?: string
    dateTo?: string
  }>({})

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
      // Load job status
      const statusResponse = await fetch('/api/worker-status')
      if (statusResponse.ok) {
        const statusData = await statusResponse.json()
        setWorkerStatus(statusData)
      }
      
      // Load actual worker processes
      const processesResponse = await fetch('/api/worker-processes')
      if (processesResponse.ok) {
        const processesData = await processesResponse.json()
        setWorkerProcesses(processesData)
      }
      
      setLastRefresh(new Date())
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

  const getStatusMessage = (job: Job): string | null => {
    if (!isProcessing(job.status) || !job.updated_at) return null
    
    const subStatus = job.metadata?.sub_status
    const now = new Date().getTime()
    const updated = new Date(job.updated_at).getTime()
    const elapsedMinutes = (now - updated) / 1000 / 60
    
    // Get status-specific messages and time estimates
    const statusInfo: Record<string, { message: string, totalTime: number, subStatuses?: Record<string, { message: string, time: number }> }> = {
      generating_script: {
        message: 'Generating script...',
        totalTime: 2.5,
        subStatuses: {
          generating_title_description: { message: 'Creating title & description...', time: 1 },
          generating_script: { message: 'Writing script content...', time: 1.5 }
        }
      },
      creating_voiceover: {
        message: 'Creating voiceover...',
        totalTime: 4,
        subStatuses: {
          generating_audio: { message: 'Generating audio with AI...', time: 2.5 },
          uploading_voiceover: { message: 'Uploading to Supabase...', time: 1.5 }
        }
      },
      rendering_video: {
        message: 'Rendering video...',
        totalTime: 8,
        subStatuses: {
          rendering_video: { message: 'Processing video & captions...', time: 6 },
          uploading_video: { message: 'Uploading to Supabase...', time: 2 }
        }
      },
      uploading: {
        message: 'Uploading to YouTube...',
        totalTime: 2
      }
    }
    
    const info = statusInfo[job.status]
    if (!info) return null
    
    // If we have sub-status, use more specific estimates
    if (subStatus && info.subStatuses && info.subStatuses[subStatus]) {
      const subInfo = info.subStatuses[subStatus]
      const remaining = Math.max(0, subInfo.time - elapsedMinutes)
      
      if (remaining <= 0) return `${subInfo.message} (almost done...)`
      if (remaining < 0.5) return `${subInfo.message} (~${Math.round(remaining * 60)}s)`
      return `${subInfo.message} (~${Math.round(remaining)}m)`
    }
    
    // Otherwise use overall estimate
    const remaining = Math.max(0, info.totalTime - elapsedMinutes)
    
    if (remaining <= 0) return `${info.message} (almost done...)`
    if (remaining < 1) return `${info.message} (~${Math.round(remaining * 60)}s)`
    return `${info.message} (~${Math.round(remaining)}m)`
  }
  
  const getEstimatedTime = (job: Job): string | null => {
    // Use the new getStatusMessage for better accuracy
    return getStatusMessage(job)
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

  const handleEditChange = (jobId: string, field: 'title' | 'description' | 'script' | 'tags', value: string) => {
    setEditValues(prev => ({
      ...prev,
      [jobId]: {
        ...prev[jobId],
        [field]: value
      }
    }))
  }

  const startEditing = (jobId: string) => {
    const job = jobs.find(j => j.id === jobId)
    if (job) {
      setEditValues({
        [jobId]: {
          title: job.title || '',
          description: job.description || '',
          script: job.script || '',
          tags: job.tags ? job.tags.join(', ') : ''
        }
      })
      setEditingJob(jobId)
    }
  }

  const cancelEditing = (jobId: string) => {
    setEditingJob(null)
    setEditValues(prev => {
      const newValues = { ...prev }
      delete newValues[jobId]
      return newValues
    })
  }

  const saveJobEdits = async (jobId: string) => {
    const edits = editValues[jobId]
    if (!edits) return

    setSaving(prev => new Set(prev).add(jobId))

    try {
      const response = await fetch('/api/update-job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jobId,
          title: edits.title,
          description: edits.description,
          script: edits.script,
          tags: edits.tags
        })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to save changes')
      }

      setMessage({ type: 'success', text: 'Changes saved successfully' })
      setEditingJob(null)
      setEditValues(prev => {
        const newValues = { ...prev }
        delete newValues[jobId]
        return newValues
      })
      loadJobs()
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to save changes' })
    } finally {
      setSaving(prev => {
        const newSet = new Set(prev)
        newSet.delete(jobId)
        return newSet
      })
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

  const applyFilters = (jobsToFilter: Job[]): Job[] => {
    return jobsToFilter.filter(job => {
      // Field completion filters
      if (filters.hasTopic !== undefined && filters.hasTopic !== null) {
        const hasTopic = !!job.topic
        if (filters.hasTopic !== hasTopic) return false
      }
      if (filters.hasTitle !== undefined && filters.hasTitle !== null) {
        const hasTitle = !!job.title
        if (filters.hasTitle !== hasTitle) return false
      }
      if (filters.hasScript !== undefined && filters.hasScript !== null) {
        const hasScript = !!job.script
        if (filters.hasScript !== hasScript) return false
      }
      if (filters.hasVoiceover !== undefined && filters.hasVoiceover !== null) {
        const hasVoiceover = !!job.voiceover_url
        if (filters.hasVoiceover !== hasVoiceover) return false
      }
      if (filters.hasVideo !== undefined && filters.hasVideo !== null) {
        const hasVideo = !!job.video_url
        if (filters.hasVideo !== hasVideo) return false
      }
      if (filters.hasYouTube !== undefined && filters.hasYouTube !== null) {
        const hasYouTube = !!job.youtube_url
        if (filters.hasYouTube !== hasYouTube) return false
      }

      // Status filter
      if (filters.status && filters.status !== 'all') {
        if (job.status !== filters.status) return false
      }

      // Date filters
      if (filters.dateFrom) {
        const jobDate = new Date(job.created_at)
        const fromDate = new Date(filters.dateFrom)
        if (jobDate < fromDate) return false
      }
      if (filters.dateTo) {
        const jobDate = new Date(job.created_at)
        const toDate = new Date(filters.dateTo)
        toDate.setHours(23, 59, 59, 999) // End of day
        if (jobDate > toDate) return false
      }

      return true
    })
  }

  const clearFilters = () => {
    setFilters({})
  }

  const filteredJobs = applyFilters(jobs)

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

      {showStatusPanel && (
        <div className="card" style={{ marginBottom: '20px', backgroundColor: '#f9f9f9' }}>
          <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ 
              width: '12px', 
              height: '12px', 
              borderRadius: '50%', 
              backgroundColor: workerProcesses?.summary.allRunning ? '#00aa00' : workerProcesses?.summary.running ? '#ffa500' : '#ff0000',
              display: 'inline-block',
              animation: workerProcesses?.summary.running ? 'pulse 2s infinite' : 'none'
            }}></span>
            Worker Status {
              workerProcesses?.summary.allRunning ? `(${workerProcesses.summary.running}/${workerProcesses.summary.total} Running)` :
              workerProcesses?.summary.running ? `(${workerProcesses.summary.running}/${workerProcesses.summary.total} Running - Partial)` :
              '(Not Detected)'
            }
          </h3>
          
          {/* Worker Processes Status */}
          {workerProcesses && (
            <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #ddd' }}>
              <h4 style={{ marginTop: 0, marginBottom: '15px', fontSize: '16px', fontWeight: '600' }}>Worker Processes</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '12px' }}>
                {workerProcesses.workers.map((worker, idx) => (
                  <div 
                    key={idx}
                    style={{
                      padding: '12px',
                      borderRadius: '6px',
                      border: `2px solid ${worker.running ? '#00aa00' : '#ddd'}`,
                      backgroundColor: worker.running ? '#f0fff0' : '#f9f9f9'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '20px' }}>{worker.emoji}</span>
                      <strong style={{ fontSize: '14px', color: worker.running ? '#00aa00' : '#666' }}>
                        {worker.name}
                      </strong>
                      <span style={{
                        fontSize: '10px',
                        padding: '2px 6px',
                        borderRadius: '10px',
                        backgroundColor: worker.running ? '#00aa00' : '#999',
                        color: 'white',
                        fontWeight: '600'
                      }}>
                        {worker.running ? 'RUNNING' : 'STOPPED'}
                      </span>
                    </div>
                    {worker.running && (
                      <div style={{ fontSize: '12px', color: '#666', marginTop: '6px' }}>
                        <div>Status: Running (Local)</div>
                        {(worker.activeJobs ?? 0) > 0 && (
                          <div style={{ color: '#00aa00', fontWeight: '600' }}>
                            ✓ Processing {worker.activeJobs} job(s)
                          </div>
                        )}
                        {(worker.pendingJobs ?? 0) > 0 && (
                          <div style={{ color: '#4a90e2', fontWeight: '600' }}>
                            ⏳ {worker.pendingJobs} pending job(s)
                          </div>
                        )}
                        {worker.instanceCount > 1 && (
                          <div style={{ color: '#ffa500', fontWeight: '600' }}>
                            ⚠️ {worker.instanceCount} instances detected
                          </div>
                        )}
                        {worker.lastHeartbeat && (
                          <div style={{ fontSize: '10px', color: '#999', marginTop: '2px' }}>
                            Last heartbeat: {new Date(worker.lastHeartbeat).toLocaleTimeString()}
                          </div>
                        )}
                      </div>
                    )}
                    {!worker.running && (
                      <div style={{ fontSize: '11px', color: '#999', fontStyle: 'italic', marginTop: '4px' }}>
                        Process not detected
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {workerStatus && (
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
                <div style={{ marginTop: '5px', fontSize: '12px', maxHeight: '120px', overflowY: 'auto' }}>
                  {workerStatus.pendingJobs.slice(0, 5).map((job, idx) => (
                    <div key={idx} style={{ 
                      marginBottom: '4px', 
                      padding: '6px', 
                      backgroundColor: '#fff', 
                      borderRadius: '4px',
                      border: '1px solid #e0e0e0'
                    }}>
                      <div style={{ fontWeight: '600', fontSize: '11px', color: '#333' }}>
                        {job.id}... - {job.topic.substring(0, 30)}
                      </div>
                      <div style={{ fontSize: '10px', color: '#666', marginTop: '2px' }}>
                        Needs: {job.action.replace('_', ' ')}
                      </div>
                    </div>
                  ))}
                  {workerStatus.pendingJobs.length > 5 && (
                    <div style={{ fontSize: '10px', color: '#999', fontStyle: 'italic', marginTop: '4px' }}>
                      + {workerStatus.pendingJobs.length - 5} more...
                    </div>
                  )}
                </div>
              )}
            </div>
            
            {/* Processing Jobs Grouped by Worker */}
            {workerStatus.jobsByWorker && (
              <div style={{ gridColumn: '1 / -1' }}>
                <strong style={{ display: 'block', marginBottom: '10px' }}>Processing Jobs by Worker:</strong>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
                  {Object.entries(workerStatus.jobsByWorker).map(([workerType, jobs]) => {
                    if (jobs.length === 0) return null
                    
                    const workerEmoji = {
                      'Script Worker': '📝',
                      'Voiceover Worker': '🎤',
                      'Video Worker': '🎬',
                      'YouTube Worker': '📤'
                    }[workerType] || '⚙️'
                    
                    return (
                      <div key={workerType} style={{
                        padding: '12px',
                        backgroundColor: '#fff',
                        borderRadius: '6px',
                        border: '1px solid #e0e0e0'
                      }}>
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '8px', 
                          marginBottom: '12px',
                          fontWeight: '600',
                          fontSize: '18px',
                          color: '#4a90e2'
                        }}>
                          <span style={{ fontSize: '20px' }}>{workerEmoji}</span>
                          <span>{workerType}</span>
                          <span style={{
                            fontSize: '14px',
                            padding: '4px 8px',
                            backgroundColor: '#4a90e2',
                            color: 'white',
                            borderRadius: '10px'
                          }}>
                            {jobs.length}
                          </span>
                        </div>
                        <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                          {jobs.map((job, idx) => {
                            const startTime = job.startedAt ? new Date(job.startedAt) : new Date(job.updatedAt || '')
                            const now = new Date()
                            const elapsedMinutes = Math.round((now.getTime() - startTime.getTime()) / 1000 / 60)
                            
                            return (
                              <div key={idx} style={{
                                marginBottom: '10px',
                                padding: '10px',
                                backgroundColor: '#f9f9f9',
                                borderRadius: '4px',
                                border: '1px solid #e0e0e0'
                              }}>
                                <div style={{ fontWeight: '600', fontSize: '14px', color: '#333', marginBottom: '6px' }}>
                                  {job.id}... - {job.topic.substring(0, 25)}
                                </div>
                                {job.title && job.title !== 'N/A' && (
                                  <div style={{ fontSize: '13px', color: '#666', marginBottom: '6px', fontStyle: 'italic' }}>
                                    "{job.title.substring(0, 40)}..."
                                  </div>
                                )}
                                <div style={{ fontSize: '13px', color: '#999' }}>
                                  Running for: {elapsedMinutes}m | Status: {job.status.replace('_', ' ')}
                                  {job.subStatus && (
                                    <span style={{ color: '#4a90e2', fontWeight: '600' }}>
                                      {' • '}{job.subStatus.replace('_', ' ')}
                                    </span>
                                  )}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })}
                </div>
                {workerStatus.processingJobs.length === 0 && (
                  <div style={{ padding: '10px', textAlign: 'center', color: '#999', fontSize: '13px' }}>
                    No jobs currently processing
                  </div>
                )}
              </div>
            )}
            
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
          )}
          
          {workerStatus && !workerProcesses?.summary.allRunning && workerStatus.pendingJobs.length > 0 && (
            <div style={{ 
              padding: '10px', 
              backgroundColor: '#fff3cd', 
              border: '1px solid #ffc107', 
              borderRadius: '4px',
              marginTop: '10px'
            }}>
              ⚠️ <strong>Warning:</strong> You have {workerStatus.pendingJobs.length} pending job(s) but {workerProcesses?.summary.running === 0 ? 'no workers detected' : `only ${workerProcesses?.summary.running}/${workerProcesses?.summary.total} workers running`}. 
              Start workers to process jobs: <code>./start_moneyleads_workers.sh</code>
            </div>
          )}
          
          <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
            Last updated: {lastRefresh.toLocaleTimeString()} | 
            {workerStatus && `Total jobs: ${workerStatus.totalJobs} | `}
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
          <h2 style={{ margin: 0 }}>
            All Video Jobs ({filteredJobs.length}{filteredJobs.length !== jobs.length ? ` of ${jobs.length}` : ''})
          </h2>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button 
              onClick={() => setShowFilters(!showFilters)} 
              className="btn btn-secondary"
              style={{ backgroundColor: showFilters ? '#4a90e2' : '', color: showFilters ? 'white' : '' }}
            >
              🔍 {showFilters ? 'Hide' : 'Show'} Filters
            </button>
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

        {showFilters && (
          <div style={{ 
            marginBottom: '20px', 
            padding: '15px', 
            backgroundColor: '#f9f9f9', 
            borderRadius: '8px',
            border: '1px solid #ddd'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h3 style={{ margin: 0, fontSize: '16px' }}>Filters</h3>
              <button onClick={clearFilters} className="btn btn-secondary" style={{ fontSize: '12px', padding: '4px 8px' }}>
                Clear All
              </button>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
              {/* Field Completion Filters */}
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: '600' }}>
                  Topic/Idea
                </label>
                <select
                  value={filters.hasTopic === undefined ? 'all' : filters.hasTopic ? 'yes' : 'no'}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    hasTopic: e.target.value === 'all' ? undefined : e.target.value === 'yes' 
                  }))}
                  style={{ width: '100%', padding: '6px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="all">All</option>
                  <option value="yes">Has Topic</option>
                  <option value="no">No Topic</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: '600' }}>
                  Title
                </label>
                <select
                  value={filters.hasTitle === undefined ? 'all' : filters.hasTitle ? 'yes' : 'no'}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    hasTitle: e.target.value === 'all' ? undefined : e.target.value === 'yes' 
                  }))}
                  style={{ width: '100%', padding: '6px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="all">All</option>
                  <option value="yes">Has Title</option>
                  <option value="no">No Title</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: '600' }}>
                  Script
                </label>
                <select
                  value={filters.hasScript === undefined ? 'all' : filters.hasScript ? 'yes' : 'no'}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    hasScript: e.target.value === 'all' ? undefined : e.target.value === 'yes' 
                  }))}
                  style={{ width: '100%', padding: '6px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="all">All</option>
                  <option value="yes">Has Script</option>
                  <option value="no">No Script</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: '600' }}>
                  Voiceover
                </label>
                <select
                  value={filters.hasVoiceover === undefined ? 'all' : filters.hasVoiceover ? 'yes' : 'no'}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    hasVoiceover: e.target.value === 'all' ? undefined : e.target.value === 'yes' 
                  }))}
                  style={{ width: '100%', padding: '6px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="all">All</option>
                  <option value="yes">Has Voiceover</option>
                  <option value="no">No Voiceover</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: '600' }}>
                  Video
                </label>
                <select
                  value={filters.hasVideo === undefined ? 'all' : filters.hasVideo ? 'yes' : 'no'}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    hasVideo: e.target.value === 'all' ? undefined : e.target.value === 'yes' 
                  }))}
                  style={{ width: '100%', padding: '6px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="all">All</option>
                  <option value="yes">Has Video</option>
                  <option value="no">No Video</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: '600' }}>
                  YouTube
                </label>
                <select
                  value={filters.hasYouTube === undefined ? 'all' : filters.hasYouTube ? 'yes' : 'no'}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    hasYouTube: e.target.value === 'all' ? undefined : e.target.value === 'yes' 
                  }))}
                  style={{ width: '100%', padding: '6px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="all">All</option>
                  <option value="yes">Has YouTube</option>
                  <option value="no">No YouTube</option>
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: '600' }}>
                  Status
                </label>
                <select
                  value={filters.status || 'all'}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    status: e.target.value === 'all' ? undefined : e.target.value 
                  }))}
                  style={{ width: '100%', padding: '6px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="all">All Statuses</option>
                  <option value="pending">Pending</option>
                  <option value="generating_script">Generating Script</option>
                  <option value="creating_voiceover">Creating Voiceover</option>
                  <option value="rendering_video">Rendering Video</option>
                  <option value="uploading">Uploading</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
              </div>

              {/* Date Filters */}
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: '600' }}>
                  Date From
                </label>
                <input
                  type="date"
                  value={filters.dateFrom || ''}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    dateFrom: e.target.value || undefined 
                  }))}
                  style={{ width: '100%', padding: '6px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: '600' }}>
                  Date To
                </label>
                <input
                  type="date"
                  value={filters.dateTo || ''}
                  onChange={(e) => setFilters(prev => ({ 
                    ...prev, 
                    dateTo: e.target.value || undefined 
                  }))}
                  style={{ width: '100%', padding: '6px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
            </div>
          </div>
        )}

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
              {filteredJobs.map((job, index) => (
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
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
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
                        {isProcessing(job.status) && (
                          <span style={{ 
                            fontSize: '14px', 
                            color: '#4a90e2',
                            fontWeight: '600',
                            textTransform: 'uppercase',
                            display: 'block',
                            marginTop: '4px'
                          }}>
                            {job.status === 'generating_script' && '📝 Script Worker'}
                            {job.status === 'creating_voiceover' && '🎤 Voiceover Worker'}
                            {job.status === 'rendering_video' && '🎬 Video Worker'}
                            {job.status === 'uploading' && '📤 YouTube Worker'}
                          </span>
                        )}
                        {isProcessing(job.status) && getEstimatedTime(job) && (
                          <span style={{ 
                            fontSize: '13px', 
                            color: '#856404',
                            fontStyle: 'italic',
                            fontWeight: '500',
                            display: 'block',
                            marginTop: '2px'
                          }}>
                            ({getEstimatedTime(job)})
                          </span>
                        )}
                        {job.status === 'pending' && job.metadata?.action_needed && (
                          <span style={{ 
                            fontSize: '10px', 
                            color: '#666',
                            fontStyle: 'italic'
                          }}>
                            (queued: {job.metadata.action_needed.replace('_', ' ')})
                          </span>
                        )}
                      </div>
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
                            <div style={{ marginTop: '15px' }}>
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
                                {!job.voiceover_url && !job.video_url && !job.youtube_url && (
                                  <p style={{ color: '#999', fontSize: '13px' }}>No URLs available</p>
                                )}
                              </div>
                            </div>
                          </div>
                          <div>
                            <h4 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              Title
                              {editingJob === job.id ? (
                                <div style={{ display: 'flex', gap: '5px' }}>
                                  <button
                                    onClick={() => saveJobEdits(job.id)}
                                    className="btn btn-primary"
                                    style={{ fontSize: '11px', padding: '4px 8px' }}
                                    disabled={saving.has(job.id)}
                                  >
                                    {saving.has(job.id) ? 'Saving...' : 'Save'}
                                  </button>
                                  <button
                                    onClick={() => cancelEditing(job.id)}
                                    className="btn btn-secondary"
                                    style={{ fontSize: '11px', padding: '4px 8px' }}
                                    disabled={saving.has(job.id)}
                                  >
                                    Cancel
                                  </button>
                                </div>
                              ) : (
                                <button
                                  onClick={() => startEditing(job.id)}
                                  className="btn btn-secondary"
                                  style={{ fontSize: '11px', padding: '4px 8px' }}
                                >
                                  Edit
                                </button>
                              )}
                            </h4>
                            {editingJob === job.id ? (
                              <input
                                type="text"
                                value={editValues[job.id]?.title || ''}
                                onChange={(e) => handleEditChange(job.id, 'title', e.target.value)}
                                style={{ width: '100%', padding: '8px', fontSize: '14px', border: '1px solid #ddd', borderRadius: '4px' }}
                                placeholder="Enter title"
                              />
                            ) : (
                              <p>{job.title || 'No title'}</p>
                            )}
                          </div>
                          <div>
                            <h4>Description</h4>
                            {editingJob === job.id ? (
                              <textarea
                                value={editValues[job.id]?.description || ''}
                                onChange={(e) => handleEditChange(job.id, 'description', e.target.value)}
                                style={{ width: '100%', minHeight: '150px', padding: '8px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px', fontFamily: 'inherit' }}
                                placeholder="Enter description"
                              />
                            ) : (
                              <p style={{ whiteSpace: 'pre-wrap' }}>{job.description || 'No description'}</p>
                            )}
                          </div>
                          {job.script && (
                            <div style={{ gridColumn: '1 / -1' }}>
                              <h4>Script</h4>
                              {editingJob === job.id ? (
                                <textarea
                                  value={editValues[job.id]?.script || ''}
                                  onChange={(e) => handleEditChange(job.id, 'script', e.target.value)}
                                  style={{ width: '100%', minHeight: '300px', padding: '10px', fontFamily: 'monospace', fontSize: '12px', border: '1px solid #ddd', borderRadius: '4px' }}
                                  placeholder="Enter script"
                                />
                              ) : (
                                <textarea
                                  readOnly
                                  value={job.script}
                                  style={{ width: '100%', minHeight: '200px', padding: '10px', fontFamily: 'monospace', fontSize: '12px' }}
                                />
                              )}
                            </div>
                          )}
                          <div>
                            <h4>Tags</h4>
                            {editingJob === job.id ? (
                              <input
                                type="text"
                                value={editValues[job.id]?.tags || ''}
                                onChange={(e) => handleEditChange(job.id, 'tags', e.target.value)}
                                style={{ width: '100%', padding: '8px', fontSize: '13px', border: '1px solid #ddd', borderRadius: '4px' }}
                                placeholder="Enter tags (comma-separated)"
                              />
                            ) : (
                              <p>{job.tags && job.tags.length > 0 ? job.tags.join(', ') : 'No tags'}</p>
                            )}
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
