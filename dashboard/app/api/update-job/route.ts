import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { jobId, title, description, script, tags } = body

    if (!jobId) {
      return NextResponse.json(
        { error: 'Job ID is required' },
        { status: 400 }
      )
    }

    // Build update object with only provided fields
    const updates: any = {}
    if (title !== undefined) updates.title = title
    if (description !== undefined) updates.description = description
    if (script !== undefined) updates.script = script
    if (tags !== undefined) {
      // Handle tags as string (comma-separated) or array
      if (typeof tags === 'string') {
        updates.tags = tags.split(',').map(t => t.trim()).filter(t => t.length > 0)
      } else if (Array.isArray(tags)) {
        updates.tags = tags
      }
    }

    if (Object.keys(updates).length === 0) {
      return NextResponse.json(
        { error: 'No fields to update' },
        { status: 400 }
      )
    }

    // Update the job
    const { data, error } = await supabase
      .from('video_jobs')
      .update(updates)
      .eq('id', jobId)
      .select()
      .single()

    if (error) {
      console.error('Error updating job:', error)
      return NextResponse.json(
        { error: error.message || 'Failed to update job' },
        { status: 500 }
      )
    }

    return NextResponse.json({ success: true, job: data })
  } catch (error: any) {
    console.error('Error in update-job route:', error)
    return NextResponse.json(
      { error: error.message || 'Unknown error occurred' },
      { status: 500 }
    )
  }
}

