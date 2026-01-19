import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function GET(request: NextRequest) {
  try {
    // Get all jobs to analyze status
    const { data: jobs, error } = await supabase
      .from('video_jobs')
      .select('*')
      .order('updated_at', { ascending: false })
      .limit(50)

    if (error) {
      return NextResponse.json(
        { error: `Failed to fetch jobs: ${error.message}` },
        { status: 500 }
      )
    }

    // Analyze job status
    const statusCounts: Record<string, number> = {}
    const pendingJobs: any[] = []
    const processingJobs: any[] = []
    const recentActivity: any[] = []
    
    // Group processing jobs by worker type
    const jobsByWorker: Record<string, any[]> = {
      'Script Worker': [],
      'Voiceover Worker': [],
      'Video Worker': [],
      'YouTube Worker': []
    }

    for (const job of jobs || []) {
      const status = job.status || 'unknown'
      statusCounts[status] = (statusCounts[status] || 0) + 1

      if (status === 'pending' || status === 'ready') {
        const metadata = job.metadata || {}
        const actionNeeded = metadata.action_needed || (status === 'ready' ? 'post_to_youtube' : 'next step')
        pendingJobs.push({
          id: job.id.substring(0, 8),
          topic: job.topic || 'N/A',
          action: actionNeeded,
          updatedAt: job.updated_at
        })
      } else if (['generating_script', 'creating_voiceover', 'rendering_video', 'uploading'].includes(status)) {
        // Map status to worker type
        const workerTypeMap: Record<string, string> = {
          'generating_script': 'Script Worker',
          'creating_voiceover': 'Voiceover Worker',
          'rendering_video': 'Video Worker',
          'uploading': 'YouTube Worker'
        }
        const workerType = workerTypeMap[status] || 'Unknown Worker'
        
        const processingJob = {
          id: job.id.substring(0, 8),
          fullId: job.id,
          topic: job.topic || 'N/A',
          title: job.title || 'N/A',
          status: status,
          subStatus: job.metadata?.sub_status || null,
          workerType: workerType,
          updatedAt: job.updated_at,
          startedAt: job.started_at || job.updated_at
        }
        
        processingJobs.push(processingJob)
        
        // Group by worker type
        if (jobsByWorker[workerType]) {
          jobsByWorker[workerType].push({
            ...processingJob,
            subStatus: job.metadata?.sub_status || null
          })
        }
      }

      // Recent activity (last 10 minutes)
      if (job.updated_at) {
        const updated = new Date(job.updated_at)
        const now = new Date()
        const minutesAgo = (now.getTime() - updated.getTime()) / 1000 / 60
        
        if (minutesAgo < 10) {
          recentActivity.push({
            id: job.id.substring(0, 8),
            topic: job.topic || 'N/A',
            status: status,
            minutesAgo: Math.round(minutesAgo)
          })
        }
      }
    }

    // Determine if workers are likely running based on activity
    // Workers are running if:
    // 1. There are jobs currently processing
    // 2. There's recent activity (jobs updated in last 10 min)
    // 3. There are pending jobs that need processing (indicates workers should be active)
    const hasRecentActivity = recentActivity.length > 0
    const hasProcessingJobs = processingJobs.length > 0
    const hasPendingJobs = pendingJobs.length > 0
    const workersLikelyRunning = hasRecentActivity || hasProcessingJobs || hasPendingJobs

    return NextResponse.json({
      workersRunning: workersLikelyRunning,
      statusCounts,
      pendingJobs: pendingJobs.slice(0, 10),
      processingJobs: processingJobs.slice(0, 10),
      jobsByWorker, // Grouped by worker type
      recentActivity: recentActivity.slice(0, 10),
      totalJobs: jobs?.length || 0,
      timestamp: new Date().toISOString()
    })
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Unknown error occurred' },
      { status: 500 }
    )
  }
}

