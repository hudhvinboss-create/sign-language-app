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
        self.feature_dim = 126  # 21 landmarks * 3 coords * 2 hands (max)

    def extract_hand_features(self, hand_landmarks):
        """
        Extract normalized features from hand landmarks.
        Returns a fixed-size feature vector.
        """
        if not hand_landmarks or len(hand_landmarks) == 0:
            return np.zeros(self.feature_dim)

        features = []

        for hand in hand_landmarks[:2]:  # Max 2 hands
            # Normalize landmarks relative to wrist (landmark 0)
            wrist = hand[0]
            normalized = []

            for lm in hand:
                normalized.extend([
                    lm['x'] - wrist['x'],
                    lm['y'] - wrist['y'],
                    lm['z'] - wrist['z']
                ])

            features.extend(normalized)

        # Pad if only one hand
        if len(hand_landmarks) < 2:
            features.extend([0.0] * 63)

        return np.array(features, dtype=np.float32)

    def extract_finger_states(self, hand_landmarks):
        """
        Extract finger extended/folded states.
        Useful for rule-based recognition.
        """
        if not hand_landmarks or len(hand_landmarks) == 0:
            return []

        finger_states = []

        # Finger tip and pip (proximal interphalangeal joint) indices
        finger_indices = [
            (8, 6),   # Index
            (12, 10), # Middle
            (16, 14), # Ring
            (20, 18)  # Pinky
        ]

        for hand in hand_landmarks:
            states = []
            for tip_idx, pip_idx in finger_indices:
                # Check if tip is above pip (extended) - simplified
                tip = hand[tip_idx]
                pip = hand[pip_idx]

                # Calculate distance from wrist
                wrist = hand[0]
                tip_dist = math.sqrt(
                    (tip['x'] - wrist['x'])**2 + 
                    (tip['y'] - wrist['y'])**2
                )
                pip_dist = math.sqrt(
                    (pip['x'] - wrist['x'])**2 + 
                    (pip['y'] - wrist['y'])**2
                )

                states.append(1 if tip_dist > pip_dist else 0)

            # Thumb: check if tip is far from index base
            thumb_tip = hand[4]
            index_base = hand[5]
            thumb_dist = math.sqrt(
                (thumb_tip['x'] - index_base['x'])**2 +
                (thumb_tip['y'] - index_base['y'])**2
            )
            states.append(1 if thumb_dist > 0.1 else 0)

            finger_states.append(states)

        return finger_states

    def extract_finger_curls(self, hand_landmarks):
        """
        Continuous 0.0 (fully folded) - 1.0+ (fully extended) curl ratio per
        finger, plus a thumb curl ratio and a coarse thumb-position category.

        This replaces the old binary extract_finger_states() for recognition
        purposes: a 0/1 vector meant many genuinely different signs (e.g. FIVE
        and C, or FOUR and B) produced the *exact same* pattern and collided.
        Continuous ranges let sign definitions distinguish "fully extended"
        from "partially curled" instead of only "extended" vs "folded".
        """
        if not hand_landmarks or len(hand_landmarks) == 0:
            return []

        results = []
        # (tip, pip/mid-joint, mcp/knuckle) landmark indices per finger
        finger_indices = [
            (8, 6, 5),    # Index
            (12, 10, 9),  # Middle
            (16, 14, 13), # Ring
            (20, 18, 17), # Pinky
        ]

        for hand in hand_landmarks:
            wrist = hand[0]
            # Middle-finger-knuckle-to-wrist distance as a scale reference,
            # so curl values are roughly independent of hand size/distance
            # from the camera.
            palm_size = _dist(hand[9], wrist) or 1e-6

            curls = []
            for tip_idx, _pip_idx, mcp_idx in finger_indices:
                tip_dist = _dist(hand[tip_idx], wrist)
                mcp_dist = _dist(hand[mcp_idx], wrist)
                extension = (tip_dist - mcp_dist) / palm_size
                curls.append(_clamp01(extension))

            thumb_tip = hand[4]
            thumb_mcp = hand[2]
            thumb_extension = (_dist(thumb_tip, wrist) - _dist(thumb_mcp, wrist)) / palm_size
            thumb_curl = _clamp01(thumb_extension)

            # Palm center = average of the four MCP knuckles.
            mcp_pts = [hand[5], hand[9], hand[13], hand[17]]
            palm_center = {
                'x': sum(p['x'] for p in mcp_pts) / 4,
                'y': sum(p['y'] for p in mcp_pts) / 4,
            }
            thumb_to_palm = _dist(thumb_tip, palm_center) / palm_size
            if thumb_to_palm < 0.35:
                thumb_pos = "tucked"       # folded flat against/under the palm
            elif thumb_to_palm < 0.75:
                thumb_pos = "across"       # crossing in front of the fist (e.g. A/S)
            else:
                thumb_pos = "side"         # extended out to the side (e.g. FIVE, A)

            results.append({'curls': curls, 'thumb_curl': thumb_curl, 'thumb_pos': thumb_pos})

        return results

    def classify_motion(self, motion_features):
        """
        Coarse "static" vs "moving" classification from motion_features
        (see extract_motion_features). Used to gate motion-based signs like
        HELLO/THANK-YOU so they stop colliding with static handshapes like
        FIVE that happen to look the same when the hand isn't moving.
        """
        if motion_features is None or len(motion_features) == 0:
            return "static"
        mean_velocity = float(motion_features[0])
        return "moving" if mean_velocity > 0.02 else "static"

    def extract_motion_features(self, landmark_history):
        """
        Extract motion features from a sequence of landmarks.
        landmark_history: list of hand_landmarks over time
        """
        if len(landmark_history) < 2:
            return np.zeros(20)

        # Calculate velocity and direction of wrist movement
        velocities = []
        directions = []

        for i in range(1, len(landmark_history)):
            prev = landmark_history[i-1]
            curr = landmark_history[i]

            if prev and curr and len(prev) > 0 and len(curr) > 0:
                prev_wrist = prev[0][0]  # First hand, wrist
                curr_wrist = curr[0][0]

                dx = curr_wrist['x'] - prev_wrist['x']
                dy = curr_wrist['y'] - prev_wrist['y']

                velocity = math.sqrt(dx**2 + dy**2)
                direction = math.atan2(dy, dx)

                velocities.append(velocity)
                directions.append(direction)

        if not velocities:
            return np.zeros(20)

        # Return statistics
        return np.array([
            np.mean(velocities) if velocities else 0,
            np.std(velocities) if velocities else 0,
            np.max(velocities) if velocities else 0,
            np.mean(directions) if directions else 0,
            np.std(directions) if directions else 0,
        ] + [0.0] * 15, dtype=np.float32)

    def get_feature_vector(self, hands_data, landmark_history=None):
        """
        Get complete feature vector for recognition.
        """
        hand_features = self.extract_hand_features(hands_data.get('landmarks', []))

        if landmark_history:
            motion_features = self.extract_motion_features(landmark_history)
        else:
            motion_features = np.zeros(20)

        return np.concatenate([hand_features, motion_features])
