# pi-jukebox-app
This is the applicaiton repo for the jukebox



## preapre the envitronment

sudo apt-get update
sudo apt-get install vlc python3-venv
sudo apt-get install liblgpio-dev
sudo apt-get install python3-dev build-essential


cd /home/chris/jukebox
python3 -m venv .venv

source .venv/bin/activate
pip install -r requirements.txt
pip install gpiozero lgpio


## Enable spi port

Step 1: Enable SPI via raspi-config
Run this command in your Raspberry Pi SSH terminal:

Bash
sudo raspi-config
This will open a text-based menu. Navigate using your arrow keys and the Enter key:

Go down to 3 Interface Options and press Enter.

Go down to I4 SPI and press Enter.

It will ask: "Would you like the SPI interface to be enabled?" Select .

You will see a confirmation saying "The SPI interface is enabled". Press Enter.

Use the Right Arrow key to select  at the bottom of the main menu.


## Installign the services

To ensure your Jukebox is a true "plug-and-play" embedded device, we will create two separate `systemd` service files.

One service will run the main application as your standard user (to ensure audio routing works correctly), and the other will run the shutdown listener as `root` (since shutting down the system requires administrator privileges).

### 1. Create the Files in Your VS Code Project

To keep your project repository clean and version-controlled, you should store these configuration files in your `scripts/` folder.

**File 1: `scripts/pi-jukebox.service**`

```ini
[Unit]
Description=Pi Jukebox RFID Application
After=network.target sound.target

[Service]
Type=simple
User=chris
WorkingDirectory=/home/chris/jukebox
# Execute our dynamic bash script
ExecStart=/bin/bash /home/chris/jukebox/scripts/start.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

```

**File 2: `scripts/pi-shutdown.service**`

```ini
[Unit]
Description=Pi Jukebox Hardware Shutdown Button
After=multi-user.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/chris/jukebox
# Point directly to the virtual environment's Python and the script
ExecStart=/home/chris/jukebox/.venv/bin/python /home/chris/jukebox/src/shutdown.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

```

### 2. Deploy and Install on the Raspberry Pi

1. Save these files locally and press `Ctrl+Shift+B` (or `Cmd+Shift+B`) to run your **Deploy Code (rsync)** task.
2. SSH into your Raspberry Pi.
3. Linux `systemd` requires service files to live in a very specific system folder: `/etc/systemd/system/`. Run these commands to copy the files from your project directory into the system directory:

```bash
# Copy the service files to the systemd directory
sudo cp /home/chris/jukebox/scripts/pi-jukebox.service /etc/systemd/system/
sudo cp /home/chris/jukebox/scripts/pi-shutdown.service /etc/systemd/system/

# Set the correct permissions for the service files
sudo chmod 644 /etc/systemd/system/pi-jukebox.service
sudo chmod 644 /etc/systemd/system/pi-shutdown.service

```

### 3. Enable and Start the Services

Now we tell the operating system to reload its configuration, enable the scripts to run on boot, and start them immediately. Run these commands in your SSH terminal:

```bash
# Tell systemd to recognize the new files
sudo systemctl daemon-reload

# Enable them to start automatically every time the Pi boots up
sudo systemctl enable pi-jukebox.service
sudo systemctl enable pi-shutdown.service

# Start them right now in the background
sudo systemctl start pi-jukebox.service
sudo systemctl start pi-shutdown.service

```

### 4. Verification

You can check the health of your services at any time using the `status` command.

```bash
sudo systemctl status pi-jukebox.service
sudo systemctl status pi-shutdown.service

```

*(Press `q` to exit the status view).*

---

Once you have these running, the Pi will operate entirely headless—if you pull the power plug and plug it back in, the Green LED will light up automatically once it finishes booting, ready for a tag.

Would you like to perform a hard reboot (`sudo reboot`) to verify the fully automated startup sequence works exactly as intended?

chmod +x scripts/normalize_audio.sh
