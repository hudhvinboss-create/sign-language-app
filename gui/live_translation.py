"""
Live Camera Translation Screen.
Real-time sign language detection from webcam.
"""
import tkinter as tk
from tkinter import ttk, font
import cv2
import threading
import time
from PIL import Image, ImageTk

class LiveTranslationFrame(tk.Frame):
    def __init__(self, parent, controller, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.controller = controller
        self.configure(bg="#1a1a2e")

        self.camera = None
        self.is_running = False
        self.detector = None
        self.feature_extractor = None
        self.recognizer = None
        self.sentence_builder = None
        self.landmark_history = []
        self.max_history = 10
        self.current_tk_image = None

        # Run hand/pose detection every Nth frame instead of every frame.
        # Detection is the expensive part of the loop; raise this to 2 or 3
        # if the feed still feels laggy (camera capture stays full-rate,
        # only detection+recognition is skipped on the frames in between).
        self.detect_every_n_frames = 1
        self._last_annotated_frame = None
        self._last_hands_data = {'landmarks': [], 'handedness': [], 'count': 0}
        self._last_pose_data = {'landmarks': None}

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

        title = tk.Label(header, text="Live Sign Language Translation",
                        font=("Helvetica", 18, "bold"), bg="#16213e", fg="white")
        title.pack(side=tk.LEFT, padx=20, pady=10)

        # Main content
        content = tk.Frame(self, bg="#1a1a2e")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Camera feed
        left_panel = tk.Frame(content, bg="#1a1a2e")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.camera_label = tk.Label(left_panel, bg="#0f0f1a", bd=2, relief=tk.SUNKEN)
        self.camera_label.pack(pady=10, padx=10)

        # Camera controls
        controls = tk.Frame(left_panel, bg="#1a1a2e")
        controls.pack(pady=10)

        self.start_btn = tk.Button(controls, text="▶ Start Camera", 
                                  font=("Helvetica", 12, "bold"),
                                  bg="#e94560", fg="white", width=15,
                                  command=self._start_camera)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(controls, text="⏹ Stop", 
                                 font=("Helvetica", 12, "bold"),
                                 bg="#533483", fg="white", width=15,
                                 command=self._stop_camera, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Right panel - Translation results
        right_panel = tk.Frame(content, bg="#16213e", width=380)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        right_panel.pack_propagate(False)

        # Current sign image
        self.sign_image_label = tk.Label(right_panel, bg="#0f0f1a", bd=2, relief=tk.SUNKEN,
                                        text="No sign detected", fg="#888888",
                                        font=("Helvetica", 10))
        self.sign_image_label.pack(pady=(15, 5), padx=15)

        # Current sign
        tk.Label(right_panel, text="Current Sign", font=("Helvetica", 14, "bold"),
                bg="#16213e", fg="#e94560").pack(pady=(10, 5))

        self.current_sign_label = tk.Label(right_panel, text="---",
                                          font=("Helvetica", 24, "bold"),
                                          bg="#16213e", fg="white")
        self.current_sign_label.pack(pady=5)

        # Confidence
        self.confidence_label = tk.Label(right_panel, text="Confidence: 0%",
                                        font=("Helvetica", 12),
                                        bg="#16213e", fg="#a0a0a0")
        self.confidence_label.pack(pady=5)

        # Meaning
        tk.Label(right_panel, text="Meaning", font=("Helvetica", 14, "bold"),
                bg="#16213e", fg="#e94560").pack(pady=(15, 5))

        self.meaning_text = tk.Text(right_panel, height=3, width=35,
                                   font=("Helvetica", 11),
                                   bg="#0f0f1a", fg="white", relief=tk.FLAT,
                                   wrap=tk.WORD)
        self.meaning_text.pack(pady=5, padx=10)
        self.meaning_text.insert(tk.END, "Start camera to begin translation...")
        self.meaning_text.config(state=tk.DISABLED)

        # Sentence
        tk.Label(right_panel, text="Sentence", font=("Helvetica", 14, "bold"),
                bg="#16213e", fg="#e94560").pack(pady=(15, 5))

        self.sentence_text = tk.Text(right_panel, height=4, width=35,
                                    font=("Helvetica", 14, "bold"),
                                    bg="#0f0f1a", fg="#4ecca3", relief=tk.FLAT,
                                    wrap=tk.WORD)
        self.sentence_text.pack(pady=5, padx=10)
        self.sentence_text.insert(tk.END, "")
        self.sentence_text.config(state=tk.DISABLED)

        # Status
        self.status_label = tk.Label(right_panel, text="Status: Ready",
                                    font=("Helvetica", 10),
                                    bg="#16213e", fg="#888888")
        self.status_label.pack(pady=(15, 5))

        # Clear button
        tk.Button(right_panel, text="Clear Sentence", font=("Helvetica", 10),
                 bg="#533483", fg="white", command=self._clear_sentence).pack(pady=10)

    def _start_camera(self):
        from ai.hand_detector import HandDetector
        from ai.feature_extractor import FeatureExtractor
        from ai.sign_recognizer import SignRecognizer
        from ai.sentence_builder import SentenceBuilder
        from utils.video_utils import CameraCapture
        from utils.image_generator import SignImageGenerator

        self.detector = HandDetector()
        self.feature_extractor = FeatureExtractor()
        self.recognizer = SignRecognizer(language=self.controller.language)
        self.sentence_builder = SentenceBuilder(language=self.controller.language)
        self.image_gen = SignImageGenerator()
        self.camera = CameraCapture()

        if not self.camera.start():
            self.status_label.config(text="Status: Camera Error - Check permissions")
            return

        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Status: Running")

        # Start processing thread
        self.process_thread = threading.Thread(target=self._process_loop)
        self.process_thread.daemon = True
        self.process_thread.start()

    def _stop_camera(self):
        self.is_running = False
        if self.camera:
            self.camera.stop()
        if self.detector:
            self.detector.release()

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Stopped")
        self.camera_label.config(image="")

    def _process_loop(self):
        import numpy as np
        from PIL import Image, ImageTk

        frame_count = 0
        while self.is_running:
            frame = self.camera.read_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            frame_count += 1

            # Detect hands and pose (skip on some frames if configured, and
            # reuse the last known result so recognition/sentence-building
            # still has data to work with each loop).
            if frame_count % self.detect_every_n_frames == 0:
                annotated_frame, hands_data, pose_data = self.detector.detect_all(frame)
                self._last_annotated_frame = annotated_frame
                self._last_hands_data = hands_data
                self._last_pose_data = pose_data
            else:
                annotated_frame = frame
                hands_data = self._last_hands_data
                pose_data = self._last_pose_data

            # Extract features
            features = self.feature_extractor.get_feature_vector(hands_data)
            hand_curls = self.feature_extractor.extract_finger_curls(
                hands_data.get('landmarks', [])
            )

            # Store landmark history for motion
            if hands_data.get('landmarks'):
                self.landmark_history.append(hands_data['landmarks'])
                if len(self.landmark_history) > self.max_history:
                    self.landmark_history.pop(0)

            motion_features = self.feature_extractor.extract_motion_features(self.landmark_history)
            motion_class = self.feature_extractor.classify_motion(motion_features)

            # Recognize sign
            sign, confidence, method = self.recognizer.recognize(
                features, hand_curls, motion_class
            )

            # Build sentence
            is_confirmed, confirmed_sign, sentence = self.sentence_builder.add_sign(
                sign, confidence
            )

            # Update UI (every 3 frames to reduce load).
            # IMPORTANT: this thread must never touch Tk widgets directly --
            # Tkinter is not thread-safe. self.after(0, ...) schedules the
            # actual widget updates to run on the main/GUI thread instead.
            if frame_count % 3 == 0:
                self.after(0, self._update_ui, annotated_frame, sign, confidence,
                           sentence, hands_data.get('count', 0))

            # No extra sleep needed -- detect_all() + self.camera.read_frame()
            # already pace the loop to the camera/model's real throughput.
            # A fixed sleep here only adds latency on top of that.

    def _update_ui(self, frame, sign, confidence, sentence, hand_count):
        from PIL import Image, ImageTk

        # Update camera feed
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        pil_image = pil_image.resize((480, 360), Image.Resampling.LANCZOS)
        tk_image = ImageTk.PhotoImage(pil_image)

        self.camera_label.config(image=tk_image)
        self.camera_label.image = tk_image  # Keep reference

        # Update sign info
        if sign != "UNKNOWN":
            self.current_sign_label.config(text=sign)
            self.confidence_label.config(
                text=f"Confidence: {confidence*100:.1f}%",
                fg="#4ecca3" if confidence > 0.7 else "#ffa500" if confidence > 0.5 else "#ff4444"
            )

            # Get meaning from database
            db = self.controller.db
            sign_data = db.get_sign_by_word(sign, self.controller.language)
            if sign_data:
                self.meaning_text.config(state=tk.NORMAL)
                self.meaning_text.delete(1.0, tk.END)
                self.meaning_text.insert(tk.END, sign_data[4])  # meaning column
                self.meaning_text.config(state=tk.DISABLED)

                # Generate sign image card
                try:
                    word = sign_data[1]
                    hand_pos = sign_data[5] or ""
                    movement = sign_data[6] or ""
                    meaning = sign_data[4] or ""
                    img = self.image_gen.generate(word, hand_pos, movement, meaning)
                    img = img.resize((280, 200), Image.Resampling.LANCZOS)
                    self.current_tk_image = ImageTk.PhotoImage(img)
                    self.sign_image_label.config(image=self.current_tk_image, text="")
                except Exception as e:
                    self.sign_image_label.config(image="", text=f"[{sign}]")

            self.status_label.config(
                text=f"Status: {hand_count} hand(s) | opencv"
            )
        else:
            self.current_sign_label.config(text="---")
            self.confidence_label.config(text="Confidence: 0%", fg="#a0a0a0")
            self.sign_image_label.config(image="", text="No sign detected", fg="#888888")
            self.status_label.config(text=f"Status: {hand_count} hand(s)")

        # Update sentence
        self.sentence_text.config(state=tk.NORMAL)
        self.sentence_text.delete(1.0, tk.END)
        self.sentence_text.insert(tk.END, sentence)
        self.sentence_text.config(state=tk.DISABLED)

        # Save to history if sentence is complete
        if sentence and len(sentence) > 0 and sign == "UNKNOWN":
            self.controller.db.add_translation(
                "live", "camera", sentence, confidence, self.controller.language
            )

    def _clear_sentence(self):
        if self.sentence_builder:
            self.sentence_builder.reset()
        self.sentence_text.config(state=tk.NORMAL)
        self.sentence_text.delete(1.0, tk.END)
        self.sentence_text.config(state=tk.DISABLED)

    def on_show(self):
        pass

    def on_hide(self):
        self._stop_camera()
