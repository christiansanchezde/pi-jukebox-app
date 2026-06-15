# Jukebox Setup & Deployment Guide

This guide covers everything needed to configure the Raspberry Pi hardware, set up the developer environment on your host computer, and deploy the Jukebox application.

---

## 1. Target Setup (Raspberry Pi)

Start by flashing your SD card with the latest standard **Raspberry Pi OS (Debian 13 / Trixie)**. SSH into the Pi using your configured `[USER]` account.

### 1.1 Install System Dependencies
Update the package manager and install the necessary system-level components, including the VLC engine, Python virtual environment tools, and the C-headers required for the modern `lgpio` hardware interface:

```bash
sudo apt-get update
sudo apt-get install vlc python3-venv
sudo apt-get install liblgpio-dev
sudo apt-get install python3-dev build-essential
```

### 1.2 Enable the SPI Port

The RFID reader communicates via the SPI bus, which is disabled by default in Raspberry Pi OS. Enable it via the configuration tool:

1. Run the config tool:

```bash
   sudo raspi-config
```

2. Navigate down to **3 Interface Options** and press `Enter`.
3. Navigate down to **I4 SPI** and press `Enter`.
4. When asked "Would you like the SPI interface to be enabled?", select ****.
5. You will see a confirmation saying "The SPI interface is enabled". Press `Enter`.
6. Use the `Right Arrow` key to select **** at the bottom of the main menu.

### 1.3 Create the Target Python Environment

Clone or copy your project folder to the Pi, then isolate the application dependencies in a virtual environment:

```bash
cd /home/[USER]/jukebox
python3 -m venv .venv
source .venv/bin/activate

# Install the application libraries
pip install -r requirements.txt
```

### 1.4 Install System Services

To make the Jukebox function as a "plug-and-play" embedded appliance, we register two `systemd` services.

* `pi-jukebox.service`: Runs the main app (as `[USER]`).
* `pi-shutdown.service`: Runs the hardware button listener (as `root`).

Copy the service files and set permissions:

```bash
sudo cp /home/[USER]/jukebox/scripts/pi-jukebox.service /etc/systemd/system/
sudo cp /home/[USER]/jukebox/scripts/pi-shutdown.service /etc/systemd/system/

sudo chmod 644 /etc/systemd/system/pi-jukebox.service
sudo chmod 644 /etc/systemd/system/pi-shutdown.service
```

Enable and start the services so they run automatically on boot:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-jukebox.service
sudo systemctl enable pi-shutdown.service
sudo systemctl start pi-jukebox.service
sudo systemctl start pi-shutdown.service
```

*(Optional) Verify their status using:*

```bash
sudo systemctl status pi-jukebox.service
sudo systemctl status pi-shutdown.service
```

---

## 2. Host Setup (Developer PC)

To develop, deploy, and process audio locally without polluting your host machine, configure a dedicated host environment.

### 2.1 Host Dependencies

You will need `ffmpeg` installed on your host system (or WSL) to process audio:

* **Linux / WSL:** `sudo apt-get install ffmpeg`
* **macOS:** `brew install ffmpeg`

### 2.2 Create the Host Virtual Environment

At the root of your local project repository, create a dedicated `.venv-host` environment:

```bash
python3 -m venv .venv-host
source .venv-host/bin/activate
pip install -r requirements_host.txt
```

---

## 3. Audio Normalization

To prevent sudden volume spikes when children switch between different MP3 tracks, the project includes an automated audio normalizer.

1. Ensure your host virtual environment is active.
2. Place all new MP3s in their respective folders inside `./music/`.
3. Run the normalization script:

```bash
   chmod +x scripts/normalize_audio.sh
   ./scripts/normalize_audio.sh
```

This script will automatically back up your music folder to `./backups/` and apply dynamic range compression to standardize the volume of all tracks at 44.1 kHz.

---

## 4. Deployment via VS Code

This repository utilizes automated VS Code Tasks to push updates over SSH via `rsync`, doing all the heavy lifting for you so you never have to manually copy files.

### 4.1 Configure Your Local Tasks
To prevent committing personal network details to version control, the deployment tasks are stored in a template folder. 

1. Copy the `.vscode-template` folder and rename the copy to `.vscode` (which is ignored by Git).
```bash
   cp -r .vscode-template .vscode
```

2. Open `.vscode/tasks.json` in your editor.
3. Replace all instances of `[USER]` with your Raspberry Pi's username.
4. Replace all instances of `[PI_IP_ADDRESS]` with your Raspberry Pi's actual IP address (e.g., `192.168.2.40`).

### 4.2 Running the Tasks

Once configured, open the VS Code Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`), select **Tasks: Run Task**, and choose one of the automated workflows:

* **`Deploy Code (rsync)`:** Pushes all application code, service files, and scripts to the Pi. It strictly ignores local `.venv/`, `.venv-host/`, and `music/` directories to protect your embedded environment. *(Note: You can also trigger this instantly by pressing `Ctrl+Shift+B` or `Cmd+Shift+B`)*.
* **`Sync Music Directory (rsync)`:** Bypasses your Git rules to scan your local `./music/` directory and incrementally uploads only new or newly normalized audio files directly to the Pi.
* **`Normalize Music (Host)`:** Automatically backs up your audio files and runs the `ffmpeg-normalize` script to dynamically compress and balance the volume of all tracks before you sync them to the Pi.
