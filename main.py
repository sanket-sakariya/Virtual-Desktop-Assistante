import os
import eel
import sys

from backend.feature import *
from backend.command import *


def start():
    eel.init("frontend") 

    # Expose the init function to frontend (can be called from JavaScript)
    @eel.expose
    def init():
        # eel.hideStart()
        speak("Welcome to Jarvis")

    play_assistant_sound()  # Play the startup sound

    # Launch the UI in app mode (Edge)
    os.system('start msedge.exe --app="http://127.0.0.1:8000/index.html"')

    # Start the Eel server and keep it running
    eel.start("index.html", mode=None, host="localhost", block=True)


@eel.expose
def close():
    print("Closing application...")
    eel._shutdown("index.html", mode=None, host="localhost", block=False)

    sys.exit(0)  # Exit the Python script

