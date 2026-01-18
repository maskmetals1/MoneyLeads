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

    for (const job of jobs || []) {
      const status = job.status || 'unknown'
      statusCounts[status] = (statusCounts[status] || 0) + 1

      if (status === 'pending') {
        const metadata = job.metadata || {}
        const actionNeeded = metadata.action_needed
        pendingJobs.push({
          id: job.id.substring(0, 8),
          topic: job.topic || 'N/A',
          action: actionNeeded || 'next step',
          updatedAt: job.updated_at
        })
      } else if (['generating_script', 'creating_voiceover', 'rendering_video', 'uploading'].includes(status)) {
        processingJobs.push({
          id: job.id.substring(0, 8),
          topic: job.topic || 'N/A',
          status: status,
          updatedAt: job.updated_at
        })
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
    const hasRecentActivity = recentActivity.length > 0
    const hasProcessingJobs = processingJobs.length > 0
    const workersLikelyRunning = hasRecentActivity || hasProcessingJobs

    return NextResponse.json({
      workersRunning: workersLikelyRunning,
      statusCounts,
      pendingJobs: pendingJobs.slice(0, 10),
      processingJobs: processingJobs.slice(0, 10),
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

