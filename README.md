# ESP-Car-Remote-Simulator

This repository contains the Python-based GUI simulator for the ESP-Car-Remote project. This simulator allows for testing the ESP32 firmware functionalities (both Arduino and ESP-IDF versions) by emulating button presses and joystick movements, and also provides a real-time audio visualization for the microphone-enabled ESP-IDF project.

## Features

-   **Virtual Joystick & Buttons:** Simulate input from a physical remote control.
-   **Serial Communication:** Connects to the ESP32 via a serial (COM) port to send commands and receive data.
-   **Real-time Audio Playback:** For the ESP-IDF microphone project, it receives raw audio data over serial and plays it through your computer's speakers.
-   **Audio Visualizer (VU Meter):** Displays the real-time audio level received from the ESP32 microphone.
-   **Cross-platform:** Developed using Python and Tkinter, making it compatible with Windows, macOS, and Linux.

## Prerequisites

Before running the simulator, ensure you have Python 3 installed on your system.
You will also need to install the following Python libraries:

```bash
pip install pyserial PyAudio numpy
```

**Note on PyAudio:**
Installing `PyAudio` can sometimes be challenging, especially on Windows, due to its dependency on PortAudio. If `pip install PyAudio` fails, you might need to:
1.  Install PortAudio development libraries manually.
2.  Find a pre-compiled wheel file (`.whl`) for your Python version and operating system (e.g., `PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl`) from unofficial sources like [Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/).
3.  Install the wheel file using `pip install path/to/your/PyAudio‑*.whl`.

## Usage

1.  **Clone this repository:**
    ```bash
    git clone https://github.com/alazndy/ESP-Car-Remote-Simulator.git
    cd ESP-Car-Remote-Simulator
    ```
2.  **Install Python dependencies** (as described in Prerequisites).
3.  **Ensure your ESP32 is programmed** with the appropriate firmware (either Arduino or ESP-IDF microphone streamer) and connected to your computer via USB.
4.  **Run the simulator:**
    ```bash
    python esp32_controller_gui.py
    ```
5.  **Connect to ESP32:** A connection window will appear. Select the COM port to which your ESP32 is connected and click "Bağlan" (Connect).
6.  **Interact:**
    *   **Joystick:** Drag the joystick knob to send directional commands (W, A, S, D). Double-click the joystick area to send an "Enter/Select" command (T).
    *   **Buttons:** Click the virtual buttons to send corresponding commands (e.g., Play/Pause, Volume Up/Down).
    *   **Microphone (ESP-IDF version only):** If your ESP32 is running the ESP-IDF microphone streamer, you should hear the microphone input through your computer's speakers, and the "Mikrofon Ses Seviyesi" (Microphone Volume Level) VU meter will visualize the audio intensity.

## Contributing

Contributions to improve the simulator are welcome! Please feel free to open issues or submit pull requests.

## License

This project is distributed under the MIT License.
