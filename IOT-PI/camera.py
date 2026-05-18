"""
camera.py
---------
Handles the Kinect camera frame processing loop.
Each frame triggers:
1. Gate state machine transitions (open/close timing)
2. RFID card scanning
3. Face detection and recognition via the AI model
"""

import time
import cv2
import face_recognition

from config import RFID_ADMIN
from hardware import ui, set_led, servo_open, servo_close, solenoid, reader
from face_db import db_loading, db_lock, known_encodings, known_names
from access_control import grant, deny, state, timer
from mqtt_handler import client

# We need to modify state/timer from access_control, so import the module directly
import access_control


def process_frame(dev, data, timestamp):
    """
    Callback invoked by freenect for every video frame from the Kinect sensor.

    This function implements a state machine:
        SCANNING         → Check RFID, then check faces in frame
        WAIT_OPEN        → Pause before physically opening the gate
        OPEN             → Gate is open, countdown displayed on LCD
        DENIED_COOLDOWN  → Brief pause after denial before resuming

    Args:
        dev: Freenect device handle (unused directly)
        data: Raw RGB frame data from the Kinect (numpy array)
        timestamp: Frame timestamp from the sensor
    """
    # Skip processing while the face database is being reloaded
    if db_loading:
        return

    now = time.time()

    # --- State: WAIT_OPEN ---
    # Access was granted; after a short delay, physically open the gate
    if access_control.state == "WAIT_OPEN" and now >= access_control.timer:
        servo_open()
        solenoid(True)  # Energize solenoid to release lock
        access_control.timer = now + 5
        access_control.state = "OPEN"

    # --- State: OPEN ---
    # Gate is open; show countdown on LCD, then close when timer expires
    elif access_control.state == "OPEN":
        if now >= access_control.timer:
            servo_close()
            solenoid(False)  # De-energize solenoid to re-lock
            set_led("GRN", False)
            access_control.state = "SCANNING"
        else:
            remaining = int(access_control.timer - now)
            ui("GATE OPEN", f"Closes in {remaining}s")

    # --- State: DENIED_COOLDOWN ---
    # Wait briefly after a denial before resuming scanning
    elif access_control.state == "DENIED_COOLDOWN":
        if now >= access_control.timer:
            access_control.state = "SCANNING"

    # --- State: SCANNING ---
    # Actively check for RFID cards and faces
    elif access_control.state == "SCANNING":
        set_led("RED", True)
        set_led("GRN", False)

        # --- Step 1: RFID Check ---
        # Non-blocking read; returns None if no card is present
        rid, _ = reader.read_no_block()
        if rid:
            if rid == RFID_ADMIN:
                grant("Admin", "RFID", client)
            else:
                deny("Invalid Card", "RFID", client)
            return

        # --- Step 2: Face Recognition ---
        # Downscale frame to 25% for faster face detection
        small_frame = cv2.resize(data, (0, 0), fx=0.25, fy=0.25)
        face_locations = face_recognition.face_locations(small_frame)

        if face_locations:
            # Compute encodings for all detected faces
            face_encs = face_recognition.face_encodings(small_frame, face_locations)
            any_matched = False

            # Thread-safe read of the face database
            with db_lock:
                for encoding in face_encs:
                    matches = face_recognition.compare_faces(known_encodings, encoding)
                    if True in matches:
                        # Find the name corresponding to the first match
                        matched_name = known_names[matches.index(True)]
                        grant(matched_name, "Face AI", client)
                        any_matched = True
                        return  # Exit early on first successful match

            # If faces were detected but none matched the database
            if not any_matched:
                deny("Unknown Face", "Face AI", client)
                return
