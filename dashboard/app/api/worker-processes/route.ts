import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

export async function GET(request: NextRequest) {
  try {
    const workers = [
      { name: 'Script Worker', file: 'worker_script.py', emoji: '📝' },
      { name: 'Voiceover Worker', file: 'worker_voiceover.py', emoji: '🎤' },
      { name: 'Video Worker', file: 'worker_video.py', emoji: '🎬' },
      { name: 'YouTube Worker', file: 'worker_youtube.py', emoji: '📤' }
    ]

    const workerStatuses = []

    for (const worker of workers) {
      try {
        // Check if process is running
        const { stdout } = await execAsync(`pgrep -f "${worker.file}"`)
        const pids = stdout.trim().split('\n').filter(pid => pid)
        
        if (pids.length > 0) {
          // Get process details for the first PID
          try {
            const { stdout: psOutput } = await execAsync(`ps -p ${pids[0]} -o pid,etime,command`)
            const lines = psOutput.trim().split('\n')
            const info = lines.length > 1 ? lines[1] : ''
            
            workerStatuses.push({
              name: worker.name,
              file: worker.file,
              emoji: worker.emoji,
              running: true,
              pid: pids[0],
              instanceCount: pids.length,
              info: info
            })
          } catch {
            workerStatuses.push({
              name: worker.name,
              file: worker.file,
              emoji: worker.emoji,
              running: true,
              pid: pids[0],
              instanceCount: pids.length
            })
          }
        } else {
          workerStatuses.push({
            name: worker.name,
            file: worker.file,
            emoji: worker.emoji,
            running: false,
            instanceCount: 0
          })
        }
      } catch (error: any) {
        // pgrep returns non-zero exit code when no process found
        if (error.code === 1) {
          workerStatuses.push({
            name: worker.name,
            file: worker.file,
            emoji: worker.emoji,
            running: false,
            instanceCount: 0
          })
        } else {
          // Other error
          workerStatuses.push({
            name: worker.name,
            file: worker.file,
            emoji: worker.emoji,
            running: false,
            instanceCount: 0,
            error: error.message
          })
        }
      }
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

