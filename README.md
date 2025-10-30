PyQt6 Analog Clock:

A frameless analog clock application built with PyQt6.
It displays the current time, date, and battery level with a simple, modern interface.

Features:

Real-time hour, minute, and second hands
Battery level ring with charging indicator

Date display:

Timezone support (local and custom)

Custom color themes:

Always-on-top and system tray options
Frameless, draggable window

Requirements:

Python 3.9 or later

Install dependencies:

pip install PyQt6 psutil

Run:

python app.py

Project Structure:

CLOCK/
│
├─ app.py          # Main application file
├─ Requirements.txt # Project modules to install  
└─ README.md       # Project documentation

Configuration:

All visual settings (colors, font sizes, tick spacing, etc.) can be adjusted inside the WatchWidget class in app.py.
The clock uses Python’s built-in zoneinfo module for timezone handling.
No external assets or configuration files are required.

Tested On:

Windows 10 / 11
Python 3.10 – 3.12
PyQt6 6.7+
psutil 6.0+

Author:

Nishank