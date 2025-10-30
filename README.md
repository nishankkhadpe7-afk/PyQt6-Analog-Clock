PyQt6 Analog Clock:

A frameless analog clock application built with PyQt6.
It displays the current time, date, and battery level with a simple, modern interface.

Features:

 1. Real-time hour, minute, and second hands
 2. Battery level ring with charging indicator
 3. Date display
 4. Timezone support (local and custom)
 5. Custom color themes
 6. Always-on-top and system tray options
 7. Frameless, draggable window

Requirements:

Python 3.9 or later

Installation:

 1. Clone or download the project folder.
 2. Open a terminal or command prompt in the project directory.
 3. Install the required modules using:
    pip install -r requirements.txt
    (This will automatically install PyQt6, psutil, and tzdata.)

Run:

python app.py

Project Structure:

CLOCK
 │
 ├─ app.py            # Main application file
 ├─ requirements.txt  # Project dependencies
 └─ README.md         # Project documentation

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
