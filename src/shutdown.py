#!/usr/bin/env python3
from gpiozero import Button
import subprocess
from signal import pause

# Define the button on GPIO 13.
# 'Button' defaults to pull_up=True and active_state=False (triggers on falling edge)
shutdown_btn = Button(13)

def shutdown_system():
    print("Gracefully halting the system...")
    subprocess.call(['shutdown', '-h', 'now'], shell=False)

# Trigger the shutdown function when the button is pressed
shutdown_btn.when_pressed = shutdown_system

print("Shutdown listener active on GPIO 13. Press the hardware button to halt...")

# Pause keeps the script running in the background, using 0% CPU
pause()