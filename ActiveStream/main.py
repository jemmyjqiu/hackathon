import customtkinter as ctk
import threading
import whisper
import os
import wave
import pyaudio
from PIL import Image # Need this for Figma assets
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-3-flash-preview"

class FigmaStyleOverlay(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- HUD LOOK: Frameless & Transparent ---
        self.title("ActiveStream HUD")
        self.geometry("450x700")
        self.overrideredirect(True) # Removes the ugly window border/title bar
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.9) # Slick translucency
        self.configure(fg_color="#1A1A1A") # Deep Figma Dark Mode Grey

        # --- LOAD FIGMA ASSETS (Placeholders for now) ---
        # If you export a button from Figma, load it like this:
        # self.btn_img = ctk.CTkImage(light_image=Image.open("record_btn.png"), size=(200, 50))

        self.audio_model = whisper.load_model("small")
        self.current_lang_name = "Korean"
        self.setup_chat_session()

        # --- CUSTOM UI DESIGN ---
        # Top Bar (Simulated)
        self.top_bar = ctk.CTkFrame(self, height=40, fg_color="#252525", corner_radius=0)
        self.top_bar.pack(fill="x")
        
        self.close_btn = ctk.CTkButton(self.top_bar, text="✕", width=30, fg_color="transparent", 
                                      hover_color="#FF4B4B", command=self.destroy)
        self.close_btn.pack(side="right", padx=10)

        self.title_label = ctk.CTkLabel(self, text="ACTIVE STREAM", font=("Inter", 18, "bold"), text_color="#1fdbff")
        self.title_label.pack(pady=20)

        # Glass-morphism Chat Box
        self.chat_display = ctk.CTkTextbox(self, width=400, height=400, 
                                          fg_color="#2A2A2A", border_color="#3D3D3D", 
                                          border_width=2, corner_radius=15,
                                          font=("Inter", 13), spacing3=10)
        self.chat_display.pack(pady=10)
        self.setup_tags()

        self.status_label = ctk.CTkLabel(self, text="READY", font=("Inter", 10, "bold"), text_color="#555555")
        self.status_label.pack()

        # Premium Feeling Button
        self.record_btn = ctk.CTkButton(self, text="ANALYZE CLIP", 
                                       command=self.start_tutor_flow,
                                       height=50, width=300,
                                       corner_radius=25,
                                       fg_color="#1fdbff", text_color="#000000",
                                       hover_color="#17a2bb",
                                       font=("Inter", 14, "bold"))
        self.record_btn.pack(pady=20)

        # Subtle Input Field
        self.reply_entry = ctk.CTkEntry(self, width=400, height=40, 
                                       placeholder_text="Type response...",
                                       corner_radius=10, border_width=0,
                                       fg_color="#333333")
        self.reply_entry.pack(pady=10)
        self.reply_entry.bind("<Return>", lambda e: self.send_reply())

        # Allow window dragging since we removed the title bar
        self.top_bar.bind("<B1-Motion>", self.move_window)
        self.top_bar.bind("<Button-1>", self.get_pos)

    def setup_tags(self):
        self.chat_display.tag_config("user", foreground="#1fdbff", justify='right', rmargin=20)
        self.chat_display.tag_config("ai", foreground="#FFFFFF", justify='left', lmargin1=10)
        self.chat_display.tag_config("system", foreground="#666666", justify='center')
        self.chat_display.configure(state="disabled")

    def get_pos(self, event):
        self.xwin = event.x
        self.ywin = event.y

    def move_window(self, event):
        self.geometry(f'+{event.x_root - self.xwin}+{event.y_root - self.ywin}')

    # ... [Keep previous record_audio_logic and transcription logic here] ...

    def setup_chat_session(self):
        instr = f"You are a coach. Be brief. Ask ONE question. Explain only if asked."
        self.chat_session = client.chats.create(model=MODEL_ID, config=types.GenerateContentConfig(system_instruction=instr))

    def insert_message(self, sender, message, tag):
        self.after(0, self._safe_insert, sender, message, tag)

    def _safe_insert(self, sender, message, tag):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{message}\n\n", tag)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def start_tutor_flow(self):
        self.record_btn.configure(state="disabled", text="LISTENING")
        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        # [Use your existing transcription logic here...]
        pass

if __name__ == "__main__":
    app = FigmaStyleOverlay()
    app.mainloop()