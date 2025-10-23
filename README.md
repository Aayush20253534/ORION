# ORION AI Assistant


## Overview

ORION is a Python-based AI assistant with both voice and text command capabilities, a sci-fi GUI, real-time system stats, and integration with OpenAI's GPT API for intelligent responses.

It can open applications, browse websites, set reminders, manage system operations, and perform multimedia actions.

---

## Features

* Voice and text command recognition
* Real-time system monitoring (CPU, Memory, Disk, Battery, Location)
* Sci-fi orbital GUI animations
* Clipboard management
* File search and opening
* Media playback from a library
* AI responses via OpenAI GPT
* Reminders and notifications
* Dark-themed GUI built with `customtkinter`

---

## Installation

### Requirements

* Python 3.10+
* pip packages:

```bash
pip install customtkinter SpeechRecognition pyttsx3 gTTS pygame pyperclip openai psutil pillow opencv-python requests
```

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/orion-ai.git
```

2. Navigate to the project directory:

```bash
cd orion-ai
```

3. Replace `YOUR_OPENAI_KEY_HERE` in the main script with your OpenAI API key.

4. Run the application:

```bash
python main.py
```

---

## Usage

* **Voice Commands:** Speak into the microphone. Examples:

  * "Open youtube"
  * "Remind me to call in 10"
  * "Find file report"

* **Text Commands:** Type in the input box and press Enter.

* **System Operations:** Shutdown, restart, lock, log off

* **Media:** Play songs via predefined library

* **AI:** Ask natural language questions, ORION responds intelligently

---

## File Structure

```
orion-ai/
├─ main.py            # Main application script
├─ musicLibrary.py    # Optional music library
├─ README.pdf         # This document
├─ client.py          # For AI integration

```

---

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature-name`)
3. Make your changes
4. Commit (`git commit -m 'Add feature'`)
5. Push (`git push origin feature-name`)
6. Open a Pull Request

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

---

## Acknowledgements

* [OpenAI](https://openai.com/) for GPT API
* [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for modern GUI components
* Python community and libraries used in this project
