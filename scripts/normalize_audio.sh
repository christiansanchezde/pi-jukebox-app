#!/bin/bash
set -e

# Resolve project root dynamically
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

# Safety check
if [ ! -d "music" ]; then
    echo "Error: music/ directory not found in project root."
    exit 1
fi

# Create timestamped backup
echo "Creating compressed backup of music directory..."
mkdir -p backups
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="backups/music_backup_${TIMESTAMP}.tar.gz"
tar -czf "$BACKUP_FILE" music/
echo "Backup saved to: $BACKUP_FILE"

# Activate environment and run normalization
echo "Activating .venv-host..."
if [ ! -f ".venv-host/bin/activate" ]; then
    echo "Error: .venv-host not found. Run 'python3 -m venv .venv-host' first."
    exit 1
fi
source .venv-host/bin/activate

echo "Starting normalization process..."
find music/ -name "*.mp3" -exec ffmpeg-normalize {} -c:a libmp3lame -b:a 320k -ar 44100 -f -o {} \;

echo "Done! You can now use your VS Code task to sync the music to the Pi."