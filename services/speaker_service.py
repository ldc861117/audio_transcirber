import os
import numpy as np
import speaker_db
import speaker_v2
from pathlib import Path
from speaker import CLIPS_DIR

class SpeakerService:
    @staticmethod
    def get_user_profiles(user_id: int):
        profiles = speaker_db.get_profiles_for_user(user_id)
        result = []
        for p in profiles:
            clips = speaker_db.get_clips_for_profile(p["id"])
            result.append({
                "id": p["id"],
                "name": p["name"],
                "created_at": p["created_at"],
                "updated_at": p["updated_at"],
                "clips": clips,
                "clip_count": len(clips)
            })
        return result

    @staticmethod
    def update_name(profile_id: int, user_id: int, name: str):
        profile = speaker_db.get_profile(profile_id)
        if not profile or profile["user_id"] != user_id:
            return False, "说话人不存在"
        if not name.strip():
            return False, "名称不能为空"

        success = speaker_db.update_profile_name(profile_id, name.strip())
        return success, ""

    @staticmethod
    def delete_profile(profile_id: int, user_id: int):
        profile = speaker_db.get_profile(profile_id)
        if not profile or profile["user_id"] != user_id:
            return False, "说话人不存在"
        success = speaker_db.delete_profile(profile_id)
        return success, ""

    @staticmethod
    def merge_profiles(keep_id: int, merge_id: int, user_id: int):
        p1 = speaker_db.get_profile(keep_id)
        p2 = speaker_db.get_profile(merge_id)
        if not p1 or not p2 or p1["user_id"] != user_id or p2["user_id"] != user_id:
            return False, "说话人不存在"
        success = speaker_db.merge_profiles(keep_id, merge_id)
        return success, ""

    @staticmethod
    def match_speaker(user_id: int, embedding: np.ndarray):
        return speaker_v2.match_with_library(user_id, embedding)

    @staticmethod
    def save_task_speakers(user_id: int, task_speakers: list, speaker_updates: list):
        """
        task_speakers: list of speaker results from task (with embeddings)
        speaker_updates: list of {label, name, matched_profile_id} from user
        """
        saved = []

        # Create a map of label -> task_speaker_result
        task_spk_map = {s["label"]: s for s in task_speakers}

        for update in speaker_updates:
            label = update.get("label")
            name = update.get("name", label)
            matched_id = update.get("matched_profile_id")

            task_spk = task_spk_map.get(label)
            if not task_spk:
                continue

            if matched_id:
                # Update existing profile
                speaker_db.update_profile_name(matched_id, name)
                # Add new clips if any
                existing_clips = speaker_db.get_clips_for_profile(matched_id)
                existing_fns = {c["filename"] for c in existing_clips}
                for c in task_spk.get("clips", []):
                    if c["filename"] not in existing_fns:
                        speaker_db.add_clip(matched_id, c["filename"], c["duration"])
                saved.append({"profile_id": matched_id, "name": name, "action": "updated"})
            elif task_spk.get("has_embedding"):
                # Create new profile
                try:
                    from speaker import get_embedder
                    clips = task_spk.get("clips", [])
                    if not clips:
                        continue

                    embedder = get_embedder()
                    clip_path = str(CLIPS_DIR / clips[0]["filename"])
                    embedding = embedder.embed_from_file(clip_path)

                    profile_id = speaker_db.create_profile(user_id, embedding, name)
                    for c in clips:
                        speaker_db.add_clip(profile_id, c["filename"], c["duration"])
                    saved.append({"profile_id": profile_id, "name": name, "action": "created"})
                except Exception as e:
                    print(f"Error saving speaker {label}: {e}")

        return saved
