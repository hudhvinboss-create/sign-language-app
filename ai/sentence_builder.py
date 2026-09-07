"""
Sentence construction from recognized signs.
Handles sign sequences, grammar, and context.
"""
import re
from collections import deque

class SentenceBuilder:
    def __init__(self, language="ASL", buffer_size=30):
        self.language = language
        self.buffer_size = buffer_size
        self.sign_buffer = deque(maxlen=buffer_size)
        self.current_sentence = []
        self.last_sign = None
        self.sign_hold_frames = 0
        self.min_hold_frames = 5  # Minimum frames to confirm a sign
        self.silence_threshold = 15  # Frames of silence to end sentence
        self.silence_count = 0

        # ASL grammar rules (simplified)
        self.grammar_rules = {
            "word_order": ["subject", "object", "verb"],  # ASL typically uses SOV or SVO
            "question_words": ["WHO", "WHAT", "WHERE", "WHEN", "WHY", "HOW"],
            "negation": ["NOT", "NO", "NEVER"],
        }

    def add_sign(self, sign, confidence):
        """
        Add a recognized sign to the buffer.
        Returns: (is_confirmed, confirmed_sign, sentence_so_far)
        """
        if sign == "UNKNOWN" or confidence < 0.5:
            self.silence_count += 1
            if self.silence_count >= self.silence_threshold:
                # End of signing phrase
                if self.last_sign:
                    self._commit_sign(self.last_sign)
                    self.last_sign = None
                    self.sign_hold_frames = 0
            return (False, None, self.get_sentence())

        self.silence_count = 0

        if sign == self.last_sign:
            self.sign_hold_frames += 1
            if self.sign_hold_frames >= self.min_hold_frames:
                # Sign is held long enough, commit it
                if sign not in self.current_sentence or sign in ["YES", "NO"]:
                    self._commit_sign(sign)
                    self.last_sign = None
                    self.sign_hold_frames = 0
                    return (True, sign, self.get_sentence())
        else:
            # New sign detected
            if self.last_sign and self.sign_hold_frames >= self.min_hold_frames:
                self._commit_sign(self.last_sign)
            self.last_sign = sign
            self.sign_hold_frames = 1

        return (False, None, self.get_sentence())

    def _commit_sign(self, sign):
        """Add sign to current sentence."""
        # Avoid duplicates unless it's a repeated emphasis
        if not self.current_sentence or self.current_sentence[-1] != sign:
            self.current_sentence.append(sign)
            self.sign_buffer.append(sign)

    def get_sentence(self):
        """Get the current constructed sentence."""
        if not self.current_sentence:
            return ""

        # Basic sentence construction
        sentence = " ".join(self.current_sentence)

        # Simple formatting
        sentence = sentence.replace("-", " ")
        sentence = sentence.title()

        return sentence

    def get_formatted_sentence(self):
        """Get sentence with basic grammar applied."""
        sentence = self.get_sentence()

        # Add punctuation for questions
        if any(word in sentence.upper() for word in self.grammar_rules["question_words"]):
            if not sentence.endswith("?"):
                sentence += "?"

        return sentence

    def reset(self):
        """Reset the sentence builder."""
        self.sign_buffer.clear()
        self.current_sentence = []
        self.last_sign = None
        self.sign_hold_frames = 0
        self.silence_count = 0

    def get_recent_signs(self, count=5):
        """Get recent signs from buffer."""
        return list(self.sign_buffer)[-count:]

    def set_language(self, language):
        self.language = language
        self.reset()
