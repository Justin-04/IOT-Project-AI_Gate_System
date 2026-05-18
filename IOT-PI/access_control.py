"""
access_control.py
-----------------
Handles the grant/deny logic for access events.
Controls LEDs, buzzer, LCD feedback, and publishes log events via MQTT.
"""

import time
import json

from config import T_LOGS
from hardware import ui, set_led, buzz

# --- Gate State Machine ---
# Possible states:
#   "SCANNING"         — actively checking RFID and camera
#   "WAIT_OPEN"        — access granted, waiting before opening gate
#   "OPEN"             — gate is physically open, countdown to close
#   "DENIED_COOLDOWN"  — access denied, brief pause before resuming scan
state = "SCANNING"

# Timestamp (epoch) when the current state should transition
timer = 0


def grant(user, method, mqtt_client):
    """
    Handle a successful access event.

    Actions:
        1. Turn on green LED, turn off red LED
        2. Display user name on LCD
        3. Short buzzer beep
        4. Publish GRANTED log to MQTT
        5. Transition to WAIT_OPEN state

    Args:
        user: Name of the authorized person
        method: How they were identified ("Face AI", "RFID", "Remote")
        mqtt_client: Connected MQTT client for publishing logs
    """
    global state, timer

    set_led("RED", False)
    set_led("GRN", True)
    ui("ACCESS GRANTED", user)
    buzz("grant")

    # Publish structured log event to the cloud
    mqtt_client.publish(T_LOGS, json.dumps({
        "user": user,
        "status": "GRANTED",
        "method": method
    }))

    # Transition: wait 2 seconds before physically opening the gate
    timer = time.time() + 2
    state = "WAIT_OPEN"


def deny(reason, method, mqtt_client):
    """
    Handle a failed access attempt.

    Actions:
        1. Turn on red LED, turn off green LED
        2. Display denial reason on LCD
        3. Double buzzer beep
        4. Publish DENIED log to MQTT
        5. Transition to DENIED_COOLDOWN state

    Args:
        reason: Short description shown on LCD (e.g. "Unknown Face")
        method: Detection method that triggered the denial
        mqtt_client: Connected MQTT client for publishing logs
    """
    global state, timer

    set_led("GRN", False)
    set_led("RED", True)
    ui("ACCESS DENIED", reason)
    buzz("deny")

    # Publish structured log event to the cloud
    mqtt_client.publish(T_LOGS, json.dumps({
        "user": "Unknown",
        "status": "DENIED",
        "method": method
    }))

    # Transition: cooldown for 2 seconds before resuming scanning
    timer = time.time() + 2
    state = "DENIED_COOLDOWN"
