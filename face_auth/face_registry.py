"""Register users by storing face embeddings."""
import json
from pathlib import Path
from typing import List, Optional, Tuple

import face_recognition
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import EMBEDDINGS_DIR, FACE_MATCH_THRESHOLD, NUM_JITTERS, MODEL


class FaceRegistry:
    """Register faces and store 128-D embeddings for later identification."""

    def __init__(self, embeddings_dir: Optional[Path] = None):
        self.embeddings_dir = Path(embeddings_dir or EMBEDDINGS_DIR)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.embeddings_dir / "index.json"

    def _load_index(self) -> dict:
        """Load user_id -> filename mapping."""
        if self._index_path.exists():
            with open(self._index_path, "r") as f:
                return json.load(f)
        return {}

    def _save_index(self, index: dict) -> None:
        with open(self._index_path, "w") as f:
            json.dump(index, f, indent=2)

    def register_from_image(
        self, image: np.ndarray, user_id: str, name: str
    ) -> Tuple[bool, str]:
        """
        Register a user from a single face image.
        Returns (success, message).
        """
        import cv2
        if isinstance(image, (str, Path)):
            rgb = face_recognition.load_image_file(str(image))
        elif len(image.shape) == 2:
            rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            # Assume BGR from OpenCV (e.g. cv2.imdecode)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(
            rgb, model=MODEL, number_of_times_to_upsample=1
        )
        if not face_locations:
            return False, "No face detected in image. Ensure good lighting and a clear view."

        if len(face_locations) > 1:
            return False, "Multiple faces detected. Please use an image with only one face."

        encodings = face_recognition.face_encodings(
            rgb, face_locations, num_jitters=NUM_JITTERS, model="small"
        )
        if not encodings:
            return False, "Could not compute face encoding."

        embedding = encodings[0]
        safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in user_id)
        emb_path = self.embeddings_dir / f"{safe_id}.npy"
        meta_path = self.embeddings_dir / f"{safe_id}.json"

        np.save(emb_path, embedding)
        with open(meta_path, "w") as f:
            json.dump({"user_id": user_id, "name": name}, f, indent=2)

        index = self._load_index()
        index[user_id] = {"file": f"{safe_id}.npy", "name": name}
        self._save_index(index)
        return True, f"Registered successfully: {name} ({user_id})"

    def register_from_file(self, filepath: str, user_id: str, name: str) -> Tuple[bool, str]:
        """Register from image file path."""
        path = Path(filepath)
        if not path.exists():
            return False, f"File not found: {filepath}"
        image = face_recognition.load_image_file(str(path))
        return self.register_from_image(image, user_id, name)

    def get_all_encodings(self) -> Tuple[List[np.ndarray], List[str], List[str]]:
        """Return (encodings, user_ids, names)."""
        index = self._load_index()
        encodings = []
        user_ids = []
        names = []
        for uid, info in index.items():
            emb_file = self.embeddings_dir / info["file"]
            if not emb_file.exists():
                continue
            encodings.append(np.load(emb_file))
            user_ids.append(uid)
            names.append(info.get("name", uid))
        return encodings, user_ids, names

    def delete_user(self, user_id: str) -> bool:
        """Remove a user from the registry."""
        index = self._load_index()
        if user_id not in index:
            return False
        info = index[user_id]
        emb_path = self.embeddings_dir / info["file"]
        if emb_path.exists():
            emb_path.unlink()
        base = emb_path.stem
        meta = self.embeddings_dir / f"{base}.json"
        if meta.exists():
            meta.unlink()
        del index[user_id]
        self._save_index(index)
        return True

    def list_users(self) -> List[dict]:
        """List all registered users."""
        index = self._load_index()
        return [{"user_id": uid, "name": info.get("name", uid)} for uid, info in index.items()]
