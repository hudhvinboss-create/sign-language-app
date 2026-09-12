"""
Feature extraction from hand and body landmarks.
Converts raw MediaPipe landmarks into normalized feature vectors for sign recognition.
"""
import numpy as np
import math

def _dist(a, b):
    return math.sqrt((a['x'] - b['x'])**2 + (a['y'] - b['y'])**2)

def _clamp01(v):
    return max(0.0, min(1.0, v))

class FeatureExtractor:
    def __init__(self):
        self.feature_dim = 126

    def extract_hand_features(self, hand_landmarks):
        if not hand_landmarks or len(hand_landmarks) == 0:
            return np.zeros(self.feature_dim)
        features = []
        for hand in hand_landmarks[:2]:
            wrist = hand[0]
            normalized = []
            for lm in hand:
                normalized.extend([lm['x'] - wrist['x'], lm['y'] - wrist['y'], lm['z'] - wrist['z']])
            features.extend(normalized)
        if len(hand_landmarks) < 2:
            features.extend([0.0] * 63)
        return np.array(features, dtype=np.float32)

    def extract_finger_states(self, hand_landmarks):
        if not hand_landmarks or len(hand_landmarks) == 0:
            return []
        finger_states = []
        finger_indices = [(8, 6), (12, 10), (16, 14), (20, 18)]
        for hand in hand_landmarks:
            states = []
            for tip_idx, pip_idx in finger_indices:
                tip, pip, wrist = hand[tip_idx], hand[pip_idx], hand[0]
                tip_dist = math.sqrt((tip['x']-wrist['x'])**2 + (tip['y']-wrist['y'])**2)
                pip_dist = math.sqrt((pip['x']-wrist['x'])**2 + (pip['y']-wrist['y'])**2)
                states.append(1 if tip_dist > pip_dist else 0)
            thumb_tip, index_base = hand[4], hand[5]
            thumb_dist = math.sqrt((thumb_tip['x']-index_base['x'])**2 + (thumb_tip['y']-index_base['y'])**2)
            states.append(1 if thumb_dist > 0.1 else 0)
            finger_states.append(states)
        return finger_states

    def extract_finger_curls(self, hand_landmarks):
        if not hand_landmarks or len(hand_landmarks) == 0:
            return []
        results = []
        finger_indices = [(8, 6, 5), (12, 10, 9), (16, 14, 13), (20, 18, 17)]
        for hand in hand_landmarks:
            wrist = hand[0]
            palm_size = _dist(hand[9], wrist) or 1e-6
            curls = []
            for tip_idx, _pip_idx, mcp_idx in finger_indices:
                tip_dist = _dist(hand[tip_idx], wrist)
                mcp_dist = _dist(hand[mcp_idx], wrist)
                curls.append(_clamp01((tip_dist - mcp_dist) / palm_size))
            thumb_tip, thumb_mcp = hand[4], hand[2]
            thumb_curl = _clamp01((_dist(thumb_tip, wrist) - _dist(thumb_mcp, wrist)) / palm_size)
            mcp_pts = [hand[5], hand[9], hand[13], hand[17]]
            palm_center = {'x': sum(p['x'] for p in mcp_pts)/4, 'y': sum(p['y'] for p in mcp_pts)/4}
            thumb_to_palm = _dist(thumb_tip, palm_center) / palm_size
            if thumb_to_palm < 0.35:
                thumb_pos = "tucked"
            elif thumb_to_palm < 0.75:
                thumb_pos = "across"
            else:
                thumb_pos = "side"
            results.append({'curls': curls, 'thumb_curl': thumb_curl, 'thumb_pos': thumb_pos})
        return results

    def classify_motion(self, motion_features):
        """Detect subtle webcam hand movement reliably enough for waving signs."""
        if motion_features is None or len(motion_features) == 0:
            return "static"
        mean_velocity = float(motion_features[0])
        # 0.02 was too strict for normal webcam waving. Small real movements
        # often land around 0.005-0.02 after landmark normalization.
        return "moving" if mean_velocity > 0.005 else "static"

    def extract_motion_features(self, landmark_history):
        if len(landmark_history) < 2:
            return np.zeros(20)
        velocities, directions = [], []
        for i in range(1, len(landmark_history)):
            prev, curr = landmark_history[i-1], landmark_history[i]
            if prev and curr and len(prev) > 0 and len(curr) > 0:
                prev_wrist, curr_wrist = prev[0][0], curr[0][0]
                dx, dy = curr_wrist['x']-prev_wrist['x'], curr_wrist['y']-prev_wrist['y']
                velocities.append(math.sqrt(dx**2 + dy**2))
                directions.append(math.atan2(dy, dx))
        if not velocities:
            return np.zeros(20)
        return np.array([np.mean(velocities), np.std(velocities), np.max(velocities),
                         np.mean(directions), np.std(directions)] + [0.0] * 15, dtype=np.float32)

    def get_feature_vector(self, hands_data, landmark_history=None):
        hand_features = self.extract_hand_features(hands_data.get('landmarks', []))
        motion_features = self.extract_motion_features(landmark_history) if landmark_history else np.zeros(20)
        return np.concatenate([hand_features, motion_features])
