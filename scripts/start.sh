#!/bin/bash
set -e

# Dynamically resolve the absolute path to the project root
# (Finds the directory of this script, then goes up one level)
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

# Activate the virtualenv
. .venv/bin/activate

# Exec the main script
exec python src/jukebox.py