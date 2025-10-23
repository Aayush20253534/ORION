from dotenv import load_dotenv
import os
import sys
import time
import math
import threading
import subprocess
import webbrowser
from datetime import datetime
import psutil
import cv2
from PIL import Image, ImageTk
import requests

try:
    import customtkinter as ctk
    import speech_recognition as sr
    import pyttsx3
    from gtts import gTTS
    import pygame
    import pyperclip
    import google.generativeai as genai
except Exception as e:
    print("Missing packages or import error:", e)
    print("Install dependencies: pip install customtkinter SpeechRecognition pyttsx3 gTTS pygame pyperclip openai")
    raise

try:
    import musicLibrary
except Exception:
    class DummyMusic:
        music = {"test": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"} 
    musicLibrary = DummyMusic()

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = genai.GenerativeModel("gemini-2.0-flash")

LISTENING_ACTIVE = False  
EXIT_REQUESTED = False



VOICE_RATE = 160
VOICE_VOLUME = 1.0
MALE_VOICE_INDEX = 1
WINDOW_SIZE = "1100x650"

r = sr.Recognizer()
mic = sr.Microphone()

engine = pyttsx3.init()
voices = engine.getProperty('voices')
try:
    engine.setProperty('voice', voices[MALE_VOICE_INDEX].id)
except Exception:
    pass
engine.setProperty('rate', VOICE_RATE)
engine.setProperty('volume', VOICE_VOLUME)

pygame.mixer.init()

def get_real_location():
    """
    Returns a string with city, region, country using IP-based geolocation.
    """
    try:
        response = requests.get("https://ipinfo.io/json")
        if response.status_code == 200:
            data = response.json()
            city = data.get("city", "")
            region = data.get("region", "")
            country = data.get("country", "")
            return f"{city}, {region}, {country}"
        else:
            return "Location N/A"
    except Exception as e:
        print("Error fetching location:", e)
        return "Location N/A"
    
def speak(text):
    """Primary TTS via pyttsx3, fallback to gTTS + pygame if pyttsx3 fails."""
    if not text:
        return
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception:
        try:
            tts = gTTS(text=text, lang='en')
            filename = "temp_tts.mp3"
            tts.save(filename)
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print("TTS Error:", e)

def aiProcess(command):
    """
    Uses Google Gemini 2.0 Flash for AI responses.
    """
    try:
        response = GEMINI_MODEL.generate_content(
            f"You are Orion, a helpful AI assistant. Respond clearly and naturally.\nUser: {command}"
        )
        return response.text.strip() if response.text else "I couldn't generate a response."
    except Exception as e:
        print("AI Error:", e)
        return "Sorry, I cannot process that right now."

def write_app(app_name):
    """
    Opens desktop applications using os.system without needing full paths.
    """
    app_name = app_name.lower()
    try:
        app_commands = {
            "notepad": "notepad",
            "calculator": "calc",
            "snipping tool": "snippingtool",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
            "chrome": "chrome",
            "edge": "msedge",
            "this pc": "explorer shell:MyComputerFolder",
            "network": "explorer shell:NetworkPlacesFolder",
            "recycle bin": "explorer shell:RecycleBinFolder",
            "control panel": "control",
            "windows explorer": "explorer",
            "adobe reader": "AcroRd32",  
            "zoom": r"C:\Users\LENOVO\AppData\Roaming\Zoom\bin\Zoom.exe",
        }

        command = app_commands.get(app_name)
        if command:
            os.system(f"start {command}")
        else:
            speak(f"Sorry, I don't know how to open {app_name}")
    except Exception as e:
        speak(f"Error opening {app_name}: {e}")
        
def open_folder(folder_path):
    """
    Opens a folder in Windows Explorer.
    folder_path: full path to the folder
    """
    try:
        if os.path.exists(folder_path):
            os.startfile(folder_path)
        else:
            speak(f"The folder {folder_path} does not exist.")
    except Exception as e:
        speak(f"Error opening folder: {e}")

def system_action(action):
    action = action.lower()
    try:
        if "shutdown" in action:
            os.system("shutdown /s /t 5")
            speak("Shutting down the PC.")
        elif "restart" in action:
            os.system("shutdown /r /t 5")
            speak("Restarting the PC.")
        elif "lock" in action:
            os.system("rundll32.exe user32.dll,LockWorkStation")
            speak("Locking the PC.")
        elif "log off" in action or "logoff" in action:
            os.system("shutdown /l")
            speak("Logging off.")
        else:
            speak("I cannot perform that system action.")
    except Exception as e:
        speak(f"System action error: {e}")

def search_file(file_name, search_path=r"C:\Users\LENOVO\Desktop"):
    found = False
    for root, dirs, files in os.walk(search_path):
        for f in files:
            if file_name.lower() in f.lower():
                file_path = os.path.join(root, f)
                speak(f"Found {f} at {file_path}")
                try:
                    os.startfile(file_path)
                except Exception:
                    pass
                found = True
                return
    if not found:
        speak(f"{file_name} not found in {search_path}")

def clipboard_action(action):
    try:
        if "paste" in action or "show" in action:
            text = pyperclip.paste()
            speak(f"Clipboard contains: {text}")
        else:
            speak("Clipboard action not recognized.")
    except Exception as e:
        speak(f"Clipboard error: {e}")

def set_reminder(reminder_text, delay_sec):
    def remind():
        time.sleep(delay_sec)
        speak(f"Reminder: {reminder_text}")
    threading.Thread(target=remind, daemon=True).start()
    speak(f"Reminder set for {delay_sec} seconds.")

def processCommand(command, log_callback):
    """
    Processes the text command. Uses AI for fallback.
    Keeps log_callback to push messages to GUI.
    """
    command_lower = command.lower()
    response = ""

    if "open " in command_lower and "open app" not in command_lower:
        try:
            after = command_lower.split("open",1)[1].strip()
            site = after.split()[0]
            if "." in site or "http" in site:
                url = site if site.startswith("http") else f"https://{site}"
            else:
                url = f"https://{site}.com"
            webbrowser.open(url)
            response = f"Opening {site}"
        except Exception as e:
            response = f"Failed to open site: {e}"

    elif "open app" in command_lower or "write app" in command_lower:
        app_name = command_lower.replace("open app", "").replace("write app", "").strip()
        write_app(app_name)
        response = f"Opening {app_name}"


    elif command_lower.startswith("play"):
        parts = command_lower.split()
        if len(parts) >= 2:
            song = parts[1]
            if song in getattr(musicLibrary, "music", {}):
                webbrowser.open(musicLibrary.music[song])
                response = f"Playing {song}"
            else:
                response = f"Sorry, {song} not found in library."
        else:
            response = "Please say the song name."

    elif any(x in command_lower for x in ["shutdown", "restart", "lock", "log off", "logoff"]):
        system_action(command_lower)
        response = f"Performing {command_lower}"

    elif "find file" in command_lower:
        file_name = command_lower.replace("find file", "").strip()
        search_file(file_name)
        response = f"Searching for {file_name}"

    elif "clipboard" in command_lower or "paste" in command_lower:
        clipboard_action(command_lower)
        response = "Clipboard command executed."

    elif "remind me" in command_lower:
        try:
            parts = command_lower.split(" in ")
            reminder_text = parts[0].replace("remind me to", "").replace("remind me", "").strip()
            delay_sec = int(parts[1].split()[0])
            set_reminder(reminder_text, delay_sec)
            response = f"Reminder set for {delay_sec} seconds."
        except Exception:
            response = "Failed to set reminder. Try 'remind me to <task> in <seconds>'."

    else:
        response = aiProcess(command)

    speak(response)
    log_callback(f"Orion: {response}")

def listen_command(log_callback, indicator):
    """
    Continuously listens via microphone and processes recognized speech.
    Responds to "Orion start", "Orion stop", and "Orion exit" commands.
    """
    global LISTENING_ACTIVE, EXIT_REQUESTED

    while not EXIT_REQUESTED:
        with mic as source:
            try:
                r.adjust_for_ambient_noise(source, duration=0.8)
            except Exception:
                pass

            if LISTENING_ACTIVE:
                log_callback("🎧 Listening (Orion active)...")
                indicator.start_animation()
            else:
                log_callback("🟡 Say 'Orion start' to activate listening.")
                indicator.stop_animation()

            try:
                audio = r.listen(source, timeout=10, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                log_callback(f"Microphone error: {e}")
                continue

        try:
            command = r.recognize_google(audio).lower()
            log_callback(f"You: {command}")

            if "orion start" in command:
                LISTENING_ACTIVE = True
                speak("Listening activated.")
                log_callback("🟢 Orion is now active.")
                continue

            elif "orion stop" in command:
                LISTENING_ACTIVE = False
                speak("Listening paused.")
                log_callback("🔴 Orion stopped listening.")
                continue

            elif "orion exit" in command or "orion close" in command:
                speak("Goodbye.")
                log_callback("⚪ Orion is shutting down...")
                EXIT_REQUESTED = True
                indicator.stop_animation()
                threading.Thread(target=lambda: os._exit(0), daemon=True).start()
                break

            if LISTENING_ACTIVE:
                indicator.start_animation()
                processCommand(command, log_callback)
                indicator.stop_animation()

        except sr.UnknownValueError:
            if LISTENING_ACTIVE:
                speak("Sorry, I didn’t catch that.")
            continue
        except Exception as e:
            log_callback(f"Recognition error: {e}")
            continue

def continuous_listen(app):
    """Continuously listen for commands in the background."""
    global EXIT_REQUESTED
    while not EXIT_REQUESTED:
        try:
            listen_command(app.log, app.indicator)
        except Exception as e:
            app.log(f"Error in listening loop: {e}")
            time.sleep(2)


class ListeningIndicator(ctk.CTkCanvas):
    """
    Circular arc that rotates while listening. Uses CTkCanvas but behaves similarly to Tk Canvas.
    """
    def __init__(self, master, size=100, bg="#0f1216"):
        super().__init__(master, width=size, height=size, highlightthickness=0, bg=bg)
        self.size = size
        self.angle = 0
        pad = 6
        self.arc = self.create_arc(pad, pad, size - pad, size - pad, start=0, extent=60, style="arc", outline="#00ffff", width=4)
        self.animating = False

    def start_animation(self):
        if not self.animating:
            self.animating = True
            threading.Thread(target=self._animate, daemon=True).start()

    def stop_animation(self):
        self.animating = False
        self.itemconfig(self.arc, start=0)

    def _animate(self):
        while self.animating:
            self.angle = (self.angle + 6) % 360
            try:
                self.itemconfig(self.arc, start=self.angle)
            except Exception:
                pass
            time.sleep(0.02)

class OrbitalCanvas(ctk.CTkCanvas):
    """
    Central sci-fi orbital visualization with multiple rotating rings and orbiting dots.
    """
    def __init__(self, master, size=420, bg="#07080a"):
        super().__init__(master, width=size, height=size, highlightthickness=0, bg=bg)
        self.size = size
        self.center = (size // 2, size // 2)
        self.rings = [40, 70, 100, 130, 160]
        self.dots = []
        self.angles = [i * 30 for i in range(len(self.rings))]
        self._create_static()
        self.running = True
        threading.Thread(target=self._animate, daemon=True).start()

    def _create_static(self):
        cx, cy = self.center
        self.create_oval(cx-40, cy-40, cx+40, cy+40, fill="#001f3f", outline="#00e6ff", width=3)
        self.create_text(cx, cy, text="ORION", fill="#00e6ff", font=("Orbitron", 14, "bold"))
        for r in self.rings:
            self.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#0d4b66", width=1)
        for i, r in enumerate(self.rings):
            a = math.radians(self.angles[i])
            x = cx + r * math.cos(a)
            y = cy + r * math.sin(a)
            dot = self.create_oval(x-6, y-6, x+6, y+6, fill="#00e6ff", outline="")
            self.dots.append((dot, r, (i % 2)*0.6 + 0.6))

    def _animate(self):
        cx, cy = self.center
        while self.running:
            for i in range(len(self.dots)):
                dot_id, r, speed = self.dots[i]
                self.angles[i] = (self.angles[i] + 1.5 * speed) % 360
                a = math.radians(self.angles[i])
                x = cx + r * math.cos(a)
                y = cy + r * math.sin(a)
                self.coords(dot_id, x-5, y-5, x+5, y+5)
            time.sleep(0.02)

    def stop(self):
        self.running = False

class ORIONApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("O.R.I.O.N - AI Assistant")
        self.geometry(WINDOW_SIZE)
        self.minsize(1000, 600)
        ctk.set_appearance_mode("dark")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.left_panel = ctk.CTkFrame(self, width=220, corner_radius=8, fg_color="#071021")
        self.left_panel.grid(row=0, column=0, sticky="nsw", padx=(12,6), pady=12)
        self._build_left_panel()


        self.center_panel = ctk.CTkFrame(self, corner_radius=10, fg_color="#08121a")
        self.center_panel.grid(row=0, column=1, sticky="nsew", padx=6, pady=12)
        self.center_panel.grid_rowconfigure(1, weight=1)
        self._build_center_panel()

        self.header = ctk.CTkLabel(self, text="O.R.I.O.N", font=("Orbitron", 20, "bold"), text_color="#00e6ff")
        self.header.place(x=80, y=8)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _build_left_panel(self):
        t = ctk.CTkLabel(self.left_panel, text="SYSTEM", font=("Roboto", 14, "bold"), text_color="#7fd3ff")
        t.pack(pady=(25, 25))
        self.system_labels = {}

        for name in ["CPU", "Memory", "Disk", "Power", "Location"]:
            f = ctk.CTkFrame(self.left_panel, fg_color="#05121a", corner_radius=6)
            f.pack(fill="x", padx=10, pady=6)
            lbl = ctk.CTkLabel(f, text=name, anchor="w", font=("Helvetica", 11))
            lbl.grid(row=0, column=0, sticky="w", padx=8, pady=6)
            val_lbl = ctk.CTkLabel(f, text="...", anchor="e", font=("Helvetica", 12, "bold"), text_color="#00e6ff")
            val_lbl.grid(row=0, column=1, sticky="e", padx=8, pady=6)
            f.grid_columnconfigure(0, weight=1)
            f.grid_columnconfigure(1, weight=0)
            self.system_labels[name] = val_lbl

        threading.Thread(target=self._update_system_stats, daemon=True).start()

    def _update_system_stats(self):
        while True:
            try:
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory().used / (1024 ** 3)
                total_mem = psutil.virtual_memory().total / (1024 ** 3)
                disk = psutil.disk_usage('/').percent
                try:
                    battery = psutil.sensors_battery()
                    power = "AC" if battery.power_plugged else f"{battery.percent:.0f}%"
                except Exception:
                    power = "N/A"

                self.system_labels["CPU"].configure(text=f"{cpu:.1f}%")
                self.system_labels["Memory"].configure(text=f"{mem:.1f}/{total_mem:.1f} GB")
                self.system_labels["Disk"].configure(text=f"{disk:.1f}%")
                self.system_labels["Power"].configure(text=power)
                location = get_real_location()
                self.system_labels["Location"].configure(text=location)

            except Exception as e:
                print("System stats update error:", e)
            time.sleep(2)

    def _build_center_panel(self):
        top_frame = ctk.CTkFrame(self.center_panel, fg_color="#07131a", corner_radius=8)
        top_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12,8))
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=0)

        self.orbital = OrbitalCanvas(top_frame, size=420, bg="#04050a")
        self.orbital.grid(row=0, column=0, padx=12, pady=12)

        mini = ctk.CTkFrame(top_frame, fg_color="#05121a", width=220, corner_radius=8)
        mini.grid(row=0, column=1, sticky="n", padx=(6,12), pady=12)
        mini.grid_rowconfigure(3, weight=1)
        lbl_time = ctk.CTkLabel(mini, text="SYSTEM TIME", font=("Roboto", 10), text_color="#9adcfb")
        lbl_time.pack(pady=(8,2))
        self.lbl_clock = ctk.CTkLabel(mini, text="00:00:00", font=("Orbitron", 16, "bold"), text_color="#00e6ff")
        self.lbl_clock.pack(pady=(0,8))

        bottom_frame = ctk.CTkFrame(self.center_panel, fg_color="#07131a", corner_radius=8)
        bottom_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(8,12))
        bottom_frame.grid_rowconfigure(0, weight=1)
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(bottom_frame, width=780, height=160, corner_radius=8, font=("Consolas", 11))
        self.textbox.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.textbox.insert("end", ">>> Welcome, Sir. Orion is online.\n")

        control_frame = ctk.CTkFrame(bottom_frame, fg_color="#07131a", corner_radius=8)
        control_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0,12))
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=0)

        left_controls = ctk.CTkFrame(control_frame, fg_color="#07131a", corner_radius=8)
        left_controls.grid(row=0, column=0, sticky="w", padx=6)
        self.indicator = ListeningIndicator(left_controls, size=64, bg="#07121a")
        self.indicator.pack(side="left", padx=(6,12))

        self.input_entry = ctk.CTkEntry(control_frame, placeholder_text="Type a command or press Speak...", width=420)
        self.input_entry.grid(row=0, column=1, sticky="e", padx=(0,6))
        self.input_entry.bind("<Return>", self._on_enter_pressed)

        help_lbl = ctk.CTkLabel(control_frame, text="Tip: Try 'open youtube', 'remind me to call in 10', 'find file report'",
                                font=("Roboto", 9), text_color="#8fd8ff")
        help_lbl.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(6,0))


    def _on_enter_pressed(self, event):
        txt = self.input_entry.get().strip()
        if txt:
            self.log(f"You: {txt}")
            self.input_entry.delete(0, "end")
            threading.Thread(target=processCommand, args=(txt, self.log), daemon=True).start()

    def log(self, message):
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")

    def on_closing(self):
        try:
            self.orbital.stop()
        except Exception:
            pass
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        self.destroy()


def start_clock(app):
    def update():
        while True:
            now = datetime.now().strftime("%H:%M:%S")
            try:
                app.lbl_clock.configure(text=now)
            except Exception:
                pass
            time.sleep(1)
    threading.Thread(target=update, daemon=True).start()
    
if __name__ == "__main__":
    threading.Thread(target=speak, args=("Initializing Orion interface. Say 'Orion start' to begin.",), daemon=True).start()
    app = ORIONApp()
    start_clock(app)
    threading.Thread(target=continuous_listen, args=(app,), daemon=True).start()
    app.mainloop()
