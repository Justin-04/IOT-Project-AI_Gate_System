"""
mqtt_handler.py
---------------
Manages the MQTT connection to the cloud broker.
Handles incoming messages for:
- Remote control commands (open gate, reboot, shutdown)
- User enrollment (add new face to database)
- User deletion (remove face from database)
"""

import os
import json
import time
import base64
import threading

import paho.mqtt.client as mqtt

from config import CLOUD_IP, AUTH_FOLDER, T_CTRL, T_ADD, T_DEL
from hardware import ui
from face_db import reload_db
from access_control import grant

# --- MQTT Client Instance ---
client = mqtt.Client()


def on_message(client_ref, userdata, msg):
    """
    Callback invoked when a message arrives on any subscribed topic.

    Handles three categories:
        1. T_ADD  — Enroll a new user (saves image, reloads face DB)
        2. T_DEL  — Delete a user (removes image, reloads face DB)
        3. T_CTRL — Execute a remote command (OPEN, REBOOT_PI, SHUTDOWN_PI)

    Args:
        client_ref: The MQTT client instance (unused, we use the module-level `client`)
        userdata: User-defined data (unused)
        msg: The received MQTTMessage with .topic and .payload
    """
    try:
        # --- User Management (JSON payloads) ---
        if msg.topic in [T_ADD, T_DEL]:
            data = json.loads(msg.payload.decode())
            target_name = data['name'].lower()

            if msg.topic == T_ADD:
                # Decode the base64 image and save to the authorized users folder
                filepath = os.path.join(AUTH_FOLDER, f"{target_name}.jpg")
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(data['image']))
                print(f"📥 Enrolled file: {target_name}.jpg")
                # Reload face database in background to avoid blocking MQTT loop
                threading.Thread(target=reload_db).start()

            elif msg.topic == T_DEL:
                # Remove the user's image file from disk
                filepath = os.path.join(AUTH_FOLDER, f"{target_name}.jpg")
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"🗑️ Deleted file from storage: {target_name}.jpg")
                else:
                    print(f"⚠️ Target file {target_name}.jpg not found.")
                # Reload face database in background
                threading.Thread(target=reload_db).start()

        # --- Remote Control Commands (plain string payloads) ---
        elif msg.topic == T_CTRL:
            cmd = msg.payload.decode().strip()

            if cmd == "OPEN":
                # Remotely trigger gate open (admin override)
                grant("Admin", "Remote", client)

            elif cmd == "REBOOT_PI":
                ui("SYSTEM REBOOT", "Initiating...")
                time.sleep(2)
                os.system("sudo reboot")

            elif cmd == "SHUTDOWN_PI":
                ui("SYSTEM OFF", "Safe to unplug")
                time.sleep(2)
                os.system("sudo poweroff")

    except Exception as e:
        print(f"MQTT Message Error: {e}")


# Register the message callback
client.on_message = on_message


def start_mqtt():
    """
    Connect to the MQTT broker and subscribe to control topics.
    Runs in a daemon thread so it doesn't block the main camera loop.
    The loop_forever() call handles reconnection automatically.
    """
    def worker():
        try:
            client.connect(CLOUD_IP, 1883)
            client.subscribe([
                (T_CTRL, 0),
                (T_ADD, 0),
                (T_DEL, 0)
            ])
            client.loop_forever()
        except Exception as e:
            print(f"MQTT Worker Failure: {e}")

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
