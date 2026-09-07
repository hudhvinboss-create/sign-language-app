"""
Sign Recognition Model Interface.
Supports loading trained ML models and includes a rule-based fallback for basic signs.
"""
import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import warnings

class SignRecognizer:
    def __init__(self, language="ASL", model_path=None):
        self.language = language
        self.model = None
        self.label_map = {}
        self.inverse_label_map = {}
        self.confidence_threshold = 0.6

        # Rule-based definitions for basic signs (fallback)
        self.rule_based_signs = self._init_rule_based_signs()

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            # Initialize with a simple default model for demo
            self._init_default_model()

    def _init_rule_based_signs(self):
        """
        Define simple rule-based sign patterns.
        Format: {sign_name: {finger_states: [...], description: ...}}
        finger_states: [index, middle, ring, pinky, thumb] (1=extended, 0=folded)
        """
        return {
            "ONE": {
                "finger_states": [[1, 0, 0, 0, 0]],
                "description": "Index finger extended"
            },
            "TWO": {
                "finger_states": [[1, 1, 0, 0, 0]],
                "description": "Index and middle extended"
            },
            "THREE": {
                "finger_states": [[1, 1, 1, 0, 0]],
                "description": "Three fingers extended"
            },
            "FOUR": {
                "finger_states": [[1, 1, 1, 1, 0]],
                "description": "Four fingers extended"
            },
            "FIVE": {
                "finger_states": [[1, 1, 1, 1, 1]],
                "description": "All fingers extended"
            },
            "A": {
                "finger_states": [[0, 0, 0, 0, 1]],
                "description": "Fist with thumb out"
            },
            "B": {
                "finger_states": [[1, 1, 1, 1, 0]],
                "description": "Flat hand, thumb tucked"
            },
            "C": {
                "finger_states": [[1, 1, 1, 1, 1]],  # Approximation
                "description": "Curved hand"
            },
            "HELLO": {
                "finger_states": [[1, 1, 1, 1, 1]],
                "motion": "wave",
                "description": "Open hand waving"
            },
            "THANK-YOU": {
                "finger_states": [[1, 1, 1, 1, 1]],
                "motion": "chin_touch",
                "description": "Hand from chin outward"
            },
            "I-LOVE-YOU": {
                "finger_states": [[1, 0, 0, 1, 1]],  # Index and pinky extended, thumb out
                "description": "I-L-Y handshape"
            },
        }

    def _init_default_model(self):
        """Initialize a simple default model for demonstration."""
        # Create a simple RandomForest with minimal training data for demo
        self.model = RandomForestClassifier(n_estimators=10, random_state=42)

        # Generate some dummy training data for basic signs
        # In production, this would be replaced with real training data
        X = []
        y = []

        basic_signs = ["HELLO", "THANK-YOU", "PLEASE", "SORRY", "HELP", 
                       "YES", "NO", "ONE", "TWO", "THREE", "FOUR", "FIVE"]

        np.random.seed(42)
        for sign in basic_signs:
            for _ in range(5):
                X.append(np.random.randn(146) * 0.1)
                y.append(sign)

        if len(X) > 0:
            X = np.array(X)
            self.model.fit(X, y)
            self.label_map = {i: label for i, label in enumerate(self.model.classes_)}
            self.inverse_label_map = {label: i for i, label in enumerate(self.model.classes_)}

    def load_model(self, model_path):
        """Load a trained model from file."""
        try:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data.get('model')
                self.label_map = data.get('label_map', {})
                self.inverse_label_map = {v: k for k, v in self.label_map.items()}
                self.confidence_threshold = data.get('confidence_threshold', 0.6)
            print(f"Model loaded from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            self._init_default_model()

    def save_model(self, model_path):
        """Save the current model to file."""
        data = {
            'model': self.model,
            'label_map': self.label_map,
            'confidence_threshold': self.confidence_threshold,
            'language': self.language
        }
        with open(model_path, 'wb') as f:
            pickle.dump(data, f)
        print(f"Model saved to {model_path}")

    def recognize(self, features, finger_states=None, motion_features=None):
        """
        Recognize sign from features.
        Returns: (sign_name, confidence, method)
        """
        results = []

        # Try ML model first
        if self.model is not None and features is not None:
            try:
                features = features.reshape(1, -1)
                if hasattr(self.model, 'predict_proba'):
                    probs = self.model.predict_proba(features)[0]
                    pred_idx = np.argmax(probs)
                    confidence = float(probs[pred_idx])
                    sign = self.label_map.get(pred_idx, self.model.classes_[pred_idx])

                    if confidence >= self.confidence_threshold:
                        results.append((sign, confidence, "ml"))
            except Exception as e:
                pass

        # Try rule-based fallback
        if finger_states and len(finger_states) > 0:
            rule_result = self._rule_based_recognize(finger_states, motion_features)
            if rule_result:
                results.append(rule_result)

        # Return best result
        if results:
            results.sort(key=lambda x: x[1], reverse=True)
            return results[0]

        return ("UNKNOWN", 0.0, "none")

    def _rule_based_recognize(self, finger_states, motion_features=None):
        """Rule-based recognition using finger states."""
        if not finger_states or len(finger_states) == 0:
            return None

        hand_state = finger_states[0]  # Primary hand

        best_match = None
        best_score = 0

        for sign_name, rules in self.rule_based_signs.items():
            expected = rules.get("finger_states", [[]])[0]
            if len(expected) == len(hand_state):
                score = sum(1 for a, b in zip(expected, hand_state) if a == b) / len(expected)
                if score > best_score and score >= 0.8:
                    best_score = score
                    best_match = (sign_name, score, "rule-based")

        return best_match

    def get_supported_signs(self):
        """Get list of supported signs."""
        signs = set(self.rule_based_signs.keys())
        if self.model and hasattr(self.model, 'classes_'):
            signs.update(self.model.classes_)
        return sorted(list(signs))

    def set_confidence_threshold(self, threshold):
        self.confidence_threshold = threshold
