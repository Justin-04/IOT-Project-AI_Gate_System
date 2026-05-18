"""
config.py
---------
Central configuration for the AI Security Gate system.
Contains all constants, pin mappings, MQTT topics, and servo calibration values.
"""

# Cloud server IP (OCI instance running the MQTT broker and web API)
CLOUD_IP = "xxx.xxx.xxx.xxx"

# Local folder where authorized user face images are stored
AUTH_FOLDER = "authorized_users"

# The RFID tag UID that grants admin access
RFID_ADMIN = xxxxxxxxxxxx

# --- MQTT Topics ---
# Topic for publishing access log events (granted/denied)
T_LOGS = "security/logs"
# Topic for receiving remote control commands (OPEN, REBOOT, SHUTDOWN)
T_CTRL = "security/control"
# Topic for receiving new user enrollment data (name + base64 image)
T_ADD = "security/add_user"
# Topic for receiving user deletion requests
T_DEL = "security/delete_user"

# --- GPIO Pin Assignments (BCM numbering) ---
PINS = {
    "RED": 5,    # Red LED — indicates scanning / denied state
    "GRN": 6,    # Green LED — indicates access granted
    "BUZ": 21,   # Piezo buzzer — audio feedback
    "SOL": 26,   # Solenoid lock — energize to unlock
    "SRV": 12,   # Servo motor — rotates gate arm
}

# --- Servo Duty Cycle Calibration ---
# These values map to physical angles on the servo:
# DUTY_CLOSED ~= 90 degrees (gate arm down / locked)
# DUTY_OPEN   ~= 190 degrees (gate arm up / open)
DUTY_CLOSED = 6.5
DUTY_OPEN = 2.5
