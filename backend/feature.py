import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import eel
from urllib.parse import quote
import os
import pyaudio
import pvporcupine
import pygame
import pyautogui
import pywhatkit as kit
import psutil
import re
import platform
import sqlite3
import time
import struct
import webbrowser
import urllib.parse
import subprocess
import requests
from backend.command import speak, takecommand
from backend.config import ASSISTANT_NAME
from backend.helper import extract_yt_term, remove_words
import cv2
import numpy as np
import pyautogui
import time
import threading
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import screen_brightness_control as sbc

recording = False

# Initialize the environment and SQLite connection
load_dotenv()
conn = sqlite3.connect("jarvis.db")
cursor = conn.cursor()

# Initialize pygame mixer for sound
pygame.mixer.init()

# Initialize Gemini model (via Google Generative AI)
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')
chat = model.start_chat()

# Play assistant sound
@eel.expose
def play_assistant_sound():
    sound_file = r"C:\Users\i\Desktop\Jarvis-2025\frontend\assets\audio\start_sound.mp3"
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play()

# Open app or URL based on query
def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "").replace("open", "").strip().lower()
    if query:
        try:
            cursor.execute('SELECT path FROM sys_command WHERE name IN (?)', (query,))
            results = cursor.fetchall()

            if len(results) != 0:
                speak("Opening " + query)
                os.startfile(results[0][0])
            else:
                cursor.execute('SELECT url FROM web_command WHERE name IN (?)', (query,))
                results = cursor.fetchall()
                
                if len(results) != 0:
                    speak("Opening " + query)
                    webbrowser.open(results[0][0])
                else:
                    speak("I couldn't find " + query)
        except Exception as e:
            speak("Something went wrong: " + str(e))


def closeCommand(query):
    query = query.replace(ASSISTANT_NAME, "").replace("close", "").strip().lower()
    
    if query:
        try:
            # Fetch the app path from the database
            cursor.execute('SELECT path FROM sys_command WHERE name = ?', (query,))
            result = cursor.fetchone()

            if result:
                app_path = result[0]
                # Extract process name from the path (e.g., chrome.exe)
                exe_name = os.path.basename(app_path)

                speak(f"Closing {query}")
                # Kill the process
                os.system(f"taskkill /f /im {exe_name}")
            else:
                speak("I couldn't find " + query)
        except Exception as e:
            speak("Something went wrong: " + str(e))



# Play YouTube video
def PlayYoutube(query):
    search_term = extract_yt_term(query)
    speak("Playing " + search_term + " on YouTube")
    kit.playonyt(search_term)

# Voice command hotword detection (Listen for "jarvis" or "alexa")
def hotword():
    porcupine = None
    paud = None
    audio_stream = None
    try:
        # Pre-trained keywords for wake word detection
        porcupine = pvporcupine.create(keywords=["jarvis", "alexa"]) 
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)
        
        # Loop for streaming
        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)

            # Process keyword detected from mic
            keyword_index = porcupine.process(keyword)
            if keyword_index >= 0:
                print("Hotword detected")
                pyautogui.keyDown("win")
                pyautogui.press("j")
                time.sleep(2)
                pyautogui.keyUp("win")
                
    except Exception as e:
        print(str(e))
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()

