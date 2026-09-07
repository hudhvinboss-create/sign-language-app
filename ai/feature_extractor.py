"""
Feature extraction from hand and body landmarks.
Converts raw MediaPipe landmarks into normalized feature vectors for sign recognition.
"""
import numpy as np
import math

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
