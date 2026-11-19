# Main Desktop Chat Window
import customtkinter as ctk
import requests
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ChatWindow:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("My AI Agent")
        self.root.geometry("800x600")
        self.setup_ui()

    def setup_ui(self):
        # Title
        title = ctk.CTkLabel(self.root, text="🤖 My AI Agent",
                             font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=10)

        # Chat display area
        self.chat_box = ctk.CTkTextbox(self.root, width=760, height=420,
                                        font=ctk.CTkFont(size=13))
        self.chat_box.pack(padx=20, pady=5)
        self.chat_box.insert("end", "Agent: Hello! I am your personal AI assistant. How can I help you?\n\n")
        self.chat_box.configure(state="disabled")

        # Input area
        input_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        input_frame.pack(padx=20, pady=10, fill="x")

        self.input_box = ctk.CTkEntry(input_frame, placeholder_text="Type your message here...",
                                       font=ctk.CTkFont(size=13), height=40)
        self.input_box.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_box.bind("<Return>", lambda e: self.send_message())

        send_btn = ctk.CTkButton(input_frame, text="Send", width=80,
                                  height=40, command=self.send_message)
        send_btn.pack(side="right")

    def send_message(self):
        user_text = self.input_box.get().strip()
        if not user_text:
            return

        self.input_box.delete(0, "end")
        self.display_message(f"You: {user_text}")

        # Send to agent in background thread
        thread = threading.Thread(target=self.get_response, args=(user_text,))
        thread.daemon = True
        thread.start()

    def get_response(self, text: str):
        try:
            response = requests.post(
                "http://localhost:8000/chat/send",
                json={"content": text},
                timeout=30
            )
            data = response.json()
            self.display_message(f"Agent: {data['response']}")
        except Exception as e:
            self.display_message(f"Agent: Error connecting to server: {str(e)}")

    def display_message(self, message: str):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", message + "\n\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    def run(self):
        self.root.mainloop()
