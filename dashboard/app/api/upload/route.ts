import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const title = formData.get('title') as string
    const description = formData.get('description') as string
    const tags = formData.get('tags') as string
    const privacyStatus = formData.get('privacyStatus') as string || 'private'

    if (!file || !title) {
      return NextResponse.json(
        { error: 'File and title are required' },
        { status: 400 }
      )
    }

    // Create a job in Supabase
    const { data: job, error: jobError } = await supabase
      .from('video_jobs')
      .insert({
        topic: title,
        title: title,
        description: description || '',
        tags: tags ? tags.split(',').map(t => t.trim()) : [],
        status: 'pending',
        metadata: {
          manual_upload: true,
          privacy_status: privacyStatus
        }
      })
      .select()
      .single()

    if (jobError) {
      return NextResponse.json(
        { error: `Failed to create job: ${jobError.message}` },
        { status: 500 }
      )
    }

    // Upload file to Supabase Storage
    const fileExt = file.name.split('.').pop()
    const fileName = `${job.id}/video.${fileExt}`
    const fileBuffer = await file.arrayBuffer()

    const { data: uploadData, error: uploadError } = await supabase.storage
      .from('renders')
      .upload(fileName, fileBuffer, {
        contentType: file.type,
        upsert: false
      })

    if (uploadError) {
      // Delete the job if upload fails
      await supabase.from('video_jobs').delete().eq('id', job.id)
      return NextResponse.json(
        { error: `Failed to upload file: ${uploadError.message}` },
        { status: 500 }
      )
    }

    // Get public URL
    const { data: urlData } = supabase.storage
      .from('renders')
      .getPublicUrl(fileName)

    // Update job with video URL
    await supabase
      .from('video_jobs')
      .update({ video_url: urlData.publicUrl })
      .eq('id', job.id)

    return NextResponse.json({
      success: true,
      jobId: job.id,
      message: 'Video uploaded successfully. Worker will process it shortly.'
    })
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Unknown error occurred' },
      { status: 500 }
    )
  }
}

