#!/bin/bash
# Start all YouTube automation workers (MoneyLeads Python Scripts)

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found at $SCRIPT_DIR/venv"
    echo "   Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate

# Stop any existing workers first to avoid conflicts
echo "🛑 Stopping any existing workers..."
pkill -f worker_script.py 2>/dev/null && echo "   ✅ Stopped script worker" || true
pkill -f worker_voiceover.py 2>/dev/null && echo "   ✅ Stopped voiceover worker" || true
pkill -f worker_video.py 2>/dev/null && echo "   ✅ Stopped video worker" || true
pkill -f worker_youtube.py 2>/dev/null && echo "   ✅ Stopped YouTube worker" || true
pkill -f worker.py 2>/dev/null && echo "   ✅ Stopped old worker" || true

# Wait a moment for processes to fully terminate
sleep 2

echo ""
echo "🚀 Starting all workers..."
echo "$(date): 🚀 Starting all workers..." >> logs/launchd.log

# Start workers in background with logging
nohup python3 worker_script.py >> logs/worker_script.log 2>&1 &
echo "   ✅ Script worker started (PID: $!)"
echo "$(date): ✅ Script worker started (PID: $!)" >> logs/launchd.log

nohup python3 worker_voiceover.py >> logs/worker_voiceover.log 2>&1 &
echo "   ✅ Voiceover worker started (PID: $!)"
echo "$(date): ✅ Voiceover worker started (PID: $!)" >> logs/launchd.log

nohup python3 worker_video.py >> logs/worker_video.log 2>&1 &
echo "   ✅ Video worker started (PID: $!)"
echo "$(date): ✅ Video worker started (PID: $!)" >> logs/launchd.log

nohup python3 worker_youtube.py >> logs/worker_youtube.log 2>&1 &
echo "   ✅ YouTube worker started (PID: $!)"
echo "$(date): ✅ YouTube worker started (PID: $!)" >> logs/launchd.log

echo ""
echo "✅ All workers started!"
echo "📊 Check status: python3 check_workers.py"
echo "📝 View logs: tail -f logs/worker_*.log"
echo "🛑 Stop workers: ./stop_moneyleads_workers.sh"
echo ""
echo "$(date): ✅ All workers started!" >> logs/launchd.log
