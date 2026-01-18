import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function POST(request: NextRequest) {
  try {
    const { action, jobIds } = await request.json()

    if (!action || !jobIds || !Array.isArray(jobIds) || jobIds.length === 0) {
      return NextResponse.json(
        { error: 'Action and jobIds are required' },
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