# Find contact from the database
def findContact(query):
    words_to_remove = [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'whatsapp', 'video']
    query = remove_words(query, words_to_remove)
    try:
        query = query.strip().lower()
        cursor.execute("SELECT Phone FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
        results = cursor.fetchall()
        mobile_number_str = str(results[0][0])

        if not mobile_number_str.startswith('+91'):
            mobile_number_str = '+91' + mobile_number_str

        return mobile_number_str, query
    except:
        speak('Not found in contacts')
        return 0, 0

# WhatsApp message or call function
def whatsApp(Phone, message, flag, name):
    if flag == 'message':
        target_tab = 12
        jarvis_message = "Message sent successfully to " + name
    elif flag == 'call':
        target_tab = 7
        message = ''
        jarvis_message = "Calling " + name
    else:
        target_tab = 6
        message = ''
        jarvis_message = "Starting video call with " + name

    # Encode the message for URL
    encoded_message = quote(message)
    whatsapp_url = f"whatsapp://send?phone={Phone}&text={encoded_message}"

    # Open WhatsApp via the URL
    full_command = f'start "" "{whatsapp_url}"'
    subprocess.run(full_command, shell=True)
    time.sleep(5)
    pyautogui.hotkey('ctrl', 'f')

    for i in range(1, target_tab):
        pyautogui.hotkey('tab')

    pyautogui.hotkey('enter')
    speak(jarvis_message)


def remove_markdown(text):  
    # Remove bold, italic, strikethrough, and other common markdown characters
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Bold: **text**
    text = re.sub(r"\*(.*?)\*", r"\1", text)      # Italic: *text*
    text = re.sub(r"__(.*?)__", r"\1", text)      # Bold underline: __text__
    text = re.sub(r"_(.*?)_", r"\1", text)        # Italic underline: _text_
    text = re.sub(r"`(.*?)`", r"\1", text)        # Inline code: `text`
    text = re.sub(r"~~(.*?)~~", r"\1", text)      # Strikethrough: ~~text~~
    return text

# Function to interact with Gemini model (replacing HuggingChat)
def chatBot(query):
    user_input = query.lower()
    try:
        response = chat.send_message(user_input)
        answer = response.text
        clean_answer = remove_markdown(answer)  # Clean the response from markdown
        print(clean_answer)  # Print the answer to the console for debugging
        # eel.DisplayMessage(clean_answer)  # Send the answer to the frontend
        speak(clean_answer, show_on_gui=False)  # Only speak the answer
        # Do NOT call eel.DisplayMessage(answer)
    except Exception as e:
        speak("Something went wrong: " + str(e), show_on_gui=False)



def timeCommand():
    now = datetime.datetime.now()
    current_time = now.strftime("%I:%M %p")
    speak(f"The time is {current_time}")
    
    # Send time to frontend to display it
    eel.showTime(current_time)




def createFileCommand(query):
    try:
        # Ask for file name
        speak("What should be the file name?")
        file_name = takecommand()
        
        if not file_name:
            speak("No file name provided.")
            return

        # Ask for file extension
        speak("What should be the file extension?")
        file_extension = takecommand()
        
        if not file_extension: 
             file_extension = "txt"  # Default to .txt if no extension is provided

        # Construct full file name
        full_filename = f"{file_name.strip()}.{file_extension.strip()}"

        # Ask for content to write
        speak(f"What should I write in {full_filename}?")
        content = takecommand()

        if content:
            # Use Gemini to enhance or generate content
            response = chat.send_message(content)
            file_data = response.text

            with open(full_filename, "w", encoding="utf-8") as file:
                file.write(file_data)

            speak(f"{full_filename} has been created and written.")
        else:
            speak("No content received to write in the file.")
    except Exception as e:
        speak("An error occurred: " + str(e))


def takeScreenshot():
    try:
        folder = "Screenshots"
        os.makedirs(folder, exist_ok=True)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(folder, f"screenshot_{timestamp}.png")

        screenshot = pyautogui.screenshot()
        screenshot.save(filename)

        speak("Screenshot has been taken and saved.")
    except Exception as e:
        speak("An error occurred while taking screenshot: " + str(e))




def screenRecorder():
    global recording
    speak("Screen recording started.")
    screen_size = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    out = cv2.VideoWriter(f"screen_recording_{timestamp}.avi", fourcc, 20.0, screen_size)

    while recording:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(frame)

    out.release()
    speak("Screen recording stopped and saved.")

def startScreenRecording():
    global recording
    recording = True
    threading.Thread(target=screenRecorder).start()

def stopScreenRecording():
    global recording
    recording = False


def changeVolume(direction="up"):
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        current_volume = volume.GetMasterVolumeLevelScalar()

        if direction == "up":
            volume.SetMasterVolumeLevelScalar(min(current_volume + 0.5, 1.0), None)
            speak("Volume increased.")
        elif direction == "down":
            volume.SetMasterVolumeLevelScalar(max(current_volume - 0.5, 0.0), None)
            speak("Volume decreased.")
        else:
            speak("Invalid volume direction.")
    except Exception as e:
        speak("Unable to control volume: " + str(e))


def muteUnmute(action):
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        if action == "mute":
            volume.SetMute(1, None)
            speak("System muted.")
        elif action == "unmute":
            volume.SetMute(0, None)
            speak("System unmuted.")
        else:
            speak("Invalid mute action.")
    except Exception as e:
        speak("Unable to control mute: " + str(e))

def changeBrightness(direction="up"):
    try:
        current = sbc.get_brightness(display=0)[0]

        if direction == "up":
            sbc.set_brightness(min(current + 30, 100), display=0)
            speak("Brightness increased.")
        elif direction == "down":
            sbc.set_brightness(max(current - 30, 0), display=0)
            speak("Brightness decreased.")
        else:
            speak("Invalid brightness direction.")
    except Exception as e:
        speak("Unable to control brightness: " + str(e))

def googleSearch(query):
    try:
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        webbrowser.open(url)
    except Exception as e:
        print(f"Error during Google search: {e}")
        speak("Something went wrong while searching Google.")


def get_weather(city):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "API key not found in environment variables."

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather = data['weather'][0]['description']
        temperature = data['main']['temp']
        return f"The current weather in {city} is {weather} with a temperature of {temperature}°C."
    else:
        return "Unable to fetch weather data at the moment."
    
def kill_edge_browser():
    for proc in psutil.process_iter(['pid', 'name']):
        if 'msedge' in proc.info['name'].lower():
            try:
                proc.terminate()  # Terminate the process
                print(f"Killed Edge process with PID {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass


def lock_screen():
    system_platform = platform.system()
    
    if system_platform == "Windows":
        os.system("rundll32.exe user32.dll,LockWorkStation")
    else:
        print("Lock screen not supported on this OS.")