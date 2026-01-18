import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const jobId = searchParams.get('id')
    const jobIds = searchParams.get('ids')?.split(',')

    if (!jobId && !jobIds) {
      return NextResponse.json(
        { error: 'Job ID(s) required' },
        { status: 400 }
      )
    }

    const idsToDelete = jobIds || [jobId!]

    // Delete associated files from storage (optional cleanup)
    // Note: This is optional - Supabase will handle CASCADE deletes for youtube_videos table
    // But we should clean up storage files manually
    
    // Get jobs to find file paths
    const { data: jobs, error: fetchError } = await supabase
      .from('video_jobs')
      .select('id, voiceover_url, video_url, script_url')
      .in('id', idsToDelete)

    if (fetchError) {
      return NextResponse.json(
        { error: `Failed to fetch jobs: ${fetchError.message}` },
        { status: 500 }
      )
    }

    // Delete storage files if they exist
    for (const job of jobs || []) {
      try {
        // Extract file paths from URLs
        // Supabase Storage URLs format: https://[project].supabase.co/storage/v1/object/public/[bucket]/[path]
        const deleteFiles = []
        
        const extractPath = (url: string, bucket: string) => {
          if (!url) return null
          try {
            // Try to extract path from Supabase Storage URL
            const urlObj = new URL(url)
            const pathMatch = urlObj.pathname.match(new RegExp(`/${bucket}/(.+)$`))
            if (pathMatch) {
              return pathMatch[1]
            }
            // Fallback: if URL contains the bucket name, extract everything after it
            const bucketIndex = url.indexOf(`/${bucket}/`)
            if (bucketIndex !== -1) {
              return url.substring(bucketIndex + bucket.length + 1)
            }
            // Last resort: use last 2 path segments (job_id/filename)
            return url.split('/').slice(-2).join('/')
          } catch {
            // If URL parsing fails, try simple extraction
            return url.split('/').slice(-2).join('/')
          }
        }
        
        if (job.voiceover_url) {
          const path = extractPath(job.voiceover_url, 'voiceovers')
          if (path) deleteFiles.push({ bucket: 'voiceovers', path })
        }
        
        if (job.video_url) {
          const path = extractPath(job.video_url, 'renders')
          if (path) deleteFiles.push({ bucket: 'renders', path })
        }
        
        if (job.script_url) {
          const path = extractPath(job.script_url, 'scripts')
          if (path) deleteFiles.push({ bucket: 'scripts', path })
        }

        // Delete files from storage
        for (const file of deleteFiles) {
          await supabase.storage
            .from(file.bucket)
            .remove([file.path])
            .catch(err => {
              // Log but don't fail - file might not exist
              console.warn(`Failed to delete ${file.bucket}/${file.path}:`, err)
            })
        }
      } catch (err) {
        // Continue even if file deletion fails
        console.warn(`Error cleaning up files for job ${job.id}:`, err)
      }
    }

    // Delete jobs from database (CASCADE will handle youtube_videos)
    const { error: deleteError } = await supabase
      .from('video_jobs')
      .delete()
      .in('id', idsToDelete)

    if (deleteError) {
      return NextResponse.json(
        { error: `Failed to delete jobs: ${deleteError.message}` },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      message: `Successfully deleted ${idsToDelete.length} job(s)`
    })
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Unknown error occurred' },
      { status: 500 }
    )
  }
}

