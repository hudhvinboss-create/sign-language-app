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
    def __init__(self, language="ASL", model_path=None, use_demo_model=False):
        self.language = language
        self.model = None
        self.label_map = {}
        self.inverse_label_map = {}
        self.confidence_threshold = 0.6

        # Rule-based definitions for basic signs (fallback)
        self.rule_based_signs = self._init_rule_based_signs()

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        elif use_demo_model:
            # This fits a RandomForest on pure random noise (see below) --
            # it has never seen a real gesture. It's useful for exercising
            # the pipeline end-to-end, but it can actively hurt recognition
            # quality: 5 of its 12 fake classes are the numbers ONE-FIVE, so
            # it can add extra numbers-bias on top of real predictions.
            # Left OFF by default; pass use_demo_model=True to re-enable,
            # or load_model(...) with a model trained on real gesture data.
            self._init_default_model()

    # Curl-ratio bands used by the sign definitions below. These are ranges,
    # not exact values, which is the main fix: the old code required an
    # *exact* binary match, so any two signs with the same 0/1 pattern
    # (FIVE vs C, FOUR vs B, FIVE vs HELLO/THANK-YOU) were indistinguishable.
    EXTENDED = (0.55, 1.5)   # finger fully out straight
    FOLDED = (0.0, 0.30)     # finger curled into the palm
    CURLED = (0.25, 0.60)    # partially bent (e.g. a "C" shape)

    def _init_rule_based_signs(self):
        """
        Rule-based sign definitions using continuous curl ranges (from
        FeatureExtractor.extract_finger_curls) instead of exact binary
        patterns, plus an optional thumb position and required motion state.
        finger_curls order: [index, middle, ring, pinky].
        """
        E, F, C = self.EXTENDED, self.FOLDED, self.CURLED
        return {
            "ONE": {
                "finger_curls": [E, F, F, F], "thumb_curl": F,
                "description": "Index finger extended",
            },
            "TWO": {
                "finger_curls": [E, E, F, F], "thumb_curl": F,
                "description": "Index and middle extended",
            },
            "THREE": {
                "finger_curls": [E, E, E, F], "thumb_curl": F,
                "description": "Three fingers extended",
            },
            "FOUR": {
                "finger_curls": [E, E, E, E], "thumb_curl": F, "thumb_pos": "tucked",
                "description": "Four fingers extended, thumb tucked",
            },
            "FIVE": {
                "finger_curls": [E, E, E, E], "thumb_curl": E, "thumb_pos": "side",
                "description": "All fingers and thumb extended",
            },
            "A": {
                "finger_curls": [F, F, F, F], "thumb_curl": E, "thumb_pos": "side",
                "description": "Fist with thumb out to the side",
            },
            "B": {
                "finger_curls": [E, E, E, E], "thumb_curl": F, "thumb_pos": "across",
                "description": "Flat hand, thumb folded across the palm",
            },
            "C": {
                "finger_curls": [C, C, C, C], "thumb_curl": C,
                "description": "Curved hand (partial curl on all fingers)",
            },
            "HELLO": {
                "finger_curls": [E, E, E, E], "thumb_curl": E, "motion": "moving",
                "description": "Open hand, waving",
            },
            "THANK-YOU": {
                "finger_curls": [E, E, E, E], "thumb_curl": E, "motion": "moving",
                "description": "Open hand moving outward from chin",
            },
            "I-LOVE-YOU": {
                "finger_curls": [E, F, F, E], "thumb_curl": E, "thumb_pos": "side",
                "description": "Index, pinky, and thumb extended",
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

    def recognize(self, features, hand_curls=None, motion_class="static"):
        """
        Recognize sign from features.
        hand_curls: output of FeatureExtractor.extract_finger_curls()
        motion_class: "static" or "moving", from FeatureExtractor.classify_motion()
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
        if hand_curls and len(hand_curls) > 0:
            rule_result = self._rule_based_recognize(hand_curls, motion_class)
            if rule_result:
                results.append(rule_result)

        # Return best result
        if results:
            results.sort(key=lambda x: x[1], reverse=True)
            return results[0]

        return ("UNKNOWN", 0.0, "none")

    def _rule_based_recognize(self, hand_curls, motion_class="static"):
        """
        Score every defined sign against the primary hand's curl profile and
        return the best match -- but only if it's not a genuine tie. Ties are
        reported as UNKNOWN rather than silently picking whichever sign
        happens to be defined first (that silent tie-break, always favoring
        numbers since they were listed first, was the original bug).
        """
        if not hand_curls or len(hand_curls) == 0:
            return None

        hand = hand_curls[0]  # Primary hand
        curls = hand['curls']
        thumb_curl = hand['thumb_curl']
        thumb_pos = hand['thumb_pos']

        candidates = []
        for sign_name, rules in self.rule_based_signs.items():
            required_motion = rules.get("motion", "static")
            if required_motion != motion_class:
                continue  # e.g. skip HELLO/THANK-YOU entirely while hand is still

            finger_ranges = rules["finger_curls"]
            if len(finger_ranges) != len(curls):
                continue

            matches = 0
            total = len(finger_ranges) + 1  # + thumb curl
            for curl, (lo, hi) in zip(curls, finger_ranges):
                if lo <= curl <= hi:
                    matches += 1

            thumb_lo, thumb_hi = rules["thumb_curl"]
            if thumb_lo <= thumb_curl <= thumb_hi:
                matches += 1

            score = matches / total

            required_thumb_pos = rules.get("thumb_pos")
            if required_thumb_pos and thumb_pos != required_thumb_pos:
                # Soft penalty, not a hard reject -- thumb_pos is a coarse
                # heuristic and shouldn't veto an otherwise strong match.
                score -= 0.15

            candidates.append((sign_name, max(score, 0.0)))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        best_name, best_score = candidates[0]

        if best_score < 0.8:
            return None

        if len(candidates) > 1 and abs(candidates[1][1] - best_score) < 1e-6:
            return None  # genuine tie -- be honest instead of guessing

        return (best_name, best_score, "rule-based")

    def get_supported_signs(self):
        """Get list of supported signs."""
        signs = set(self.rule_based_signs.keys())
        if self.model and hasattr(self.model, 'classes_'):
            signs.update(self.model.classes_)
        return sorted(list(signs))

    def set_confidence_threshold(self, threshold):
        self.confidence_threshold = threshold
