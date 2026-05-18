"""
face_db.py
----------
Manages the local face recognition database.
Loads authorized user images from disk, computes face encodings,
and provides thread-safe access to the encoding arrays.
"""

import os
import time
import threading
import face_recognition

from config import AUTH_FOLDER
from hardware import ui

# --- Face Database State ---
# These lists hold the 128-dimensional face encodings and corresponding names
known_encodings = []
known_names = []

# Flag to indicate when the database is being reloaded (pauses scanning)
db_loading = False

# Thread lock to prevent race conditions when the face arrays are
# being swapped during a reload while the camera loop is reading them
db_lock = threading.Lock()


def reload_db():
    """
    Scan the authorized_users folder, compute face encodings for each image,
    and atomically swap the in-memory database.

    This function is safe to call from a background thread. While it runs,
    the `db_loading` flag is set to True, which pauses the camera processing loop.
    """
    global known_encodings, known_names, db_loading

    db_loading = True
    ui("SYNCING...", "Please wait")
    time.sleep(0.5)

    new_encodings = []
    new_names = []

    # Ensure the storage folder exists
    if not os.path.exists(AUTH_FOLDER):
        os.makedirs(AUTH_FOLDER)

    # Iterate over all image files in the authorized users folder
    for filename in os.listdir(AUTH_FOLDER):
        if filename.lower().endswith((".jpg", ".png")):
            try:
                filepath = os.path.join(AUTH_FOLDER, filename)
                img = face_recognition.load_image_file(filepath)
                encodings = face_recognition.face_encodings(img)

                if encodings:
                    new_encodings.append(encodings[0])
                    # Use the filename (without extension) as the display name
                    name = os.path.splitext(filename)[0].capitalize()
                    new_names.append(name)
            except Exception as e:
                print(f"Error parsing image file {filename}: {e}")

    # Atomically swap the database using a thread-safe lock
    with db_lock:
        known_encodings = new_encodings
        known_names = new_names

    db_loading = False
    ui("AI SECURITY", "READY")
    print(f"Face DB loaded: {len(known_names)} user(s)")
