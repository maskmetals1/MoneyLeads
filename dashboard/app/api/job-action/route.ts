import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

// Helper function to check dependencies
function checkDependencies(job: any, action: string): { canRun: boolean, missing: string[] } {
  const missing: string[] = []
  
  switch (action) {
    case 'generate_script':
      if (!job.topic) missing.push('topic')
      break
    
    case 'generate_voiceover':
      if (!job.script) missing.push('script')
      break
    
    case 'create_video':
      if (!job.script) missing.push('script')
      if (!job.voiceover_url) missing.push('voiceover_url')
      break
    
    case 'post_to_youtube':
      if (!job.title) missing.push('title')
      if (job.description === undefined || job.description === null) missing.push('description')
      if (!job.video_url) missing.push('video_url')
      break
    
    case 'run_all':
      if (!job.topic) missing.push('topic')
      break
  }
  
  return { canRun: missing.length === 0, missing }
}

export async function POST(request: NextRequest) {
  try {
    const { action, jobIds } = await request.json()

    if (!action || !jobIds || !Array.isArray(jobIds) || jobIds.length === 0) {
      return NextResponse.json(
        { error: 'Action and jobIds are required' },
        { status: 400 }
      )
    }

    // Fetch jobs to check dependencies
    const { data: jobs, error: fetchError } = await supabase
      .from('video_jobs')
      .select('*')
      .in('id', jobIds)

    if (fetchError) {
      return NextResponse.json(
        { error: `Failed to fetch jobs: ${fetchError.message}` },
        { status: 500 }
      )
    }

    // Check dependencies for each job
    const missingDeps: string[] = []
    for (const job of jobs || []) {
      const { canRun, missing } = checkDependencies(job, action)
      if (!canRun) {
        missingDeps.push(`Job ${job.id.substring(0, 8)}: missing ${missing.join(', ')}`)
      }
    }

    if (missingDeps.length > 0) {
      return NextResponse.json(
        { 
          error: `Missing dependencies:\n${missingDeps.join('\n')}`,
          missingDependencies: missingDeps
        },
        { status: 400 }
      )
    }

    // Update jobs to pending status - worker will pick them up
    const updates: any = {
      status: 'pending',
      updated_at: new Date().toISOString()
    }

    // Set metadata based on action
    if (action === 'generate_script') {
      updates.metadata = { action_needed: 'generate_script' }
    } else if (action === 'generate_voiceover') {
      updates.metadata = { action_needed: 'generate_voiceover' }
    } else if (action === 'create_video') {
      updates.metadata = { action_needed: 'create_video' }
    } else if (action === 'run_all') {
      updates.metadata = { action_needed: 'run_all' }
    } else if (action === 'post_to_youtube') {
      updates.metadata = { action_needed: 'post_to_youtube' }
    }

    const { error } = await supabase
      .from('video_jobs')
      .update(updates)
      .in('id', jobIds)

    if (error) {
      return NextResponse.json(
        { error: `Failed to update jobs: ${error.message}` },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      message: `Action "${action}" queued for ${jobIds.length} job(s). Worker will process them shortly.`
    })
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Unknown error occurred' },
      { status: 500 }
    )
  }
}

