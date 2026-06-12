#!/bin/bash
set -e

# go to your project directory
cd /home/chris/jukebox

# activate the virtualenv
. .venv/bin/activate

# exec the jukebox.py (so signals like SIGTERM reach it directly)
exec python jukebox.py