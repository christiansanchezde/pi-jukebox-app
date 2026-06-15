# Jukebox Hardware & Software Architecture

## 🔌 Hardware Interface
The application runs on a Raspberry Pi 3B communicating with an MFRC522 RFID Reader and standard GPIO components. 

Below is the verified pinout configuration showing both the **Physical Pin** on the Raspberry Pi header for wiring, and the corresponding **BCM (GPIO)** number used in the software:

| Component | Interface | Physical Pin | BCM (GPIO) | Notes |
|-----------|-----------|--------------|------------|-------|
| **RFID**  | SPI (SDA) | Pin 24       | GPIO 8     | Chip Select / SDA |
| **RFID**  | SPI (SCK) | Pin 23       | GPIO 11    | Serial Clock |
| **RFID**  | SPI (MOSI)| Pin 19       | GPIO 10    | Master Out Slave In |
| **RFID**  | SPI (MISO)| Pin 21       | GPIO 9     | Master In Slave Out |
| **RFID**  | GPIO (RST)| Pin 22       | GPIO 25    | Hardware Reset |
| **RFID**  | Power     | Pin 1        | -          | 3.3V Power |
| **RFID**  | Ground    | Pin 6        | -          | System Ground |
| **LED G** | GPIO      | Pin 31       | GPIO 6     | Status: System Ready / Idle |
| **LED B** | GPIO      | Pin 32       | GPIO 12    | Status: Tag Detected / Playing |
| **LED R** | GPIO      | Pin 29       | GPIO 5     | Status: Error (Missing Folder/Tag) |
| **Button**| GPIO      | Pin 33       | GPIO 13    | Graceful Shutdown (Active Low) |

## 💻 Software Stack
This iteration of the Jukebox utilizes a modern, standard embedded Linux approach:
*   **OS:** Debian GNU/Linux 13 (Trixie) / Raspberry Pi OS
*   **Init System:** Systemd
*   **Runtime:** Python 3.12+ (Strictly isolated in a `.venv`)
*   **Hardware Control:** `gpiozero` (Modern GPIO interface utilizing `lgpio`) and `mfrc522`
*   **Audio Engine:** VLC (`cvlc`) executed as an asynchronous subprocess

## 🎮 Execution Flow & Logic
The user interaction is designed to be completely screen-free and intuitive for children:

1. **Idle State:** On boot, the Green LED activates. The Python async loop polls the SPI bus at 0.2-second intervals waiting for an RFID UID.
2. **Tag Detection:** 
    * When a tag is placed, the script reads the Hex UID and checks `mappings.cfg` to resolve the target folder.
    * `cvlc` is spawned as a headless subprocess to play the folder. The Blue LED blinks to indicate playback.
3. **Smart Resume (Track Memory):** 
    * The script maintains an LRU (Least Recently Used) dictionary in memory. If a recognized tag is removed and placed back on the reader, the system remembers the last track index and plays the **next** song in the folder.
    * It maintains this memory for the last 50 unique tags scanned.
4. **Tag Removal:** When the tag is physically removed, the Python loop detects the absence and executes a robust process termination sequence on `cvlc`, stopping playback immediately.
5. **Default/Error Handling:** If an unmapped tag is scanned (or the target folder is missing), the Red LED illuminates and playback defaults to an unmapped state (or plays a default folder if configured).

## ⚙️ Service Management
To ensure appliance-like behavior, the system runs two dedicated Linux services in the background:

1.  `pi-jukebox.service`: Runs the main application loop. It runs under the standard `[USER]` account to ensure audio routing to the hardware soundcard works without permission errors. It is configured to auto-restart on failure.
2.  `pi-shutdown.service`: A lightweight script using `gpiozero.Button` that listens for a physical button press on Pin 33 (GPIO 13). It runs as `root` so it has the necessary privileges to safely halt the operating system and prevent SD card corruption.