import customtkinter as ctk
import threading
import whisper
import os
import wave
import pyaudio
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- INITIALIZATION ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-3-flash-preview"

LANG_DATA = {"Spanish": "es", "French": "fr", "Japanese": "ja", "Chinese": "zh", "German": "de", "Korean": "ko", "English": "en"}

class AudioTutorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- STABLE OVERLAY CONFIG ---
        self.title("ActiveStream Overlay")
        self.geometry("500x650")
        self.attributes("-topmost", True) # Keep on top of your video
        self.attributes("-alpha", 0.95)
        ctk.set_appearance_mode("dark")

        # Logic Variables
        self.audio_model = whisper.load_model("small")
        self.current_lang_name = "Korean"
        self.is_thinking = False
        self.setup_chat_session()

        # --- UI SETUP ---
        self.label = ctk.CTkLabel(self, text="ActiveStream AI", font=("Helvetica", 22, "bold"))
        self.label.pack(pady=(20, 10))

        self.lang_menu = ctk.CTkOptionMenu(self, values=list(LANG_DATA.keys()), command=self.change_language, width=140)
        self.lang_menu.set("Korean")
        self.lang_menu.pack(pady=5)

        self.chat_display = ctk.CTkTextbox(self, width=460, height=380, font=("Helvetica", 13), spacing3=10)
        self.chat_display.pack(pady=10)
        
        # Alignment Tags
        self.chat_display.tag_config("user", foreground="#1fdbff", justify='right', rmargin=20)
        self.chat_display.tag_config("ai", foreground="#ffcc00", justify='left', lmargin1=10, lmargin2=10)
        self.chat_display.tag_config("system", foreground="#888888", justify='center')
        self.chat_display.configure(state="disabled")

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack()

        # THE MANUAL BUTTON
        self.record_btn = ctk.CTkButton(self, text="Capture & Quiz (10s)", command=self.start_tutor_flow, fg_color="#24a0ed", font=("Helvetica", 14, "bold"))
        self.record_btn.pack(pady=10)

        self.reply_entry = ctk.CTkEntry(self, width=440, placeholder_text="Type your answer here...")
        self.reply_entry.pack(pady=10)
        self.reply_entry.bind("<Return>", lambda e: self.send_reply())

    def setup_chat_session(self):
        instr = (f"You are a {self.current_lang_name} coach. Keep responses very brief. "
                 "When a transcript is provided, ask exactly ONE English question about its meaning. "
                 "If correct, congratulate briefly. If wrong, ask if they want an explanation.")
        sys_instr = types.Part.from_text(text=instr)
        self.chat_session = client.chats.create(model=MODEL_ID, config=types.GenerateContentConfig(system_instruction=sys_instr))

    def change_language(self, choice):
        self.current_lang_name = choice
        self.setup_chat_session()
        self.insert_message("SYSTEM", f"Language changed to {choice}", "system")

    def insert_message(self, sender, message, tag):
        self.after(0, self._safe_insert, sender, message, tag)

    def _safe_insert(self, sender, message, tag):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{sender}\n", tag)
        self.chat_display.insert("end", f"{message}\n\n", tag)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def start_tutor_flow(self):
        if self.is_thinking: return
        self.record_btn.configure(state="disabled", text="Recording...")
        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        self.after(0, lambda: self.status_label.configure(text="🔴 RECORDING...", text_color="red"))
        audio_path = self.record_audio_logic()
        
        self.after(0, lambda: self.status_label.configure(text="⌛ ANALYZING...", text_color="yellow"))
        try:
            result = self.audio_model.transcribe(audio_path, language=LANG_DATA[self.current_lang_name])
            transcript = result['text'].strip()
            
            if transcript:
                self.insert_message("CAPTURED", f'"{transcript}"', "system")
                prompt = f"Transcript: '{transcript}'. Ask me one English question to test if I understood the meaning."
                threading.Thread(target=self.get_ai_response, args=(prompt,), daemon=True).start()
            else:
                self.after(0, lambda: self.status_label.configure(text="Ready", text_color="gray"))
                self.after(0, lambda: self.record_btn.configure(state="normal", text="Capture & Quiz (10s)"))
        except Exception as e:
            self.insert_message("ERROR", str(e), "system")
            self.after(0, lambda: self.record_btn.configure(state="normal", text="Capture & Quiz (10s)"))

    def send_reply(self):
        txt = self.reply_entry.get().strip()
        if not txt or self.is_thinking: return
        self.insert_message("YOU", txt, "user")
        self.reply_entry.delete(0, "end")
        threading.Thread(target=self.get_ai_response, args=(txt,), daemon=True).start()

    def get_ai_response(self, prompt):
        self.is_thinking = True
        try:
            response = self.chat_session.send_message(prompt)
            self.after(0, lambda: self.insert_message("AI TUTOR", response.text, "ai"))
        except Exception as e:
            self.after(0, lambda: self.insert_message("SYSTEM", f"AI Error: {e}", "system"))
        finally:
            self.is_thinking = False
            self.after(0, lambda: self.status_label.configure(text="Ready", text_color="gray"))
            self.after(0, lambda: self.record_btn.configure(state="normal", text="Capture & Quiz (10s)"))

    def record_audio_logic(self, seconds=10, device_id=1):
        CHUNK, FORMAT, CHANNELS, RATE = 1024, pyaudio.paInt16, 2, 44100
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, input_device_index=device_id, frames_per_buffer=CHUNK)
        frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * seconds))]
        stream.stop_stream(); stream.close(); p.terminate()
        filename = "temp_audio.wav"
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(CHANNELS); wf.setsampwidth(p.get_sample_size(FORMAT)); wf.setframerate(RATE); wf.writeframes(b''.join(frames))
        return filename

if __name__ == "__main__":
    app = AudioTutorGUI()
    app.mainloop()