"""Pretrained ASL live recognizer adapted from a landmark-skeleton pipeline.

The model is downloaded on first ASL use from the public pretrained
MediaPipe-ASL-sign-language-recognition project. The same normalized skeleton
rendering is used for live inference, which avoids feeding raw webcam pixels
through a model trained on a different representation.
"""
from pathlib import Path
from urllib.request import Request, urlopen

import cv2
import numpy as np

MODEL_URL = (
    "https://raw.githubusercontent.com/punpuniacitizen/"
    "MediaPipe-ASL-sign-language-recognition/main/asl_cnn_model.onnx"
)
LABELS = tuple("abcdefghijklmnopqrstuvwxyz")
MODEL_SIZE = 96
CANVAS_SIZE = 192
HAND_FILL = 0.7


class ASLLiveRecognizer:
    def __init__(self, model_path="models/asl_cnn_model.onnx"):
        self.model_path = Path(model_path)
        self.session = None
        self.input_name = None
        self._load_error = None

    def _ensure_model(self):
        if self.session is not None:
            return True
        try:
            import onnxruntime as ort
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.model_path.exists():
                request = Request(MODEL_URL, headers={"User-Agent": "sign-language-app"})
                with urlopen(request, timeout=30) as response, open(self.model_path, "wb") as out:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
            self.session = ort.InferenceSession(str(self.model_path), providers=["CPUExecutionProvider"])
            self.input_name = self.session.get_inputs()[0].name
            return True
        except Exception as exc:
            self._load_error = str(exc)
            self.session = None
            return False

    @staticmethod
    def _normalize(points):
        points = np.asarray(points, dtype=np.float32)
        lo = points.min(axis=0)
        hi = points.max(axis=0)
        extent = hi - lo
        box_size = max(float(extent.max()) / HAND_FILL, 1.0)
        centre = lo + extent / 2.0
        origin = centre - box_size / 2.0
        return ((points - origin) / box_size).astype(np.float32)

    @staticmethod
    def _render(points):
        canvas = np.zeros((CANVAS_SIZE, CANVAS_SIZE, 3), dtype=np.uint8)
        pts = np.rint(points * CANVAS_SIZE).astype(np.int32)
        connections = (
            (0,1),(0,5),(0,17),(5,9),(9,13),(13,17),
            (1,2),(2,3),(3,4),(5,6),(6,7),(7,8),
            (9,10),(10,11),(11,12),(13,14),(14,15),(15,16),
            (17,18),(18,19),(19,20)
        )
        for a, b in connections:
            cv2.line(canvas, tuple(pts[a]), tuple(pts[b]), (128,128,128), 2, cv2.LINE_AA)
        for i, p in enumerate(pts):
            cv2.circle(canvas, tuple(p), 3, (224,224,224), -1, cv2.LINE_AA)
            cv2.circle(canvas, tuple(p), 2, (48,128,255), -1, cv2.LINE_AA)
        return cv2.resize(canvas, (MODEL_SIZE, MODEL_SIZE), interpolation=cv2.INTER_AREA)

    def predict(self, hand_landmarks):
        """Return (letter, confidence, method) or UNKNOWN when unavailable."""
        if not hand_landmarks or len(hand_landmarks) != 21:
            return ("UNKNOWN", 0.0, "asl-pretrained")
        if not self._ensure_model():
            return ("UNKNOWN", 0.0, "asl-pretrained")

        points = np.array([[p["x"], p["y"]] for p in hand_landmarks], dtype=np.float32)
        normalized = self._normalize(points)
        image = self._render(normalized).astype(np.float32)[None, ...]
        try:
            outputs = self.session.run(None, {self.input_name: image})
            logits = np.asarray(outputs[0][0], dtype=np.float32)
            logits -= logits.max()
            probs = np.exp(logits)
            probs /= max(float(probs.sum()), 1e-9)
            idx = int(np.argmax(probs))
            label = LABELS[idx] if idx < len(LABELS) else "UNKNOWN"
            return (label.upper(), float(probs[idx]), "asl-pretrained")
        except Exception:
            return ("UNKNOWN", 0.0, "asl-pretrained")
