#!/usr/bin/env python3
"""RFID‑controlled jukebox (Embedded Device Refactor with gpiozero)."""
import os
import sys
import asyncio
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from contextlib import suppress
from collections import OrderedDict

from mfrc522 import SimpleMFRC522
from gpiozero import LED

# ——————— Global filter to drop AUTH ERROR lines ———————
class FilterStream:
    def __init__(self, orig):
        self.orig = orig
    def write(self, data):
        if "AUTH ERROR" in data:
            return
        self.orig.write(data)
    def flush(self):
        self.orig.flush()

sys.stdout = FilterStream(sys.stdout)
sys.stderr = FilterStream(sys.stderr)

# ——————— Paths & config ———————
BASE_DIR      = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MUSIC_ROOT    = os.path.join(BASE_DIR, 'music')
MAPPING_FILE  = os.path.join(BASE_DIR, 'mappings.cfg')
LOG_FILE      = os.path.join(BASE_DIR, 'jukebox.log')

# LED pins (BCM numbering)
GREEN_LED_PIN = 6    
BLUE_LED_PIN  = 12   
RED_LED_PIN   = 5    

AUDIO_EXTS     = ('.mp3', '.wav', '.ogg', '.flac')
POLL_INTERVAL  = 0.2  
BLINK_INTERVAL = 0.5  
MAX_HISTORY    = 50   

# ——————— Embedded Logging Setup ———————
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=1024*1024, backupCount=1),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger('jukebox')

# ——————— Load tag→folder mappings ———————
def load_mappings(path):
    mappings, default = {}, None
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                uid, folder = map(str.strip, line.split('=', 1))
                uid = uid.upper()
                if uid == 'DEFAULT':
                    default = folder
                else:
                    mappings[uid] = folder
    except FileNotFoundError:
        logger.error(f"Mappings file not found at {path!r}.")
    except Exception as e:
        logger.error(f"Error reading mappings file: {e}")
    return mappings, default

# ——————— Async playback task ———————
async def playback(folder: str, start_index: int = 0):
    try:
        files = await asyncio.to_thread(os.listdir, folder)
        files = sorted(f for f in files if f.lower().endswith(AUDIO_EXTS))
    except Exception as e:
        logger.error(f"Failed to read folder {folder!r}: {e}")
        return

    if not files:
        return

    if start_index:
        files = files[start_index:] + files[:start_index]

    paths = [os.path.join(folder, f) for f in files]

    try:
        proc = await asyncio.create_subprocess_exec(
            'cvlc', '--no-video', '--loop', *paths,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        logger.error("`cvlc` not found. Install VLC (`sudo apt-get install vlc`).")
        return
    except Exception as e:
        logger.error(f"Failed to start cvlc subprocess: {e}")
        return

    try:
        await proc.wait()
    except asyncio.CancelledError:
        try:
            proc.terminate() 
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(proc.wait(), timeout=2.0)
            
            if proc.returncode is None:
                proc.kill()
                await proc.wait()
        except Exception as e:
            logger.error(f"Error terminating VLC process: {e}")
        raise

# ——————— Async LED blink task ———————
async def blink_led(led: LED):
    try:
        while True:
            led.toggle()
            await asyncio.sleep(BLINK_INTERVAL)
    except asyncio.CancelledError:
        led.off()
        raise

# ——————— Main loop ———————
async def main():
    # Initialize gpiozero LEDs
    green_led = LED(GREEN_LED_PIN)
    blue_led = LED(BLUE_LED_PIN)
    red_led = LED(RED_LED_PIN)

    green_led.on()   
    blue_led.off()
    red_led.off()

    try:
        reader = SimpleMFRC522()
    except Exception as e:
        logger.critical(f"Failed to initialize SPI reader: {e}")
        return

    mappings, default_folder = load_mappings(MAPPING_FILE)

    last_uid = None                 
    play_task = blink_task = None   
    index_map = OrderedDict()  

    try:
        while True:
            try:
                uid, _ = reader.read_no_block()
            except Exception:
                uid = None

            if uid:
                uid_hex = format(uid, 'X').upper()
                if uid_hex != last_uid:
                    
                    if play_task:
                        play_task.cancel()
                        with suppress(asyncio.CancelledError):
                            await play_task
                    if blink_task:
                        blink_task.cancel()
                        with suppress(asyncio.CancelledError):
                            await blink_task
                            
                    blue_led.off()

                    folder_name = mappings.get(uid_hex, default_folder)
                    if not folder_name:
                        red_led.on()
                    else:
                        folder_path = os.path.join(MUSIC_ROOT, folder_name)
                        if not await asyncio.to_thread(os.path.isdir, folder_path):
                            logger.error(f"Folder mapped to {uid_hex} not found: {folder_path}")
                            red_led.on()
                        else:
                            try:
                                files = await asyncio.to_thread(os.listdir, folder_path)
                                files = sorted(f for f in files if f.lower().endswith(AUDIO_EXTS))
                            except Exception as e:
                                logger.error(f"File read error on {folder_path}: {e}")
                                files = []

                            if not files:
                                red_led.on()
                            else:
                                next_idx = (index_map.get(uid_hex, -1) + 1) % len(files)
                                index_map[uid_hex] = next_idx
                                index_map.move_to_end(uid_hex)
                                if len(index_map) > MAX_HISTORY:
                                    index_map.popitem(last=False)

                                red_led.off()
                                play_task = asyncio.create_task(
                                    playback(folder_path, start_index=next_idx)
                                )
                                blink_task = asyncio.create_task(blink_led(blue_led))

                    last_uid = uid_hex
            else:
                if last_uid is not None:
                    if play_task:
                        play_task.cancel()
                        with suppress(asyncio.CancelledError):
                            await play_task
                    if blink_task:
                        blink_task.cancel()
                        with suppress(asyncio.CancelledError):
                            await blink_task
                    
                    blue_led.off()
                    red_led.off()
                    last_uid = None

            await asyncio.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        pass 
    except Exception as exc:
        logger.critical(f"Unhandled exception in main loop: {exc}")
    finally:
        if play_task:
            play_task.cancel()
            with suppress(asyncio.CancelledError):
                await play_task
        if blink_task:
            blink_task.cancel()
            with suppress(asyncio.CancelledError):
                await blink_task
        # No GPIO.cleanup() needed, gpiozero handles this automatically!

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger = logging.getLogger('jukebox')
        logger.critical(f"Entrypoint exception: {e}")
        sys.exit(1)