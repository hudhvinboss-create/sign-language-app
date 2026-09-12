"""
Video File Translation Screen.
Upload and translate sign language videos.
"""
import tkinter as tk
from tkinter import ttk, filedialog, font
import cv2
import threading
import time
import os
from PIL import Image, ImageTk

class VideoTranslationFrame(tk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(bg="#1a1a2e")

        self.video_processor = None
        self.detector = None
        self.feature_extractor = None
        self.recognizer = None
        self.sentence_builder = None
        self.is_processing = False
        self.current_video_path = None
        self.detected_signs = []
        self.current_tk_image = None

        self._setup_ui()

    def _setup_ui(self):
        # Header
        header = tk.Frame(self, bg="#16213e", height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)

        back_btn = tk.Button(header, text="← Back", font=("Helvetica", 12, "bold"),
                            bg="#16213e", fg="#e94560", relief=tk.FLAT,
                            command=lambda: self.controller.show_frame("Home"))
        back_btn.pack(side=tk.LEFT, padx=20, pady=10)

        title = tk.Label(header, text="Video to Text Translation",
                        font=("Helvetica", 18, "bold"), bg="#16213e", fg="white")
        title.pack(side=tk.LEFT, padx=20, pady=10)

        # Main content
        content = tk.Frame(self, bg="#1a1a2e")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left panel - Video
        left_panel = tk.Frame(content, bg="#1a1a2e")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Upload section
        upload_frame = tk.Frame(left_panel, bg="#16213e", bd=2, relief=tk.RIDGE)
        upload_frame.pack(fill=tk.X, pady=10, padx=10)

        self.upload_btn = tk.Button(upload_frame, text="📁 Upload Video (MP4/AVI/MOV)",
                                   font=("Helvetica", 12, "bold"),
                                   bg="#e94560", fg="white", width=30,
                                   command=self._upload_video)
        self.upload_btn.pack(pady=15)

        self.video_info_label = tk.Label(upload_frame, text="No video selected",
                                        font=("Helvetica", 10),
                                        bg="#16213e", fg="#888888")
        self.video_info_label.pack(pady=5)

        # Video display
        self.video_label = tk.Label(left_panel, bg="#0f0f1a", bd=2, relief=tk.SUNKEN,
                                   text="Video will appear here", fg="#888888")
        self.video_label.pack(pady=10, padx=10)

        # Progress bar
        self.progress = ttk.Progressbar(left_panel, orient=tk.HORIZONTAL, 
                                       length=400, mode='determinate')
        self.progress.pack(pady=10)

        # Video controls
        controls = tk.Frame(left_panel, bg="#1a1a2e")
        controls.pack(pady=10)

        self.play_btn = tk.Button(controls, text="▶ Play", 
                                 font=("Helvetica", 11, "bold"),
                                 bg="#0f3460", fg="white", width=10,
                                 command=self._play_video, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.process_btn = tk.Button(controls, text="🔍 Translate", 
                                    font=("Helvetica", 11, "bold"),
                                    bg="#4ecca3", fg="white", width=12,
                                    command=self._process_video, state=tk.DISABLED)
        self.process_btn.pack(side=tk.LEFT, padx=5)

        # Right panel - Results
        right_panel = tk.Frame(content, bg="#16213e", width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        right_panel.pack_propagate(False)

        # Current sign image
        self.sign_image_label = tk.Label(right_panel, bg="#0f0f1a", bd=2, relief=tk.SUNKEN,
                                        text="No sign detected", fg="#888888",
                                        font=("Helvetica", 10))
        self.sign_image_label.pack(pady=(15, 5), padx=15)

        # Translation result
        tk.Label(right_panel, text="Translation", font=("Helvetica", 16, "bold"),
                bg="#16213e", fg="#e94560").pack(pady=(10, 10))

        self.translation_text = tk.Text(right_panel, height=6, width=40,
                                       font=("Helvetica", 14, "bold"),
                                       bg="#0f0f1a", fg="#4ecca3", relief=tk.FLAT,
                                       wrap=tk.WORD)
        self.translation_text.pack(pady=5, padx=10)
        self.translation_text.insert(tk.END, "Upload a video to see translation...")
        self.translation_text.config(state=tk.DISABLED)

        # Detected signs list
        tk.Label(right_panel, text="Detected Signs", font=("Helvetica", 14, "bold"),
                bg="#16213e", fg="#e94560").pack(pady=(15, 5))

        signs_frame = tk.Frame(right_panel, bg="#16213e")
        signs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(signs_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.signs_listbox = tk.Listbox(signs_frame, yscrollcommand=scrollbar.set,
                                       font=("Helvetica", 11),
                                       bg="#0f0f1a", fg="white", 
                                       selectbackground="#e94560",
                                       height=10)
        self.signs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.signs_listbox.yview)

        # Sign details
        self.sign_detail_label = tk.Label(right_panel, text="Select a sign for details",
                                         font=("Helvetica", 10),
                                         bg="#16213e", fg="#888888",
                                         wraplength=350, justify=tk.LEFT)
        self.sign_detail_label.pack(pady=10, padx=10)

        self.signs_listbox.bind("<<ListboxSelect>>", self._on_sign_select)

        # Save button
        self.save_btn = tk.Button(right_panel, text="💾 Save Translation",
                                 font=("Helvetica", 11),
                                 bg="#533483", fg="white",
                                 command=self._save_translation, state=tk.DISABLED)
        self.save_btn.pack(pady=10)

    def _upload_video(self):
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv"),
            ("MP4 files", "*.mp4"),
            ("AVI files", "*.avi"),
            ("MOV files", "*.mov"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(title="Select Video File", 
                                         filetypes=filetypes)
        if path:
            self.current_video_path = path
            filename = os.path.basename(path)
            self.video_info_label.config(text=f"Selected: {filename}")
            self.play_btn.config(state=tk.NORMAL)
            self.process_btn.config(state=tk.NORMAL)
            self._reset_results()

    def _reset_results(self):
        self.translation_text.config(state=tk.NORMAL)
        self.translation_text.delete(1.0, tk.END)
        self.translation_text.insert(tk.END, "Click 'Translate' to process video...")
        self.translation_text.config(state=tk.DISABLED)
        self.signs_listbox.delete(0, tk.END)
        self.sign_detail_label.config(text="Select a sign for details")
        self.sign_image_label.config(image="", text="No sign detected", fg="#888888")
        self.detected_signs = []
        self.progress['value'] = 0

    def _play_video(self):
        if not self.current_video_path:
            return

        from utils.video_utils import VideoProcessor

        if self.video_processor:
            self.video_processor.release()

        self.video_processor = VideoProcessor()
        if not self.video_processor.open_video(self.current_video_path):
            return

        self.is_processing = True
        self.play_btn.config(text="⏹ Stop", command=self._stop_playback)

        thread = threading.Thread(target=self._playback_loop)
        thread.daemon = True
        thread.start()

    def _playback_loop(self):
        from PIL import Image, ImageTk

        while self.is_processing and self.video_processor.is_playing:
            frame = self.video_processor.read_frame()
            if frame is None:
                break

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            pil_image = pil_image.resize((480, 360), Image.Resampling.LANCZOS)
            tk_image = ImageTk.PhotoImage(pil_image)

            self.video_label.config(image=tk_image)
            self.video_label.image = tk_image

            self.progress['value'] = self.video_processor.get_progress() * 100

            time.sleep(1/30)  # ~30 fps playback

        self.play_btn.config(text="▶ Play", command=self._play_video)
        self.is_processing = False

    def _stop_playback(self):
        self.is_processing = False
        if self.video_processor:
            self.video_processor.release()
        self.play_btn.config(text="▶ Play", command=self._play_video)

    def _process_video(self):
        if not self.current_video_path:
            return

        from ai.hand_detector import HandDetector
        from ai.feature_extractor import FeatureExtractor
        from ai.sign_recognizer import SignRecognizer
        from ai.sentence_builder import SentenceBuilder
        from utils.video_utils import VideoProcessor
        from utils.image_generator import SignImageGenerator

        self.detector = HandDetector()
        self.feature_extractor = FeatureExtractor()
        self.recognizer = SignRecognizer(language=self.controller.language)
        self.sentence_builder = SentenceBuilder(language=self.controller.language)
        self.image_gen = SignImageGenerator()

        self.video_processor = VideoProcessor()
        if not self.video_processor.open_video(self.current_video_path):
            return

        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.play_btn.config(state=tk.DISABLED)
        self.detected_signs = []

        thread = threading.Thread(target=self._translation_loop)
        thread.daemon = True
        thread.start()

    def _translation_loop(self):
        from PIL import Image, ImageTk

        frame_count = 0
        landmark_history = []
        max_history = 10

        while self.is_processing and self.video_processor.is_playing:
            frame = self.video_processor.read_frame()
            if frame is None:
                break

            frame_count += 1

            # Process every 3rd frame for efficiency
            if frame_count % 3 == 0:
                annotated_frame, hands_data, pose_data = self.detector.detect_all(frame)

                features = self.feature_extractor.get_feature_vector(hands_data)
                hand_curls = self.feature_extractor.extract_finger_curls(
                    hands_data.get('landmarks', [])
                )

                if hands_data.get('landmarks'):
                    landmark_history.append(hands_data['landmarks'])
                    if len(landmark_history) > max_history:
                        landmark_history.pop(0)

                motion_features = self.feature_extractor.extract_motion_features(landmark_history)
                motion_class = self.feature_extractor.classify_motion(motion_features)

                sign, confidence, method = self.recognizer.recognize(
                    features, hand_curls, motion_class
                )

                is_confirmed, confirmed_sign, sentence = self.sentence_builder.add_sign(
                    sign, confidence
                )

                if is_confirmed and confirmed_sign:
                    self.detected_signs.append((confirmed_sign, confidence))

                # Update UI
                rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)
                pil_image = pil_image.resize((480, 360), Image.Resampling.LANCZOS)
                tk_image = ImageTk.PhotoImage(pil_image)

                self.video_label.config(image=tk_image)
                self.video_label.image = tk_image

                self.progress['value'] = self.video_processor.get_progress() * 100

                # Update translation text
                self.translation_text.config(state=tk.NORMAL)
                self.translation_text.delete(1.0, tk.END)
                self.translation_text.insert(tk.END, sentence)
                self.translation_text.config(state=tk.DISABLED)

                # Update signs list
                self.signs_listbox.delete(0, tk.END)
                for sign_name, conf in self.detected_signs[-20:]:
                    self.signs_listbox.insert(tk.END, f"{sign_name} ({conf*100:.0f}%)")

                # Show current sign image
                if sign != "UNKNOWN":
                    db = self.controller.db
                    sign_data = db.get_sign_by_word(sign, self.controller.language)
                    if sign_data:
                        try:
                            img = self.image_gen.generate(sign_data[1], sign_data[5] or "", 
                                                         sign_data[6] or "", sign_data[4] or "")
                            img = img.resize((280, 200), Image.Resampling.LANCZOS)
                            self.current_tk_image = ImageTk.PhotoImage(img)
                            self.sign_image_label.config(image=self.current_tk_image, text="")
                        except Exception:
                            self.sign_image_label.config(image="", text=f"[{sign}]")

            time.sleep(0.01)

        # Final sentence
        final_sentence = self.sentence_builder.get_formatted_sentence()
        self.translation_text.config(state=tk.NORMAL)
        self.translation_text.delete(1.0, tk.END)
        self.translation_text.insert(tk.END, final_sentence)
        self.translation_text.config(state=tk.DISABLED)

        # Save to history
        if final_sentence:
            self.controller.db.add_translation(
                "video", self.current_video_path, final_sentence, 
                0.7, self.controller.language
            )

        self.is_processing = False
        self.process_btn.config(state=tk.NORMAL)
        self.play_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)
        self.progress['value'] = 100

    def _on_sign_select(self, event):
        selection = self.signs_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx < len(self.detected_signs):
            sign_name, confidence = self.detected_signs[idx]
            sign_data = self.controller.db.get_sign_by_word(sign_name, self.controller.language)

            if sign_data:
                detail = f"Word: {sign_data[1]}\n"
                detail += f"Meaning: {sign_data[4]}\n"
                detail += f"Hand Position: {sign_data[5] or 'N/A'}\n"
                detail += f"Movement: {sign_data[6] or 'N/A'}\n"
                detail += f"Confidence: {confidence*100:.1f}%"
                self.sign_detail_label.config(text=detail)

                # Show image for selected sign
                try:
                    img = self.image_gen.generate(sign_data[1], sign_data[5] or "", 
                                                 sign_data[6] or "", sign_data[4] or "")
                    img = img.resize((280, 200), Image.Resampling.LANCZOS)
                    self.current_tk_image = ImageTk.PhotoImage(img)
                    self.sign_image_label.config(image=self.current_tk_image, text="")
                except Exception:
                    self.sign_image_label.config(image="", text=f"[{sign_name}]")
            else:
                self.sign_detail_label.config(text=f"Sign: {sign_name}\nNo dictionary entry found.")
                self.sign_image_label.config(image="", text=f"[{sign_name}]")

    def _save_translation(self):
        final_sentence = self.sentence_builder.get_formatted_sentence()
        if final_sentence:
            self.controller.db.add_translation(
                "video", self.current_video_path, final_sentence,
                0.7, self.controller.language
            )
            self.sign_detail_label.config(text="Translation saved to history!")

    def on_hide(self):
        self._stop_playback()
