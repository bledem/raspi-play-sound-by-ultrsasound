# Proximity-Based Music Player

This project uses an HC-SR04 ultrasonic distance sensor connected to a Raspberry Pi to play music when someone approaches within a certain distance.

## Features

- Detects people within 1 meter using an HC-SR04 ultrasonic sensor
- Applies a low-pass filter to smooth distance measurements
- Plays random music from a directory when someone is detected
- Stops music when the person moves away
- Prevents music from playing continuously by requiring rearm
- Logs distance measurements for analysis

## Hardware Requirements

- Raspberry Pi (any model with GPIO pins)
- HC-SR04 Ultrasonic Distance Sensor
- Jumper wires
- Speakers or headphones (connected to Raspberry Pi)

## Wiring

Connect the HC-SR04 sensor to your Raspberry Pi as follows:

- HC-SR04 VCC → Raspberry Pi 5V
- HC-SR04 GND → Raspberry Pi GND
- HC-SR04 TRIG → Raspberry Pi GPIO 27 (BCM)
- HC-SR04 ECHO → Raspberry Pi GPIO 17 (BCM)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/bledem/raspi-play-sound-by-ultrsasound
   cd raspi-play-sound-by-ultrsasound 
   ```

2. Install required dependencies in a new environment:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the script
    ```bash
    sudo SDL_AUDIODRIVER=alsa AUDIODEV=hw:0,0 env/bin/python main.py
    ```
    `sudo` for GPio and `SDL_AUDIODRIVER=alsa AUDIODEV=hw:0,0` to access the music player. 

## Usage

Run the program with the helper script to ensure proper audio access:

```bash
sudo SDL_AUDIODRIVER=alsa AUDIODEV=hw:0,0 env/bin/python main.py
```

The program will:
1. Continuously measure the distance to objects in front of the sensor
2. Play a random song when someone comes within 1 meter
3. Stop the music when the person moves away
4. Wait for the person to leave before allowing another song to play

Press `Ctrl+C` to exit the program.

## Troubleshooting

### Audio Issues

If you encounter audio problems, try:
- Ensure your audio device is properly connected and configured
- Check that you have audio files in the `data` directory

### Sensor Issues

If the sensor doesn't work correctly:
- Check your wiring connections
- Verify the GPIO pin numbers in the code match your wiring
- Ensure the sensor has proper 5V power

## License

[MIT License](LICENSE)
