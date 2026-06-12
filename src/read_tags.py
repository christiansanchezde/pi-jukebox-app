#!/usr/bin/env python3
import time
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

# Hardware Pin Definitions
GREEN_LED = 6   # Status: Ready
BLUE_LED = 12   # Status: Active

print("1. Setting up GPIOs...")
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(GREEN_LED, GPIO.OUT)
GPIO.setup(BLUE_LED, GPIO.OUT)

# Turn ON Green LED immediately to prove the script is running
GPIO.output(GREEN_LED, GPIO.HIGH)
GPIO.output(BLUE_LED, GPIO.LOW)

print("2. Initializing SPI and MFRC522 Reader...")
# If the script hangs, it will be right here:
reader = SimpleMFRC522()

print("3. Reader Ready! Reading UIDs… Press Ctrl+C to exit.")

try:
    while True:
        uid, _ = reader.read_no_block()
        if uid:
            uid_hex = format(uid, 'X')
            print(f"UID: {uid_hex}")
            # Turn ON Blue LED when a tag is present
            GPIO.output(BLUE_LED, GPIO.HIGH)
        else:
            # Turn OFF Blue LED when no tag is present
            GPIO.output(BLUE_LED, GPIO.LOW)
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nShutting down gracefully...")

finally:
    GPIO.cleanup()
    print("Goodbye.")