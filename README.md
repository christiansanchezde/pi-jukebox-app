# pi-jukebox-app
This is the applicaiton repo for the jukebox



## preapre the envitronment

sudo apt-get update
sudo apt-get install vlc python3-venv
sudo apt-get install python3-dev build-essential


cd /home/chris/jukebox
python3 -m venv .venv

source .venv/bin/activate
pip install -r requirements.txt

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