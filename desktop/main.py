# Desktop App Entry Point
from desktop.chat_window import ChatWindow

def launch_desktop():
    app = ChatWindow()
    app.run()
