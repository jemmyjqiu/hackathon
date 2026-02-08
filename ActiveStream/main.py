import customtkinter as ctk
import threading
import whisper
import os
import wave
import pyaudio
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- INITIALIZATION ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-3-flash-preview"

LANG_DATA = {
    "Spanish": "es", "French": "fr", "Japanese": "ja", 
    "Chinese": "zh", "German": "de", "Korean": "ko", "English": "en"
}
CONFIG_FILE = "profile.json"

class AudioTutorGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- UI CONFIG ---
        self.title("ActiveStream Overlay")
        self.geometry("500x850")
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.95)
        ctk.set_appearance_mode("dark")

        # Load Saved Profile
        config = self.load_config()
        self.user_lang = config.get("user_lang", "English")
        self.target_lang = config.get("target_lang", "Korean")
        self.difficulty = config.get("difficulty", "Easy")

        # Load Whisper (Using 'small' as per your preference)
        print("Loading Whisper Model...")
        self.audio_model = whisper.load_model("small")
        print("Whisper Model Loaded.")
        
        self.is_thinking = False
        self.setup_chat_session()

        # --- UI SETUP ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(20, 10), fill="x")

        self.label = ctk.CTkLabel(self.header_frame, text="ActiveStream AI", font=("Helvetica", 22, "bold"))
        self.label.pack(side="left", padx=(140, 0))

        self.clear_btn = ctk.CTkButton(self.header_frame, text="Clear", width=60, height=25, 
                                       fg_color="#444444", hover_color="#FF4B4B", command=self.clear_chat)
        self.clear_btn.pack(side="right", padx=10)

        # 1. Native Language
        self.u_label = ctk.CTkLabel(self, text="Your Native Language:", font=("Helvetica", 11))
        self.u_label.pack()
        self.user_lang_menu = ctk.CTkOptionMenu(self, values=list(LANG_DATA.keys()), 
                                               command=self.change_user_lang, width=160)
        self.user_lang_menu.set(self.user_lang)
        self.user_lang_menu.pack(pady=(0, 10))

        # 2. Target Language
        self.t_label = ctk.CTkLabel(self, text="Learning Language:", font=("Helvetica", 11))
        self.t_label.pack()
        self.target_lang_menu = ctk.CTkOptionMenu(self, values=list(LANG_DATA.keys()), 
                                                 command=self.change_target_lang, width=160, fg_color="#24a0ed")
        self.target_lang_menu.set(self.target_lang)
        self.target_lang_menu.pack(pady=(0, 10))

        # 3. Difficulty Slider (FROM NEW VERSION)
        self.diff_label = ctk.CTkLabel(self, text="Quiz Difficulty:", font=("Helvetica", 11))
        self.diff_label.pack()
        self.diff_menu = ctk.CTkSegmentedButton(self, values=["Easy", "Medium", "Hard"], 
                                                command=self.change_difficulty, width=200,
                                                selected_color="#24a0ed", selected_hover_color="#1879bd")
        self.diff_menu.set(self.difficulty)
        self.diff_menu.pack(pady=(0, 10))

        self.chat_display = ctk.CTkTextbox(self, width=460, height=320, font=("Helvetica", 13), spacing3=10)
        self.chat_display.pack(pady=10)
        
        self.chat_display.tag_config("user", foreground="#1fdbff", justify='right', rmargin=20)
        self.chat_display.tag_config("ai", foreground="#ffcc00", justify='left', lmargin1=10, lmargin2=10)
        self.chat_display.tag_config("system", foreground="#888888", justify='center')
        self.chat_display.configure(state="disabled")

        self.status_label = ctk.CTkLabel(self, text="Ready", text_color="gray")
        self.status_label.pack()

        self.record_btn = ctk.CTkButton(self, text="Capture", command=self.start_tutor_flow, 
                                       fg_color="#24a0ed", font=("Helvetica", 14, "bold"))
        self.record_btn.pack(pady=10)

        self.reply_entry = ctk.CTkEntry(self, width=440, placeholder_text="Message...")
        self.reply_entry.pack(pady=10)
        self.reply_entry.bind("<Return>", lambda e: self.send_reply())

    # --- CONFIG & LOGIC ---
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f: return json.load(f)
            except: return {}
        return {}

    def save_config(self):
        config = {
            "user_lang": self.user_lang, 
            "target_lang": self.target_lang,
            "difficulty": self.difficulty
        }
        with open(CONFIG_FILE, "w") as f: json.dump(config, f)

    def setup_chat_session(self):
        # DIFFICULTY LOGIC (FROM NEW VERSION)
        if self.difficulty == "Easy":
            style_rule = (f"Ask exactly ONE simple question in {self.user_lang}. "
                          "The question MUST be answerable with 'Yes/No' or a binary choice (e.g., 'Is she happy or sad?'). "
                          "Focus only on literal keywords. Do not explain grammar.")
        elif self.difficulty == "Medium":
            style_rule = (f"Ask exactly ONE specific question in {self.user_lang}. "
                          "The user must identify a single vocabulary word (noun/verb/adjective) from the clip. "
                          "Example: 'What object did he point to?'.")
        else: # Hard
            style_rule = (f"Ask exactly ONE conceptual question in {self.user_lang} about the situation. "
                          "The user must explain 'what is happening' in a full phrase. "
                          "Example: 'Why is the speaker frustrated?'.")

        instr = (f"You are a strict {self.user_lang} quiz bot. "
                 f"When you receive a transcript in {self.target_lang}, your ONLY task is to: {style_rule} "
                 f"Do NOT give pre-ambles like 'Here is your question'. Just ask the question directly."
                 f"If the user replies, check their answer. If correct, say 'Correct!'. If wrong, briefly give the answer.")
        
        sys_instr = types.Part.from_text(text=instr)
        self.chat_session = client.chats.create(model=MODEL_ID, config=types.GenerateContentConfig(system_instruction=sys_instr))

    def change_difficulty(self, value):
        self.difficulty = value
        self.save_config()
        self.setup_chat_session()
        self.insert_message("SYSTEM", f"Difficulty set to {value}", "system")

    def change_user_lang(self, choice):
        self.user_lang = choice
        self.save_config()
        self.setup_chat_session()
        self.insert_message("SYSTEM", f"Native language: {choice}", "system")

    def change_target_lang(self, choice):
        self.target_lang = choice
        self.save_config()
        self.setup_chat_session()
        self.insert_message("SYSTEM", f"Learning language: {choice}", "system")

    def clear_chat(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.insert_message("SYSTEM", "Chat history cleared.", "system")

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
        self.is_thinking = True
        self.record_btn.configure(state="disabled", text="Recording...")
        threading.Thread(target=self.run_process, daemon=True).start()

    def run_process(self):
        self.after(0, lambda: self.status_label.configure(text="🔴 RECORDING...", text_color="red"))
        
        # RESTORED OLD AUDIO CALL (Uses device_id=1, channels=2)
        audio_path = self.record_audio_logic(seconds=10, device_id=1)
        
        if not audio_path:
            self.after(0, lambda: self.status_label.configure(text="Audio Error", text_color="orange"))
            self.after(0, self._unlock_ui)
            return

        self.after(0, lambda: self.status_label.configure(text="⌛ ANALYZING...", text_color="yellow"))
        try:
            # RESTORED OLD WHISPER CALL (Simple, efficient for your setup)
            result = self.audio_model.transcribe(audio_path, language=LANG_DATA[self.target_lang])
            transcript = result['text'].strip()
            
            if transcript:
                self.insert_message("CAPTURED", f'"{transcript}"', "system")
                
                # INJECT DIFFICULTY PROMPT
                if self.difficulty == "Easy":
                    q_type = "a simple Yes/No question"
                elif self.difficulty == "Medium":
                    q_type = "a specific keyword identification question"
                else:
                    q_type = "a conceptual 'what is happening' question"

                prompt = f"Transcript: '{transcript}'. Ask me exactly one {q_type} in {self.user_lang}."
                self.get_ai_response(prompt) 
            else:
                self.insert_message("SYSTEM", "No speech detected.", "system")
                self.after(0, self._unlock_ui)
        except Exception as e:
            self.insert_message("ERROR", str(e), "system")
            self.after(0, self._unlock_ui)

    def send_reply(self):
        txt = self.reply_entry.get().strip()
        if not txt or self.is_thinking: return
        self.is_thinking = True
        self.insert_message("YOU", txt, "user")
        self.reply_entry.delete(0, "end")
        self.get_ai_response(txt)

    def get_ai_response(self, prompt):
        self.after(0, lambda: self.status_label.configure(text="🤖 AI THINKING...", text_color="#ffcc00"))
        
        def call_api():
            try:
                # Prepare UI for stream
                self.after(0, self._prepare_streaming_ui)
                
                response_stream = self.chat_session.send_message_stream(prompt)
                
                for chunk in response_stream:
                    if chunk.text:
                        self.after(0, self._update_streaming_text, chunk.text)
                
                self.after(0, lambda: self._update_streaming_text("\n\n"))

            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg:
                    self.after(0, lambda: self.insert_message("SYSTEM", "Server busy, retrying...", "system"))
                    self.after(2000, lambda: self.get_ai_response(prompt))
                    return
                else:
                    self.after(0, lambda: self.insert_message("SYSTEM", f"AI Error: {error_msg}", "system"))
            finally:
                self.after(0, self._unlock_ui)

        threading.Thread(target=call_api, daemon=True).start()

    def _prepare_streaming_ui(self):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", "ActiveStream\n", "ai")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _update_streaming_text(self, new_text):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", new_text, "ai")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _unlock_ui(self):
        self.is_thinking = False
        self.status_label.configure(text="Ready", text_color="gray")
        self.record_btn.configure(state="normal", text="Capture")

    def record_audio_logic(self, seconds=10, device_id=1):
        # RESTORED OLD AUDIO LOGIC EXACTLY
        CHUNK, FORMAT, CHANNELS, RATE = 1024, pyaudio.paInt16, 2, 44100
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, 
                            input_device_index=device_id, frames_per_buffer=CHUNK)
            frames = [stream.read(CHUNK, exception_on_overflow=False) for _ in range(0, int(RATE / CHUNK * seconds))]
            stream.stop_stream(); stream.close(); p.terminate()
            filename = "temp_audio.wav"
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(CHANNELS); wf.setsampwidth(p.get_sample_size(FORMAT)); wf.setframerate(RATE); wf.writeframes(b''.join(frames))
            return filename
        except Exception as e:
            print(f"Audio Error: {e}")
            p.terminate()
            return None

if __name__ == "__main__":
    app = AudioTutorGUI()
    app.mainloop()