# AI Security Gate System

A Raspberry Pi-powered access control system that uses **face recognition** and **RFID** to manage physical gate access. Connected to a cloud dashboard via MQTT for remote monitoring and control.

## Architecture Overview

Raspberry Pi (Kinect + RFID + Servo/LCD) -> MQTT -> Oracle Cloud VM (Backend on port 3000 + Frontend on port 80) -> MongoDB

| Folder | Role |
|--------|------|
| `IOT-PI/` | Raspberry Pi code — face recognition, RFID scanning, gate control |
| `backend/` | Express.js API — stores logs/users in MongoDB, relays MQTT commands, sends email alerts |
| `my-react-app/` | React dashboard — view access logs, enroll/remove users, remote gate control |

---

## Backend (`backend/`)

Node.js/Express server hosted on Oracle Cloud. Stores access logs and users in MongoDB, subscribes to MQTT to persist events from the Pi, publishes commands back to it, and sends email alerts on denied access via Nodemailer.

```bash
cd backend
npm install
node server.js
```

Requires a `.env` file with `MONGO_URI`, `EMAIL_USER`, and `EMAIL_PASS`.

---

## Frontend (`my-react-app/`)

React (Vite) dashboard for viewing access history, enrolling/removing users, and remotely opening the gate.

```bash
cd my-react-app
npm install
npm run build
docker build -t security-frontend .
docker run -d -p 80:80 --name frontend security-frontend
```

---

## Raspberry Pi (`IOT-PI/`)

This is the core of the project — the physical access control unit.

### Features

- **Face Recognition** — Real-time identification using a Microsoft Kinect sensor and the `face_recognition` library
- **RFID Access** — MFRC522 card reader for badge-based entry
- **Remote Control** — Open the gate, reboot, or shutdown the Pi from the cloud dashboard
- **User Enrollment** — Add/remove authorized users remotely via MQTT (no physical access needed)
- **Access Logging** — All grant/deny events published to the cloud in real time
- **LCD Feedback** — 16x2 display shows system status, user names, and countdowns
- **Auto-Lock** — Gate automatically closes after a configurable timeout

### Hardware Requirements

| Component | Purpose |
|-----------|---------|
| Raspberry Pi 3/4 | Main controller |
| Microsoft Kinect v1 | RGB camera for face detection |
| MFRC522 RFID Reader | Badge/card scanning (SPI) |
| 16x2 LCD (HD44780) | Status display (4-bit GPIO mode) |
| SG90 Servo Motor | Gate arm rotation |
| Red LED | Scanning / denied indicator |
| Green LED | Access granted indicator |
| Piezo Buzzer | Audio feedback |

### Wiring

**Red LED** — GPIO 5 to anode through a 220Ω resistor, cathode to GND.

**Green LED** — GPIO 6 to anode through a 220Ω resistor, cathode to GND.

**Piezo Buzzer** — GPIO 21 to positive terminal, negative to GND. Use an active buzzer for direct drive.

**SG90 Servo Motor** — Orange (signal) to GPIO 12 (PWM), red (VCC) to 5V, brown (GND) to GND. Add a 470µF capacitor between 5V and GND if jittering occurs.

**16x2 LCD (HD44780, 4-bit mode):**
- RS → GPIO 25
- E → GPIO 24
- D4 → GPIO 23
- D5 → GPIO 17
- D6 → GPIO 18
- D7 → GPIO 22
- VSS, RW → GND
- VDD, LED+ → 5V (LED+ through 220Ω resistor)
- LED- → GND
- V0 → 10kΩ potentiometer wiper (between 5V and GND) for contrast

**MFRC522 RFID Reader (SPI):**
- SDA → GPIO 8 (CE0)
- SCK → GPIO 11 (SCLK)
- MOSI → GPIO 10
- MISO → GPIO 9
- GND → GND
- 3.3V → 3.3V (never 5V — it will damage the module)
- RST → leave unconnected or tie to 3.3V (default library uses GPIO 25 which conflicts with LCD RS; it works fine without RST connected)

