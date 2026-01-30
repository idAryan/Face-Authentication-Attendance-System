"""Basic spoof prevention: liveness via blink and lighting checks."""
import cv2
import numpy as np
from typing import Tuple, Optional, List

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    BLINK_EAR_THRESHOLD,
    BLINK_FRAMES_REQUIRED,
    MIN_BRIGHTNESS,
    MAX_BRIGHTNESS,
    REQUIRE_BLINK,
)


def eye_aspect_ratio_from_landmarks(eye_dict: dict) -> float:
    """Compute EAR from face_recognition eye dict: 'left_eye' / 'right_eye' list of (x,y)."""
    pts = np.array(eye_dict)
    if len(pts) < 6:
        return 0.0
    # vertical
    v1 = np.linalg.norm(pts[1] - pts[5])
    v2 = np.linalg.norm(pts[2] - pts[4])
    h = np.linalg.norm(pts[0] - pts[3])
    if h < 1e-6:
        return 0.0
    return (v1 + v2) / (2.0 * h)


class SpoofDetector:
    """
    Basic anti-spoofing:
    - Reject too dark / overexposed frames (lighting check).
    - Optional: require blink (liveness) using face_recognition face_landmarks.
    """

    def __init__(
        self,
        ear_threshold: float = BLINK_EAR_THRESHOLD,
        blink_frames_required: int = BLINK_FRAMES_REQUIRED,
        min_brightness: int = MIN_BRIGHTNESS,
        max_brightness: int = MAX_BRIGHTNESS,
        require_blink: bool = REQUIRE_BLINK,
    ):
        self.ear_threshold = ear_threshold
        self.blink_frames_required = blink_frames_required
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.require_blink = require_blink

        self._ear_history: List[float] = []
        self._blink_count = 0

    def check_lighting(self, frame: np.ndarray) -> Tuple[bool, str]:
        """Reject very dark or overexposed frames."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        mean_val = float(np.mean(gray))
        if mean_val < self.min_brightness:
            return False, "Lighting too dark. Please improve lighting."
        if mean_val > self.max_brightness:
            return False, "Frame overexposed. Reduce glare or brightness."
        return True, ""

    def _get_ear_from_landmarks(self, face_landmarks: Optional[dict]) -> Optional[float]:
        """Get combined EAR from face_recognition face_landmarks. Returns None if missing."""
        if not face_landmarks or "left_eye" not in face_landmarks or "right_eye" not in face_landmarks:
            return None
        left_ear = eye_aspect_ratio_from_landmarks(face_landmarks["left_eye"])
        right_ear = eye_aspect_ratio_from_landmarks(face_landmarks["right_eye"])
        return (left_ear + right_ear) / 2.0

    def update_blink_state(
        self, frame: np.ndarray, face_location: Optional[Tuple], face_landmarks: Optional[dict] = None
    ) -> Tuple[bool, str]:
        """
        Update internal blink state. face_landmarks from face_recognition.face_landmarks().
        Returns (liveness_ok, message).
        """
        if not self.require_blink:
            return True, ""

        ear = self._get_ear_from_landmarks(face_landmarks) if face_landmarks else None
        if ear is None:
            return False, "Could not detect eyes. Look at the camera."

        self._ear_history.append(ear)
        n = 30
        if len(self._ear_history) > n:
            self._ear_history = self._ear_history[-n:]

        if len(self._ear_history) >= self.blink_frames_required + 2:
            recent = self._ear_history[-self.blink_frames_required - 2:]
            low = all(r < self.ear_threshold for r in recent[: self.blink_frames_required])
            high_before = recent[0] >= self.ear_threshold
            high_after = recent[-1] >= self.ear_threshold
            if high_before and low and high_after:
                self._blink_count += 1
                self._ear_history.clear()

        if self._blink_count >= 1:
            return True, "Liveness confirmed (blink detected)."
        return False, "Please blink once to confirm you are live."

    def reset_blink_state(self) -> None:
        self._ear_history.clear()
        self._blink_count = 0

    def verify_frame(
        self,
        frame: np.ndarray,
        face_location: Optional[Tuple] = None,
        face_landmarks: Optional[dict] = None,
    ) -> Tuple[bool, str]:
        """Run lighting check and optional blink check. Returns (passed, message)."""
        ok, msg = self.check_lighting(frame)
        if not ok:
            return False, msg
        if self.require_blink:
            return self.update_blink_state(frame, face_location, face_landmarks)
        return True, ""
