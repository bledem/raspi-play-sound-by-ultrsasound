import os
import sys
import RPi.GPIO as GPIO
import time
import pygame
import numpy as np
import random
import logging
import datetime
from scipy.signal import butter, filtfilt
from collections import deque

# Set up logging to stdout only
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


# GPIO Setup
TRIG_PIN = 27  # GPIO Pin for Trigger
ECHO_PIN = 17  # GPIO Pin for Echo

# Set GPIO mode
GPIO.setmode(GPIO.BCM)  # Use BCM mode to match the pin numbers defined above


# HC-SR04 Ultrasonic Sensor Class
class HCSR04:
    """
    Driver to use the ultrasonic sensor HC-SR04 with RPi.GPIO.
    The sensor range is between 2cm and 4m.
    """

    def __init__(self, trigger_pin, echo_pin, timeout_sec=0.03):
        """
        trigger_pin: Output pin to send pulses
        echo_pin: Input pin to measure the distance
        timeout_sec: Timeout in seconds to listen to echo pin (default 30ms which is ~5m range)
        """
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.timeout_sec = timeout_sec

        # Setup GPIO pins
        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

        # Ensure trigger is low
        GPIO.output(self.trigger_pin, False)
        time.sleep(0.05)  # Let the sensor settle

    def _send_pulse_and_wait(self):
        """Send the pulse to trigger and measure time until echo is received."""
        # Send 10us pulse
        GPIO.output(self.trigger_pin, True)
        time.sleep(0.00001)  # 10us pulse
        GPIO.output(self.trigger_pin, False)

        pulse_start = time.time()
        pulse_end = time.time()

        # Wait for echo to go high
        timeout_start = time.time()
        while GPIO.input(self.echo_pin) == 0:
            pulse_start = time.time()
            if time.time() - timeout_start > self.timeout_sec:
                return None  # Timeout waiting for echo

        # Wait for echo to go low
        timeout_start = time.time()
        while GPIO.input(self.echo_pin) == 1:
            pulse_end = time.time()
            if time.time() - timeout_start > self.timeout_sec:
                return None  # Timeout waiting for echo

        # Calculate pulse duration
        pulse_duration = pulse_end - pulse_start
        return pulse_duration

    def distance_cm(self):
        """
        Get the distance in centimeters.
        Returns None if measurement failed or out of range.
        """
        pulse_duration = self._send_pulse_and_wait()

        if pulse_duration is None:
            return 400.0  # Return max range on timeout

        # Speed of sound is 34300 cm/s
        # Distance = (time * speed) / 2 (round trip)
        distance = (pulse_duration * 34300) / 2

        # Sensor has a range of 2cm to 400cm
        if distance < 2:
            return 2.0
        elif distance > 400:
            return 400.0

        return distance


# Initialize the HC-SR04 sensor
sensor = HCSR04(TRIG_PIN, ECHO_PIN)

# Music Directory
MUSIC_DIR = "./data"  # Change this to your folder path

# Initialize pygame for audio playback with error handling
audio_available = True
try:
    pygame.mixer.init()
except pygame.error as e:
    print(f"Warning: Audio initialization failed: {e}")
    print("Running without audio capabilities.")
    audio_available = False


# Low-Pass Filter Function
def low_pass_filter(data, cutoff=1.0, fs=10.0, order=2):
    """Applies a Butterworth low-pass filter to smooth distance readings."""
    # Convert deque to numpy array
    data_array = np.array(data)

    # Simple moving average if data is too short for filtfilt
    if len(data_array) < 15:  # Ensure we have enough data points
        return np.array([np.mean(data_array)])

    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    try:
        return filtfilt(b, a, data_array)
    except ValueError:
        # Fallback to moving average if filtfilt fails
        return np.array([np.mean(data_array)])


# Function to measure distance from HC-SR04
def get_distance():
    return sensor.distance_cm()


# Function to play a random song
def play_random_song():
    if not audio_available:
        print("Would play music here (audio disabled)")
        return

    if not pygame.mixer.music.get_busy():  # Only play if nothing is playing
        songs = [
            f for f in os.listdir(MUSIC_DIR) if f.endswith((".mp3", ".wav", ".ogg"))
        ]
        if songs:
            song = random.choice(songs)
            pygame.mixer.music.load(os.path.join(MUSIC_DIR, song))
            pygame.mixer.music.play()
            print(f"Playing: {song}")


# Function to stop the song
def stop_music():
    if not audio_available:
        print("Would stop music here (audio disabled)")
        return
    pygame.mixer.music.stop()
    print("Music stopped.")


# Main loop
try:
    # Use a deque with max size of 30 for the history
    history = deque([200.0] * 30, maxlen=30)  # Initialize with high values (no person)
    person_detected = False
    detection_start = None
    need_rearm = False  # Flag to track if we need to wait for person to leave before playing again

    while True:
        raw_distance = get_distance()
        # Add to the deque (which automatically handles removing old elements)
        history.append(raw_distance)

        # Try to apply filter, fall back to simple average if it fails
        try:
            filtered_distance = low_pass_filter(history)[-1]
        except Exception as e:
            logging.warning(f"Filter error: {e}, using raw value")
            filtered_distance = raw_distance  # Use raw value if filtering fails

        # For stdout logging, use the logging module
        logging.info(
            f"Distance: {raw_distance:.2f} cm, Filtered: {filtered_distance:.2f} cm, Need Rearm: {need_rearm}"
        )

        if filtered_distance < 100:  # Person detected within 1 meter
            if not person_detected:
                detection_start = time.time()
                person_detected = True
            elif time.time() - detection_start > 0.5:  # Ensure presence for 0.5s
                if not need_rearm:  # Only play if we don't need to rearm
                    play_random_song()
                    need_rearm = (
                        True  # Set flag to prevent playing again until person leaves
                    )
        else:
            person_detected = False
            stop_music()
            need_rearm = False  # Reset the rearm flag when person is no longer detected

        time.sleep(0.1)  # Small delay for smoother operation

except KeyboardInterrupt:
    print("Exiting program.")
    GPIO.cleanup()
    pygame.mixer.quit()