**Microsoft Kinect v1** — USB to Pi for data. Requires its own 12V power adapter (cannot be powered from USB alone). Use the proprietary USB+power splitter cable.

### Power Notes

| Component | Voltage |
|-----------|---------|
| Raspberry Pi | 5V / 3A recommended (USB-C or Micro-USB PSU) |
| Kinect | 12V dedicated AC adapter |
| Servo | 5V from Pi or external supply |
| RFID, LCD, LEDs, Buzzer | 3.3V / 5V from Pi GPIO |

If you experience brownouts (random reboots), power the servo from an external 5V supply sharing a common GND with the Pi.

### Project Structure

```
IOT-PI/
├── main.py             # Entry point — boots system, starts MQTT, launches camera
├── config.py           # Constants: IP, pins, topics, servo calibration
├── hardware.py         # GPIO, servo, LCD, RFID setup and helpers
├── face_db.py          # Face encoding database (load, reload, thread-safe access)
├── mqtt_handler.py     # MQTT connection and message handling
├── access_control.py   # Grant/deny logic and state machine
├── camera.py           # Kinect frame processing (RFID + face detection loop)
├── full-code.py        # Original monolithic script (reference only)
└── authorized_users/   # Folder for enrolled face images (auto-created)
```

### Installation

```bash
sudo apt update
sudo apt install -y python3-pip libfreenect-dev libopenblas-dev cmake
pip3 install face_recognition opencv-python numpy paho-mqtt RPi.GPIO RPLCD mfrc522 freenect
sudo raspi-config  # Interface Options → SPI → Enable
```

> `face_recognition` requires `dlib`, which can take a long time to compile on a Pi. Consider using a pre-built wheel or compiling with `-j4`.

### Usage

```bash
cd IOT-PI
sudo python3 main.py
```

### How It Works

1. **Startup** — Loads face images from `authorized_users/`, computes 128-dimensional encodings, connects to MQTT broker
2. **Scanning Loop** — Each Kinect frame is checked for RFID card taps (non-blocking) and faces (downscaled to 25% for speed)
3. **Access Decision** — If a face or card matches, the gate opens for 5 seconds
4. **Cloud Sync** — All events are published to MQTT; new users can be enrolled remotely by sending a base64-encoded image

### State Machine

```
SCANNING → (match found) → WAIT_OPEN → (2s delay) → OPEN → (5s timeout) → SCANNING
    ↓
(no match) → DENIED_COOLDOWN → (2s) → SCANNING
```

### MQTT Topics

| Topic | Direction | Payload |
|-------|-----------|---------|
| `security/logs` | Pi → Cloud | `{"user": "...", "status": "GRANTED/DENIED", "method": "..."}` |
| `security/control` | Cloud → Pi | `"OPEN"`, `"REBOOT_PI"`, or `"SHUTDOWN_PI"` |
| `security/add_user` | Cloud → Pi | `{"name": "...", "image": "<base64>"}` |
| `security/delete_user` | Cloud → Pi | `{"name": "..."}` |

### Configuration

All settings are in `config.py`:

- `CLOUD_IP` — MQTT broker address
- `AUTH_FOLDER` — Path to face image storage
- `RFID_ADMIN` — UID of the admin RFID card (obtained by scanning the card beforehand using a simple read script to retrieve its unique ID)
- `PINS` — GPIO pin mapping
- `DUTY_CLOSED` / `DUTY_OPEN` — Servo angle calibration

### Troubleshooting

| Issue | Fix |
|-------|-----|
| `RuntimeError: No access to /dev/mem` | Run with `sudo` |
| Face not detected | Ensure good lighting; check image quality in `authorized_users/` |
| RFID not reading | Verify SPI is enabled and wiring is correct |
| MQTT not connecting | Check that the broker is running and the IP is reachable |
| Servo jittering | Adjust `DUTY_CLOSED`/`DUTY_OPEN` values in `config.py` |

---

## License

Internal project — not for public distribution.
