"""
main.py
-------
Entry point for the AI Security Gate system.

This script:
1. Loads the face recognition database from disk
2. Starts the MQTT listener (background thread)
3. Launches the Kinect camera loop for real-time scanning

Hardware requirements:
- Microsoft Kinect sensor (via libfreenect)
- MFRC522 RFID reader (via SPI)
- 16x2 HD44780 LCD (via GPIO)
- Servo motor, solenoid lock, LEDs, buzzer (via GPIO)

Usage:
    sudo python3 main.py
"""

import freenect

from face_db import reload_db
from mqtt_handler import start_mqtt
from camera import process_frame
from hardware import cleanup


def main():
    """
    Initialize all subsystems and start the main processing loop.
    """
    # Step 1: Load authorized faces from disk into memory
    print("Loading face database...")
    reload_db()

    # Step 2: Connect to MQTT broker and start listening for commands
    print("Starting MQTT listener...")
    start_mqtt()

    # Step 3: Start the Kinect video loop
    # freenect.runloop calls process_frame for every video frame
    print("Starting Kinect camera loop...")
    try:
        freenect.runloop(video=process_frame)
    except KeyboardInterrupt:
        print("\nStopping AI Gate System safely...")
    finally:
        # Ensure all hardware is cleanly shut down on exit
        cleanup()


if __name__ == "__main__":
    main()
