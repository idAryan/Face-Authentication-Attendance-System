"""Face Authentication Attendance System - core modules."""
from .face_registry import FaceRegistry
from .face_identifier import FaceIdentifier
from .spoof_detection import SpoofDetector
from .attendance import AttendanceDB

__all__ = ["FaceRegistry", "FaceIdentifier", "SpoofDetector", "AttendanceDB"]
