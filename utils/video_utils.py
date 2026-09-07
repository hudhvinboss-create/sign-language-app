"""
Video processing utilities.
"""
import cv2
import numpy as np
from PIL import Image, ImageTk

class VideoProcessor:
    def __init__(self):
        self.cap = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30

    def open_video(self, video_path):
        """Open a video file."""
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            return False

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.current_frame = 0
        self.is_playing = True
        return True

    def read_frame(self):
        """Read the next frame."""
        if self.cap is None or not self.is_playing:
            return None

        ret, frame = self.cap.read()
        if not ret:
            self.is_playing = False
            return None

        self.current_frame += 1
        return frame

    def get_frame_at(self, frame_number):
        """Get frame at specific position."""
        if self.cap is None:
            return None

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
        return frame if ret else None

    def seek(self, frame_number):
        """Seek to a specific frame."""
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame = frame_number

    def release(self):
        """Release video capture."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_playing = False

    def get_progress(self):
        """Get playback progress (0.0 to 1.0)."""
        if self.total_frames == 0:
            return 0.0
        return self.current_frame / self.total_frames

    @staticmethod
    def frame_to_tkimage(frame, max_size=(640, 480)):
        """Convert OpenCV frame to Tkinter-compatible image."""
        if frame is None:
            return None

        # Resize if needed
        h, w = frame.shape[:2]
        scale = min(max_size[0]/w, max_size[1]/h)
        if scale < 1:
            new_w, new_h = int(w*scale), int(h*scale)
            frame = cv2.resize(frame, (new_w, new_h))

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        return ImageTk.PhotoImage(pil_image)

    @staticmethod
    def frame_to_pil(frame):
        """Convert OpenCV frame to PIL Image."""
        if frame is None:
            return None
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_frame)

class CameraCapture:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.is_running = False

    def start(self):
        """Start camera capture."""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            return False
        self.is_running = True
        return True

    def read_frame(self):
        """Read a frame from camera."""
        if self.cap is None or not self.is_running:
            return None
        ret, frame = self.cap.read()
        return frame if ret else None

    def stop(self):
        """Stop camera capture."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_running = False

    def set_resolution(self, width, height):
        """Set camera resolution."""
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
