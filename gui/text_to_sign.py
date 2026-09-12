"""
Text to Sign Language Translation Screen.
Converts typed text into sign language demonstrations.
"""
import tkinter as tk
from tkinter import ttk, font
from PIL import ImageTk
from utils.image_generator import SignImageGenerator
from utils.tts_engine import TTSEngine


class TextToSignFrame(tk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(bg="#1a1a2e")
        self.current_signs = []
        self.current_index = 0
        self.image_gen = SignImageGenerator()
        self.tts = TTSEngine()
        self.current_tk_image = None
        self._setup_ui()

    def _setup_ui(self):
        header = tk.Frame(self, bg="#16213e", height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)

        back_btn = tk.Button(header, text="← Back", font=("Helvetica", 12, "bold"),
                             bg="#16213e", fg="#e94560", relief=tk.FLAT,
                             command=lambda: self.controller.show_frame("Home"))
        back_btn.pack(side=tk.LEFT, padx=20, pady=10)

        title = tk.Label(header, text="Text → Sign Language",
                         font=("Helvetica", 18, "bold"), bg="#16213e", fg="white")
        title.pack(side=tk.LEFT, padx=20, pady=10)

        content = tk.Frame(self, bg="#1a1a2e")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        input_frame = tk.Frame(content, bg="#16213e", bd=2, relief=tk.RIDGE)
        input_frame.pack(fill=tk.X, pady=10, padx=10)

        tk.Label(input_frame, text="Enter text to translate:",
                 font=("Helvetica", 12), bg="#16213e", fg="white").pack(pady=(10, 5))

        self.text_input = tk.Text(input_frame, height=3, width=50,
                                  font=("Helvetica", 14), bg="#0f0f1a", fg="white",
                                  relief=tk.FLAT, wrap=tk.WORD)
        self.text_input.pack(pady=5, padx=10)
        self.text_input.insert(tk.END, "Hello, how are you?")

        btn_frame = tk.Frame(input_frame, bg="#16213e")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="🔍 Translate", font=("Helvetica", 12, "bold"),
                  bg="#e94560", fg="white", width=15,
                  command=self._translate_text).pack(side=tk.LEFT, padx=5)

        self.speak_btn = tk.Button(btn_frame, text="🔊 Speak", font=("Helvetica", 12, "bold"),
                                   bg="#0f3460", fg="white", width=12,
                                   command=self._speak_text)
        self.speak_btn.pack(side=tk.LEFT, padx=5)

        self.tts_status = tk.Label(input_frame, text=self.tts.get_status(),
                                   font=("Helvetica", 9), bg="#16213e", fg="#888888")
        self.tts_status.pack(pady=(0, 5))

        result_frame = tk.Frame(content, bg="#1a1a2e")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.sign_display = tk.Frame(result_frame, bg="#0f0f1a", bd=2,
                                     relief=tk.SUNKEN, width=420, height=320)
        self.sign_display.pack(side=tk.LEFT, padx=10, pady=10)
        self.sign_display.pack_propagate(False)

        self.sign_image_label = tk.Label(self.sign_display, bg="#0f0f1a",
                                         text="Sign image will appear here",
                                         fg="#888888", font=("Helvetica", 12))
        self.sign_image_label.pack(expand=True)

        self.sign_word_label = tk.Label(self.sign_display, text="---",
                                        font=("Helvetica", 24, "bold"),
                                        bg="#0f0f1a", fg="#e94560")
        self.sign_word_label.pack(pady=10)

        nav_frame = tk.Frame(result_frame, bg="#1a1a2e")
        nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.prev_btn = tk.Button(nav_frame, text="◀ Previous", font=("Helvetica", 11),
                                  bg="#533483", fg="white", width=12,
                                  command=self._prev_sign, state=tk.DISABLED)
        self.prev_btn.pack(pady=5)

        self.next_btn = tk.Button(nav_frame, text="Next ▶", font=("Helvetica", 11),
                                  bg="#533483", fg="white", width=12,
                                  command=self._next_sign, state=tk.DISABLED)
        self.next_btn.pack(pady=5)

        self.counter_label = tk.Label(nav_frame, text="0 / 0",
                                      font=("Helvetica", 12), bg="#1a1a2e", fg="white")
        self.counter_label.pack(pady=10)

        details_frame = tk.Frame(result_frame, bg="#16213e", width=350)
        details_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        details_frame.pack_propagate(False)

        tk.Label(details_frame, text="Sign Details", font=("Helvetica", 16, "bold"),
                 bg="#16213e", fg="#e94560").pack(pady=(20, 10))

        self.details_text = tk.Text(details_frame, height=15, width=35,
                                    font=("Helvetica", 11), bg="#0f0f1a", fg="white",
                                    relief=tk.FLAT, wrap=tk.WORD)
        self.details_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        self.details_text.insert(tk.END, "Enter text and click Translate to see sign details...")
        self.details_text.config(state=tk.DISABLED)

    def _translate_text(self):
        text = self.text_input.get(1.0, tk.END).strip()
        if not text:
            return

        normalized = text.upper().replace(",", " ").replace(".", " ").replace("?", " ").replace("!", " ").strip()
        words = normalized.split()
        self.current_signs = []

        phrase_map = {
            "HOW ARE YOU": "HOW-ARE-YOU",
            "THANK YOU": "THANK-YOU",
            "GOOD MORNING": "GOOD-MORNING",
            "GOOD NIGHT": "GOOD-NIGHT",
            "NICE TO MEET YOU": "NICE-TO-MEET-YOU",
            "SEE YOU LATER": "SEE-YOU-LATER",
            "WHAT IS YOUR NAME": "WHAT-IS-YOUR-NAME",
            "MY NAME IS": "MY-NAME-IS",
            "I NEED HELP": "I-NEED-HELP",
            "I DONT UNDERSTAND": "I-DONT-UNDERSTAND",
            "PLEASE HELP ME": "PLEASE-HELP-ME",
            "WHERE IS BATHROOM": "WHERE-IS-BATHROOM",
        }

        db = self.controller.db
        i = 0
        while i < len(words):
            matched = None
            for phrase in sorted(phrase_map, key=lambda x: len(x.split()), reverse=True):
                parts = phrase.split()
                if words[i:i + len(parts)] == parts:
                    matched = phrase_map[phrase]
                    break

            if matched:
                sign = db.get_sign_by_word(matched, self.controller.language)
                if sign:
                    self.current_signs.append(sign)
                else:
                    self.current_signs.append((None, matched, self.controller.language,
                                               "Common phrase",
                                               f"Phrase reference: {matched.replace('-', ' ').title()}",
                                               "See phrase asset", "Follow the sign sequence",
                                               f"Common phrase: {matched.replace('-', ' ').title()}",
                                               "", None, 0.6))
                i += len(phrase.split())
                continue

            word = words[i]
            sign = db.get_sign_by_word(word, self.controller.language)
            if sign:
                self.current_signs.append(sign)
            else:
                self.current_signs.append((None, word, self.controller.language, "Unknown",
                                            f"No dictionary entry for '{word}'", "N/A", "N/A",
                                            "N/A", "N/A", None, 0.6))
            i += 1

        self.current_index = 0
        self._update_display()

    def _update_display(self):
        if not self.current_signs:
            return

        total = len(self.current_signs)
        self.counter_label.config(text=f"{self.current_index + 1} / {total}")

        sign = self.current_signs[self.current_index]
        word = sign[1]
        meaning = sign[4]
        hand_pos = sign[5] or "Not available"
        movement = sign[6] or "Not available"
        example = sign[7] or "Not available"
        image_path = sign[9] if len(sign) > 9 else None

        self.sign_word_label.config(text=word)

        try:
            # Load the existing project asset. No generated/fake hand graphic.
            pil_img = self.image_gen.generate(
                word, hand_pos, movement, meaning, image_path=image_path
            )
            self.current_tk_image = ImageTk.PhotoImage(pil_img)
            self.sign_image_label.config(image=self.current_tk_image, text="")
        except Exception as e:
            self.sign_image_label.config(image="", text=f"[No image: {word}]")
            print(f"Sign asset error: {e}")

        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, f"Word: {word}\n\n")
        self.details_text.insert(tk.END, f"Meaning: {meaning}\n\n")
        self.details_text.insert(tk.END, f"Hand Position: {hand_pos}\n\n")
        self.details_text.insert(tk.END, f"Movement: {movement}\n\n")
        self.details_text.insert(tk.END, f"Example: {example}\n")
        self.details_text.config(state=tk.DISABLED)

        self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_index < total - 1 else tk.DISABLED)

    def _prev_sign(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._update_display()

    def _next_sign(self):
        if self.current_index < len(self.current_signs) - 1:
            self.current_index += 1
            self._update_display()

    def _speak_text(self):
        text = self.text_input.get(1.0, tk.END).strip()
        if not text:
            return

        success, msg = self.tts.speak(text)
        if not success:
            self.tts_status.config(text=msg, fg="#ff4444")
        else:
            self.tts_status.config(text="Spoke: " + text[:30] + "...", fg="#4ecca3")

    def on_hide(self):
        pass
