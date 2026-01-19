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

    // Check dependencies and if already queued/processing for each job
    const missingDeps: string[] = []
    const alreadyQueued: string[] = []
    const alreadyProcessing: string[] = []
    
    for (const job of jobs || []) {
      // Check if already processing (not pending or failed)
      if (job.status !== 'pending' && job.status !== 'failed') {
        alreadyProcessing.push(`Job ${job.id.substring(0, 8)}: already ${job.status}`)
        continue
      }
      
      // Check if already queued for this action OR run_all
      const metadata = job.metadata || {}
      const currentAction = metadata.action_needed
      const originalAction = metadata.original_action
      
      // Prevent duplicate run_all triggers
      if (action === 'run_all' && (currentAction === 'run_all' || originalAction === 'run_all')) {
        alreadyQueued.push(`Job ${job.id.substring(0, 8)}: already queued for run_all`)
        continue
      }
      
      // Check if already queued for this specific action
      if (currentAction === action) {
        alreadyQueued.push(`Job ${job.id.substring(0, 8)}: already queued for ${action}`)
        continue
      }
      
      // Check if run_all is already in progress (any step of run_all)
      if (action === 'run_all' && ['generating_script', 'generate_voiceover', 'create_video'].includes(currentAction)) {
        alreadyProcessing.push(`Job ${job.id.substring(0, 8)}: run_all already in progress (${currentAction})`)
        continue
      }
      
      // Check dependencies
      const { canRun, missing } = checkDependencies(job, action)
      if (!canRun) {
        missingDeps.push(`Job ${job.id.substring(0, 8)}: missing ${missing.join(', ')}`)
      }
    }

    // Return errors in priority order
    if (alreadyProcessing.length > 0) {
      return NextResponse.json(
        { 
          error: `Jobs already processing:\n${alreadyProcessing.join('\n')}`,
          alreadyProcessing: alreadyProcessing
        },
        { status: 400 }
      )
    }
    
    if (alreadyQueued.length > 0) {
      return NextResponse.json(
        { 
          error: `Jobs already queued:\n${alreadyQueued.join('\n')}\n\nPlease wait for them to complete.`,
          alreadyQueued: alreadyQueued
        },
        { status: 400 }
      )
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

