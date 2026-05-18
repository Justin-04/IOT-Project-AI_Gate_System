"""
hardware.py
-----------
Initializes and provides helper functions for all physical hardware:
- GPIO pins (LEDs, buzzer, solenoid)
- Servo motor (PWM-controlled gate arm)
- 16x2 LCD display (HD44780 via GPIO)
- MFRC522 RFID reader
"""

import RPi.GPIO as GPIO
from RPLCD.gpio import CharLCD
from mfrc522 import SimpleMFRC522

from config import PINS, DUTY_CLOSED

# --- GPIO Initialization ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set all defined pins as outputs
for pin in PINS.values():
    GPIO.setup(pin, GPIO.OUT)

# --- Servo Motor Setup ---
# 50Hz PWM signal on the servo pin (standard for hobby servos)
pwm = GPIO.PWM(PINS["SRV"], 50)
pwm.start(DUTY_CLOSED)  # Start in the closed/locked position

# --- LCD Display Setup ---
# 4-bit mode HD44780 LCD connected via GPIO pins
lcd = CharLCD(
    pin_rs=25,
    pin_e=24,
    pins_data=[23, 17, 18, 22],
    numbering_mode=GPIO.BCM,
    cols=16,
    rows=2
)

# --- RFID Reader Setup ---
reader = SimpleMFRC522()


def ui(line1, line2=""):
    """
    Display two lines of text on the 16x2 LCD.
    Each line is truncated to 16 characters to prevent overflow.

    Args:
        line1: Text for the top row
        line2: Text for the bottom row (optional)
    """
    lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string(line1[:16])
    lcd.cursor_pos = (1, 0)
    lcd.write_string(line2[:16])


def set_led(color, state):
    """
    Turn an LED on or off.

    Args:
        color: "RED" or "GRN"
        state: True (on) or False (off)
    """
    GPIO.output(PINS[color], state)


def buzz(pattern="grant"):
    """
    Activate the buzzer with a predefined pattern.

    Args:
        pattern: "grant" for a single short beep, "deny" for two rapid beeps
    """
    import time

    if pattern == "grant":
        GPIO.output(PINS["BUZ"], True)
        time.sleep(0.2)
        GPIO.output(PINS["BUZ"], False)
    elif pattern == "deny":
        for _ in range(2):
            GPIO.output(PINS["BUZ"], True)
            time.sleep(0.1)
            GPIO.output(PINS["BUZ"], False)
            time.sleep(0.1)

def servo_open():
    """Rotate the servo to the open position (~190 degrees)."""
    from config import DUTY_OPEN
    pwm.ChangeDutyCycle(DUTY_OPEN)


def servo_close():
    """Rotate the servo back to the closed position (~90 degrees)."""
    pwm.ChangeDutyCycle(DUTY_CLOSED)


def cleanup():
    """
    Safely shut down all hardware interfaces.
    Should be called on program exit to reset GPIO pins and stop PWM.
    """
    lcd.clear()
    pwm.stop()
    GPIO.cleanup()
    print("LCD Cleared, Pins Reset. Goodbye.")
