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
    const twoMinutesAgo = new Date(now.getTime() - 2 * 60 * 1000) // 2 minutes ago

    const workerStatuses = []

    for (const worker of workers) {
      // Check if this worker is active by looking for:
      // 1. Jobs currently in this worker's status
      // 2. Jobs that were recently updated with this status (within last 2 minutes)
      const activeJobs = (jobs || []).filter(job => {
        if (job.status === worker.status) {
          return true // Currently processing
        }
        // Check if job was recently updated (within 2 minutes)
        if (job.updated_at) {
          const updated = new Date(job.updated_at)
          if (updated >= twoMinutesAgo) {
            // Check if this job's status matches or if it's in a state that indicates this worker was active
            // Also check metadata for worker activity
            const metadata = job.metadata || {}
            const subStatus = metadata.sub_status
            // If sub_status indicates this worker's activity, consider it active
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

      const isRunning = activeJobs.length > 0

      workerStatuses.push({
        name: worker.name,
        file: worker.file,
        emoji: worker.emoji,
        running: isRunning,
        instanceCount: isRunning ? activeJobs.length : 0,
        activeJobs: isRunning ? activeJobs.length : 0
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

