"""
Hand and Body Landmark Detection.
Skips mediapipe on CPUs without AVX support. Uses OpenCV fallback.
"""
import cv2
import numpy as np
import os
import subprocess

def _has_avx():
    """Check if CPU supports AVX instructions."""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            return 'avx' in f.read().lower()
    except Exception:
        return False

class HandDetector:
    def __init__(self, max_hands=2, detection_confidence=0.5, tracking_confidence=0.5):
        self.max_hands = max_hands
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence
        self.mode = "unknown"

        has_avx = _has_avx()
        if not has_avx:
            print("[HandDetector] CPU lacks AVX - skipping mediapipe entirely")

        if has_avx and self._try_old_mediapipe():
            self.mode = "mediapipe_old"
            print("[HandDetector] Using mediapipe legacy API")
        elif has_avx and self._try_new_mediapipe():
            self.mode = "mediapipe_new"
            print("[HandDetector] Using mediapipe Tasks API")
        else:
            self.mode = "opencv"
            print("[HandDetector] Using OpenCV skin-tone fallback")

    def _try_old_mediapipe(self):
        try:
            import mediapipe as mp
            if not hasattr(mp, 'solutions'):
                return False
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=self.max_hands,
                min_detection_confidence=self.detection_confidence,
                min_tracking_confidence=self.tracking_confidence
            )
            self.mp_draw = mp.solutions.drawing_utils
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            try:
                self.mp_drawing_styles = mp.solutions.drawing_styles
                self.has_styles = True
            except AttributeError:
                self.has_styles = False
            return True
        except Exception as e:
            print(f"[HandDetector] Old mediapipe failed: {e}")
            return False

    def _try_new_mediapipe(self):
        try:
            from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
            from mediapipe.tasks.python import BaseOptions
            from mediapipe import Image as MPImage

            self.MPImage = MPImage
            models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
            os.makedirs(models_dir, exist_ok=True)

            hand_model_path = os.path.join(models_dir, 'hand_landmarker.task')

            if not os.path.exists(hand_model_path):
                print("[HandDetector] Downloading hand_landmarker.task...")
                import urllib.request
                try:
                    urllib.request.urlretrieve(
                        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
                        hand_model_path
                    )
                    print("[HandDetector] Download complete")
                except Exception as e:
                    print(f"[HandDetector] Download failed: {e}")
                    return False

            base_options = BaseOptions(model_asset_path=hand_model_path)
            options = HandLandmarkerOptions(
                base_options=base_options,
                num_hands=self.max_hands,
                min_hand_detection_confidence=self.detection_confidence,
                min_hand_presence_confidence=self.tracking_confidence
            )
            self.hand_landmarker = HandLandmarker.create_from_options(options)

            self.pose_landmarker = None
            try:
                pose_model_path = os.path.join(models_dir, 'pose_landmarker.task')
                if not os.path.exists(pose_model_path):
                    import urllib.request
                    urllib.request.urlretrieve(
                        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker/float16/1/pose_landmarker.task",
                        pose_model_path
                    )
                from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions
                base_options = BaseOptions(model_asset_path=pose_model_path)
                options = PoseLandmarkerOptions(base_options=base_options)
                self.pose_landmarker = PoseLandmarker.create_from_options(options)
            except Exception:
                pass

            return True
        except Exception as e:
            print(f"[HandDetector] New mediapipe failed: {e}")
            return False

    def detect_hands(self, frame):
        if self.mode == "mediapipe_old":
            return self._detect_hands_old(frame)
        elif self.mode == "mediapipe_new":
            return self._detect_hands_new(frame)
        else:
            return self._detect_hands_opencv(frame)

    def _detect_hands_old(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        annotated = frame.copy()
        landmarks_list = []
        handedness_list = []

        if results.multi_hand_landmarks:
            for idx, hl in enumerate(results.multi_hand_landmarks):
                try:
                    if getattr(self, 'has_styles', False):
                        self.mp_draw.draw_landmarks(annotated, hl, self.mp_hands.HAND_CONNECTIONS,
                            self.mp_drawing_styles.get_default_hand_landmarks_style(),
                            self.mp_drawing_styles.get_default_hand_connections_style())
                    else:
                        self.mp_draw.draw_landmarks(annotated, hl, self.mp_hands.HAND_CONNECTIONS)
                except Exception:
                    self.mp_draw.draw_landmarks(annotated, hl, self.mp_hands.HAND_CONNECTIONS)

                landmarks = []
                for lm in hl.landmark:
                    h, w, _ = frame.shape
                    landmarks.append({'x': lm.x, 'y': lm.y, 'z': lm.z,
                                      'px': int(lm.x * w), 'py': int(lm.y * h)})
                landmarks_list.append(landmarks)
                if results.multi_handedness:
                    handedness_list.append(results.multi_handedness[idx].classification[0].label)
                else:
                    handedness_list.append("Unknown")
        return annotated, landmarks_list, handedness_list

    def _detect_hands_new(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = self.MPImage(image_format=self.MPImage.ImageFormat.SRGB, data=rgb_frame)
        results = self.hand_landmarker.detect(mp_image)
        annotated = frame.copy()
        landmarks_list = []
        handedness_list = []

        if results.hand_landmarks:
            for hand_landmarks in results.hand_landmarks:
                h, w, _ = frame.shape
                pts = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]
                for p in pts:
                    cv2.circle(annotated, p, 3, (0, 255, 0), -1)
                connections = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
                             (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),
                             (0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17)]
                for a, b in connections:
                    if a < len(pts) and b < len(pts):
                        cv2.line(annotated, pts[a], pts[b], (255, 0, 0), 1)

                landmarks = []
                for lm in hand_landmarks:
                    landmarks.append({'x': lm.x, 'y': lm.y, 'z': lm.z,
                                      'px': int(lm.x * w), 'py': int(lm.y * h)})
                landmarks_list.append(landmarks)
                handedness_list.append("Unknown")
        return annotated, landmarks_list, handedness_list

    def _detect_hands_opencv(self, frame):
        annotated = frame.copy()
        h, w, _ = frame.shape

        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        lower = np.array([0, 133, 77], dtype=np.uint8)
        upper = np.array([255, 173, 127], dtype=np.uint8)
        mask = cv2.inRange(ycrcb, lower, upper)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.dilate(mask, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:self.max_hands]

        landmarks_list = []
        handedness_list = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 5000:
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)
            cv2.drawContours(annotated, [cnt], -1, (0, 255, 0), 2)

            hull = cv2.convexHull(cnt)
            cv2.drawContours(annotated, [hull], -1, (255, 0, 0), 1)

            hull_indices = cv2.convexHull(cnt, returnPoints=False)
            defects = []
            if len(hull_indices) > 3:
                try:
                    defects = cv2.convexityDefects(cnt, hull_indices)
                except cv2.error:
                    pass

            landmarks = self._generate_opencv_landmarks(cnt, defects, x, y, bw, bh, w, h)
            landmarks_list.append(landmarks)
            handedness_list.append("Unknown")

            for lm in landmarks:
                cv2.circle(annotated, (lm['px'], lm['py']), 4, (0, 0, 255), -1)

            connections = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),
                        (0,9),(9,10),(10,11),(11,12),(0,13),(13,14),(14,15),(15,16),
                        (0,17),(17,18),(18,19),(19,20),(5,9),(9,13),(13,17)]
            for a, b in connections:
                pa = (landmarks[a]['px'], landmarks[a]['py'])
                pb = (landmarks[b]['px'], landmarks[b]['py'])
                cv2.line(annotated, pa, pb, (255, 255, 0), 1)

        return annotated, landmarks_list, handedness_list

    def _generate_opencv_landmarks(self, cnt, defects, bx, by, bw, bh, img_w, img_h):
        landmarks = []
        wrist_x = bx + bw // 2
        wrist_y = by + bh
        landmarks.append({'x': wrist_x / img_w, 'y': wrist_y / img_h, 'z': 0,
                          'px': wrist_x, 'py': wrist_y})

        top = tuple(cnt[cnt[:, :, 1].argmin()][0])
        left = tuple(cnt[cnt[:, :, 0].argmin()][0])
        right = tuple(cnt[cnt[:, :, 0].argmax()][0])

        fingertips = []
        if defects is not None and len(defects) > 0:
            for i in range(defects.shape[0]):
                defect = defects[i]
                if defect.ndim > 1:
                    defect = defect[0]
                s, e, f, d = int(defect[0]), int(defect[1]), int(defect[2]), int(defect[3])
                if d > 10000:
                    start = tuple(cnt[s][0])
                    end = tuple(cnt[e][0])
                    fingertips.append(start)
                    fingertips.append(end)

        fingertips = list(set(fingertips))
        fingertips.sort(key=lambda p: p[1])

        if len(fingertips) < 4:
            top_points = sorted(cnt, key=lambda p: p[0][1])[:8]
            fingertips = [tuple(p[0]) for p in top_points]

        thumb_tip = left if left[0] < wrist_x else right
        for i in range(1, 5):
            t = i / 4.0
            x = int(wrist_x + (thumb_tip[0] - wrist_x) * t)
            y = int(wrist_y + (thumb_tip[1] - wrist_y) * t)
            landmarks.append({'x': x / img_w, 'y': y / img_h, 'z': 0, 'px': x, 'py': y})

        finger_tips = fingertips[:4] if len(fingertips) >= 4 else [top, top, top, top]
        for tip in finger_tips:
            for i in range(1, 5):
                t = i / 4.0
                x = int(wrist_x + (tip[0] - wrist_x) * t)
                y = int(wrist_y + (tip[1] - wrist_y) * t)
                landmarks.append({'x': x / img_w, 'y': y / img_h, 'z': 0, 'px': x, 'py': y})

        while len(landmarks) < 21:
            landmarks.append({'x': wrist_x / img_w, 'y': wrist_y / img_h, 'z': 0,
                              'px': wrist_x, 'py': wrist_y})

        return landmarks[:21]

    def detect_pose(self, frame):
        if self.mode == "mediapipe_old":
            return self._detect_pose_old(frame)
        elif self.mode == "mediapipe_new" and hasattr(self, 'pose_landmarker') and self.pose_landmarker:
            return self._detect_pose_new(frame)
        else:
            return frame.copy(), None

    def _detect_pose_old(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        annotated = frame.copy()
        pose_landmarks = None
        if results.pose_landmarks:
            try:
                if getattr(self, 'has_styles', False):
                    self.mp_draw.draw_landmarks(annotated, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style())
                else:
                    self.mp_draw.draw_landmarks(annotated, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            except Exception:
                self.mp_draw.draw_landmarks(annotated, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            pose_landmarks = [{'x': lm.x, 'y': lm.y, 'z': lm.z, 'visibility': lm.visibility}
                              for lm in results.pose_landmarks.landmark]
        return annotated, pose_landmarks

    def _detect_pose_new(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = self.MPImage(image_format=self.MPImage.ImageFormat.SRGB, data=rgb_frame)
        results = self.pose_landmarker.detect(mp_image)
        annotated = frame.copy()
        pose_landmarks = None
        if results.pose_landmarks:
            pose_landmarks = [{'x': lm.x, 'y': lm.y, 'z': lm.z,
                               'visibility': getattr(lm, 'visibility', 1.0)}
                              for lm in results.pose_landmarks]
        return annotated, pose_landmarks

    def detect_all(self, frame):
        hand_frame, hand_landmarks, handedness = self.detect_hands(frame)
        pose_frame, pose_landmarks = self.detect_pose(hand_frame)
        return pose_frame, {
            'landmarks': hand_landmarks,
            'handedness': handedness,
            'count': len(hand_landmarks)
        }, {'landmarks': pose_landmarks}

    def release(self):
        if self.mode == "mediapipe_old":
            self.hands.close()
            self.pose.close()
        elif self.mode == "mediapipe_new":
            if hasattr(self, 'hand_landmarker') and self.hand_landmarker:
                self.hand_landmarker.close()
            if hasattr(self, 'pose_landmarker') and self.pose_landmarker:
                self.pose_landmarker.close()
