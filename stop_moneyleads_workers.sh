#!/bin/bash
# Stop all MoneyLeads YouTube automation workers

echo "🛑 Stopping all MoneyLeads workers..."

# Kill all worker processes
pkill -f worker_script.py && echo "✅ Stopped script worker" || echo "ℹ️  Script worker not running"
pkill -f worker_voiceover.py && echo "✅ Stopped voiceover worker" || echo "ℹ️  Voiceover worker not running"
pkill -f worker_video.py && echo "✅ Stopped video worker" || echo "ℹ️  Video worker not running"
pkill -f worker_youtube.py && echo "✅ Stopped YouTube worker" || echo "ℹ️  YouTube worker not running"
pkill -f worker.py && echo "✅ Stopped old worker" || echo "ℹ️  Old worker not running"

echo ""
echo "✅ Done! Run 'python3 check_workers.py' to verify"

