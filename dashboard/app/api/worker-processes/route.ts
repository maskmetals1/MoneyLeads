import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET(request: NextRequest) {
  try {
    const workers = [
      { name: 'Script Worker', file: 'worker_script.py', emoji: '📝', status: 'generating_script' },
      { name: 'Voiceover Worker', file: 'worker_voiceover.py', emoji: '🎤', status: 'creating_voiceover' },
      { name: 'Video Worker', file: 'worker_video.py', emoji: '🎬', status: 'rendering_video' },
      { name: 'YouTube Worker', file: 'worker_youtube.py', emoji: '📤', status: 'uploading' }
    ]

    // Get all jobs to check for worker activity
    const { data: jobs, error } = await supabase
      .from('video_jobs')
      .select('*')
      .order('updated_at', { ascending: false })
      .limit(100)

    if (error) {
      return NextResponse.json(
        { error: `Failed to fetch jobs: ${error.message}` },
        { status: 500 }
      )
    }

    const now = new Date()
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000) // 5 minutes ago

    const workerStatuses = []

    for (const worker of workers) {
      // Check if this worker is active by looking for:
      // 1. Jobs currently in this worker's status (definitely running)
      const currentlyProcessing = (jobs || []).filter(job => job.status === worker.status)
      
      // 2. Check for pending jobs that need this worker's action
      const pendingJobsForWorker = (jobs || []).filter(job => {
        if (job.status !== 'pending') return false
        const metadata = job.metadata || {}
        const actionNeeded = metadata.action_needed
        
        // Map worker status to action needed
        const actionMap: Record<string, string> = {
          'generating_script': 'generate_script',
          'creating_voiceover': 'generate_voiceover',
          'rendering_video': 'create_video',
          'uploading': 'post_to_youtube'
        }
        
        const expectedAction = actionMap[worker.status]
        return actionNeeded === expectedAction || actionNeeded === 'run_all'
      })
      
      // 3. Check for heartbeats in metadata (workers send heartbeats every 30 seconds)
      let hasHeartbeat = false
      let latestHeartbeat: Date | null = null
      for (const job of jobs || []) {
        const metadata = job.metadata || {}
        const heartbeatKey = worker.name.toLowerCase().replace(' ', '_') + '_heartbeat'
        if (metadata[heartbeatKey]) {
          const heartbeatTime = new Date(metadata[heartbeatKey])
          if (heartbeatTime >= fiveMinutesAgo) {
            hasHeartbeat = true
            if (!latestHeartbeat || heartbeatTime > latestHeartbeat) {
              latestHeartbeat = heartbeatTime
            }
          }
        }
      }
      
      // 4. Check for recent activity with this worker's sub_status
      const recentActivity = (jobs || []).filter(job => {
        if (job.status === worker.status) return true // Already counted in currentlyProcessing
        
        if (job.updated_at) {
          const updated = new Date(job.updated_at)
          if (updated >= fiveMinutesAgo) {
            const metadata = job.metadata || {}
            const subStatus = metadata.sub_status
            // Check if sub_status indicates this worker's activity
            if (subStatus && (
              (worker.status === 'generating_script' && (subStatus === 'generating_title_description' || subStatus === 'generating_script')) ||
              (worker.status === 'creating_voiceover' && (subStatus === 'generating_audio' || subStatus === 'uploading_voiceover')) ||
              (worker.status === 'rendering_video' && (subStatus === 'rendering_video' || subStatus === 'uploading_video')) ||
              (worker.status === 'uploading' && subStatus.includes('upload'))
            )) {
              return true
            }
          }
        }
        return false
      })

      // Worker is running if:
      // - Currently processing a job
      // - Has recent heartbeat (within 5 minutes)
      // - Has recent activity with matching sub_status
      // - Has pending jobs waiting for it (indicates worker should be active)
      const isRunning = currentlyProcessing.length > 0 || hasHeartbeat || recentActivity.length > 0 || pendingJobsForWorker.length > 0

      workerStatuses.push({
        name: worker.name,
        file: worker.file,
        emoji: worker.emoji,
        running: isRunning,
        instanceCount: isRunning ? Math.max(currentlyProcessing.length, recentActivity.length > 0 ? 1 : 0, pendingJobsForWorker.length > 0 ? 1 : 0) : 0,
        activeJobs: currentlyProcessing.length,
        pendingJobs: pendingJobsForWorker.length,
        lastHeartbeat: latestHeartbeat ? latestHeartbeat.toISOString() : null
      })
    }

    const runningCount = workerStatuses.filter(w => w.running).length
    const totalCount = workerStatuses.length

    return NextResponse.json({
      workers: workerStatuses,
      summary: {
        running: runningCount,
        total: totalCount,
        allRunning: runningCount === totalCount
      },
      timestamp: new Date().toISOString()
    })
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Unknown error occurred' },
      { status: 500 }
    )
  }
}

