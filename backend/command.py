import time
import pyttsx3
import speech_recognition as sr
import eel
import os
import signal
import subprocess
import time
import sys


GEMINI_ALLOWED_PREFIXES = (
    "tell me about",
    "explain",
    "how to",
    "what is",
    "who is",
    "define",
    "search for",
    "how do i",
    "why does",
    "why is",
    "give me information about",
    "write the code",
    "generate code",
    "can you help me with",
    "describe",
    "what are the steps to",
    "provide an example of",
    "how can i",
    "how would you",
    "what do you mean by",
    "summarize",
    "create a program that",
    "what happens when",
    "difference between",
    "how does",
    "advantages of",
    "disadvantages of",
    "convert",
    "compare",
    "analyze",
    "write a function that",
    "what will be the output of",
    "is it possible to",
    "how can we implement",
    "can you generate",
    "generate a list of",
    "design a system that",
    "give example code for",
    "step-by-step guide to",
    "write a script that",
    "debug",
    "optimize the code for",
    "suggest improvements for",
    "what is the use of",
    "how to solve",
    "how does it work",
    "explain the concept of",
    "generate pseudocode for",
    "code for",
    "usage of",
    "explain how to write",
    "explain with an example",
    "recommend a solution to",
    "how do you write",
    "can you show me how to"
)



def speak(text,show_on_gui=True):
    text = str(text)
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    # print(voices)
    engine.setProperty('voice', voices[0].id)
    # eel.DisplayMessage(text)
    engine.say(text)
    engine.runAndWait()
    engine.setProperty('rate', 174)
    eel.receiverText(text)
    if show_on_gui:
        eel.DisplayMessage(text) # Display the message on the GUI

# Expose the Python function to JavaScript
def takecommand():
    r = sr.Recognizer()

    while True:
        with sr.Microphone() as source:
            print("Calibrating for ambient noise...")
            eel.DisplayMessage("Calibrating microphone...")

            # Calibrate microphone to ignore ambient noise
            r.adjust_for_ambient_noise(source, duration=2)  # 2 seconds for better accuracy

            print("I'm listening...")
            eel.DisplayMessage("I'm listening...")
            r.pause_threshold = 0.8  # Short silence = end of speech
            r.energy_threshold = 400  # Slightly higher threshold for ignoring low background hums

            try:
                audio = r.listen(source, timeout=None, phrase_time_limit=10)  # 10 sec max speech
                print("Recognizing...")
                eel.DisplayMessage("Recognizing...")

                query = r.recognize_google(audio, language='en-US')
                eel.DisplayMessage(query)
                speak(query)
                return query.lower()

            except sr.UnknownValueError:
                print("Didn't understand. Please speak clearly...")
                eel.DisplayMessage("Didn't understand. Speak clearly...")
                continue

            # except sr.WaitTimeoutError:
            #     print("No speech detected. Listening again...")
            #     eel.DisplayMessage("No speech detected. Listening again...")
            #     continue

            # except sr.RequestError as e:
            #     print(f"API Error: {e}")
            #     eel.DisplayMessage("API error. Listening again...")
            #     continue





@eel.expose
def takeAllCommands(message=None):
    while True:  # Loop to continuously listen for commands
        if message is None:
            query = takecommand()  # If no message is passed, listen for voice input
            if not query:
                return  # Exit if no query is received
            print(query)
            eel.senderText(query)
        else:
            query = message
            print(f"Message received: {query}")
            eel.senderText(query)
        
        try:
            if query:
                query_lower = query.lower()

                if "open" in query_lower:
                    from backend.feature import openCommand
                    openCommand(query)
                    continue

                elif "close" in query_lower:
                    from backend.feature import closeCommand
                    closeCommand(query)
                    continue

                elif "send message" in query_lower or "call" in query_lower or "video call" in query_lower:
                    from backend.feature import findContact, whatsApp
                    flag = ""
                    Phone, name = findContact(query)
                    if Phone != 0:
                        if "send message" in query_lower:
                            flag = 'message'
                            speak("What message to send?")
                            query = takecommand()  # Ask for the message text
                        elif "call" in query_lower:
                            flag = 'call'
                        else:
                            flag = 'video call'
                        whatsApp(Phone, query, flag, name)
                
                elif "on youtube" in query_lower:
                    from backend.feature import PlayYoutube
                    PlayYoutube(query)

                elif "on wikipedia" in query_lower:
                    import webbrowser
                    search_query = query.replace("on wikipedia", "").strip()
                    url = f"https://en.wikipedia.org/wiki/Special:Search?search={search_query}"
                    webbrowser.open(url)

                elif "search on google" in query or "google" in query:
                    speak("Searching Google for you...")
                    search_query = query.replace("search on google", "").replace("google", "").strip()
                    from backend.feature import googleSearch
                    googleSearch(search_query)

                elif "weather" in query_lower:
                    from backend.feature import get_weather

                    import re
                    match = re.search(r"(?:weather in|weather at|in|at)\s+(.*)", query_lower)
                    city = match.group(1).strip() if match else "your city"  # Default city fallback

                    weather_info = get_weather(city)
                    speak(weather_info)
                    eel.DisplayMessage(weather_info)


                elif "current time" in query_lower:
                    from backend.feature import timeCommand
                    timeCommand()

                elif "take screenshot" in query:
                    from backend.feature import takeScreenshot
                    takeScreenshot()

                elif "start screen recording" in query:
                    from backend.feature import startScreenRecording
                    startScreenRecording()

                elif "stop screen recording" in query:
                    from backend.feature import stopScreenRecording
                    stopScreenRecording()

                elif "increase volume" in query or "volume up" in query:
                    from backend.feature import changeVolume
                    changeVolume("up")

                elif "decrease volume" in query or "volume down" in query:
                    from backend.feature import changeVolume
                    changeVolume("down")

                elif "increase brightness" in query or "brightness up" in query:
                    from backend.feature import changeBrightness
                    changeBrightness("up")

                elif "decrease brightness" in query or "brightness down" in query:
                    from backend.feature import changeBrightness
                    changeBrightness("down")

                elif "mute" in query:
                    from backend.feature import muteUnmute
                    muteUnmute("mute")

                elif "unmute" in query:
                    from backend.feature import muteUnmute
                    muteUnmute("unmute")
                    
                elif "current date" in query_lower:
                    from backend.feature import dateCommand
                    dateCommand()
                
                elif "create file" in query or "make file" in query:
                    from backend.feature import createFileCommand
                    createFileCommand(query)
                    continue

                elif "lock the screen" in query:
                    from backend.feature import lock_screen
                    lock_screen()
                    continue

                elif "exit the app" in query:
                    from backend.feature import kill_edge_browser
                    print("Goodbye Jarvis. Closing the program.")
                    kill_edge_browser()
                    sys.exit(0)

                elif query.startswith(GEMINI_ALLOWED_PREFIXES):
                    from backend.feature import chatBot
                    chatBot(query)  # Only voice reply

                else:
                    # speak("This command doesn't require internet or deep explanation, so I won't process it.")
                    from backend.feature import chatBot
                    chatBot(query)

            else:
                speak("No command was given.")
        except Exception as e:
            print(f"An error occurred: {e}")
            speak("Sorry, something went wrong.")
            continue
        
        eel.ShowHood()  # Keep the UI updated

