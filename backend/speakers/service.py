"""
Speaker diarization and voiceprint module for Audio Transcriber.
Lightweight approach: ONNX Runtime + ECAPA-TDNN for speaker embeddings.
"""

import json
import re
import uuid
import urllib.request
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from pydub import AudioSegment
from app_paths import get_data_dir
from .db import CLIPS_DIR, create_profile, add_clip, get_profile, get_profiles_for_user, update_profile_name, update_profile_embedding, delete_profile, merge_profiles, get_clips_for_profile, find_matching_profiles

# Lazy imports for optional heavy deps
_ort = None
_scipy_signal = None


def _ensure_onnxruntime():
    global _ort
    if _ort is None:
        import onnxruntime as ort
        _ort = ort
    return _ort


def _ensure_scipy():
    global _scipy_signal
    if _scipy_signal is None:
        from scipy import signal as sig
        _scipy_signal = sig
    return _scipy_signal


# ── Constants ──────────────────────────────────────────────────

MODEL_DIR = get_data_dir() / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ECAPA-TDNN ONNX model from wespeaker (small, ~20MB)
MODEL_URL = "https://wespeaker-1256283475.cos.ap-shanghai.myqcloud.com/models/voxceleb/voxceleb_resnet34_LM.onnx"
MODEL_FILENAME = "speaker_encoder.onnx"
MODEL_PATH = MODEL_DIR / MODEL_FILENAME

SAMPLE_RATE = 16000       # Required sample rate for the model
EMBEDDING_DIM = 256       # Output dimension of ResNet34-LM
MIN_CLIP_DURATION = 1.0   # Minimum clip duration in seconds
MAX_CLIPS_PER_SPEAKER = 3 # Max typical clips to store per speaker
MATCH_THRESHOLD = 0.70    # Cosine similarity threshold for speaker match


# ── Data Classes ───────────────────────────────────────────────

@dataclass
class SpeakerSegment:
    """A segment of speech attributed to a specific speaker."""
    speaker_label: str
    start_time: float    # seconds
    end_time: float      # seconds
    text: str = ""

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class SpeakerResult:
    """Complete result for a detected speaker."""
    label: str               # Original label from Gemini (e.g., "Speaker_A")
    segments: list[SpeakerSegment] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None
    clip_paths: list[str] = field(default_factory=list)
    clip_durations: list[float] = field(default_factory=list)
    matched_profile_id: Optional[int] = None
    matched_name: str = ""
    match_similarity: float = 0.0
    total_duration: float = 0.0


# ── Model Download ─────────────────────────────────────────────

def ensure_model() -> Path:
    """Download the ONNX speaker encoder model if not present."""
    if MODEL_PATH.exists():
        return MODEL_PATH

    print("📥 Downloading speaker encoder model (~20MB)...")
    print(f"   URL: {MODEL_URL}")
    try:
        urllib.request.urlretrieve(MODEL_URL, str(MODEL_PATH))
        print(f"✅ Model saved to {MODEL_PATH}")
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        raise RuntimeError(
            f"Could not download speaker encoder model. "
            f"Please manually download from {MODEL_URL} "
            f"and place at {MODEL_PATH}"
        ) from e
    return MODEL_PATH


# ── Audio Preprocessing ───────────────────────────────────────

def _audio_to_wav16k_mono(audio_path: str) -> np.ndarray:
    """Load any audio file and convert to 16kHz mono float32 numpy array."""
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1).set_sample_width(2)

    samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
    samples = samples / 32768.0  # Normalize int16 to [-1, 1]
    return samples


def _extract_segment_audio(audio_path: str, start_time: float, end_time: float) -> np.ndarray:
    """Extract a time segment from an audio file as 16kHz mono float32."""
    audio = AudioSegment.from_file(audio_path)
    start_ms = int(start_time * 1000)
    end_ms = int(end_time * 1000)
    segment = audio[start_ms:end_ms]
    segment = segment.set_frame_rate(SAMPLE_RATE).set_channels(1).set_sample_width(2)

    samples = np.array(segment.get_array_of_samples(), dtype=np.float32)
    samples = samples / 32768.0
    return samples


def _compute_fbank(waveform: np.ndarray, sample_rate: int = SAMPLE_RATE,
                   n_mels: int = 80, n_fft: int = 512, hop_length: int = 160,
                   win_length: int = 400) -> np.ndarray:
    """
    Compute log Mel-filterbank features from a waveform using scipy.
    Returns shape (n_frames, n_mels).
    """
    signal_mod = _ensure_scipy()

    # Pre-emphasis
    emphasized = np.append(waveform[0], waveform[1:] - 0.97 * waveform[:-1])

    # STFT
    _, _, Zxx = signal_mod.stft(
        emphasized, fs=sample_rate, nperseg=win_length,
        noverlap=win_length - hop_length, nfft=n_fft,
        boundary=None, padded=False,
    )
    power_spectrum = np.abs(Zxx) ** 2

    # Mel filterbank
    mel_filters = _mel_filterbank(sample_rate, n_fft, n_mels)
    mel_spec = mel_filters @ power_spectrum

    # Log
    log_mel = np.log(mel_spec + 1e-9)
    return log_mel.T  # (n_frames, n_mels)


def _mel_filterbank(sr: int, n_fft: int, n_mels: int) -> np.ndarray:
    """Create a Mel filterbank matrix."""
    fmin, fmax = 0.0, sr / 2.0
    mel_min = 2595.0 * np.log10(1.0 + fmin / 700.0)
    mel_max = 2595.0 * np.log10(1.0 + fmax / 700.0)
    mels = np.linspace(mel_min, mel_max, n_mels + 2)
    freqs = 700.0 * (10.0 ** (mels / 2595.0) - 1.0)
    bins = np.floor((n_fft + 1) * freqs / sr).astype(int)

    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for i in range(n_mels):
        lo, mid, hi = bins[i], bins[i + 1], bins[i + 2]
        if lo < mid:
            fb[i, lo:mid] = (np.arange(lo, mid) - lo) / (mid - lo)
        if mid < hi:
            fb[i, mid:hi] = (hi - np.arange(mid, hi)) / (hi - mid)
    return fb


# ── Speaker Embedder (ONNX) ───────────────────────────────────

class SpeakerEmbedder:
    """Compute speaker embeddings using an ONNX model."""

    def __init__(self):
        self._session = None

    def _load_model(self):
        if self._session is not None:
            return
        ort = _ensure_onnxruntime()
        model_path = ensure_model()
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 2
        self._session = ort.InferenceSession(
            str(model_path), sess_options=opts,
            providers=["CPUExecutionProvider"],
        )

    def embed(self, waveform: np.ndarray) -> np.ndarray:
        """
        Compute a speaker embedding from a waveform (16kHz, mono, float32).
        Returns a normalized embedding vector.
        """
        self._load_model()

        if len(waveform) < SAMPLE_RATE * MIN_CLIP_DURATION:
            raise ValueError(f"Audio too short ({len(waveform)/SAMPLE_RATE:.1f}s). "
                             f"Need at least {MIN_CLIP_DURATION}s.")

        # Compute features
        feats = _compute_fbank(waveform)  # (T, 80)
        feats = feats.astype(np.float32)

        # Add batch dimension: (1, T, 80)
        feats = np.expand_dims(feats, axis=0)

        # Run inference
        input_name = self._session.get_inputs()[0].name
        output_name = self._session.get_outputs()[0].name
        result = self._session.run([output_name], {input_name: feats})
        embedding = result[0].flatten().astype(np.float32)

        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

    def embed_from_file(self, audio_path: str) -> np.ndarray:
        """Compute embedding from an audio file."""
        waveform = _audio_to_wav16k_mono(audio_path)
        return self.embed(waveform)

    def embed_segment(self, audio_path: str, start_time: float, end_time: float) -> np.ndarray:
        """Compute embedding from a segment of an audio file."""
        waveform = _extract_segment_audio(audio_path, start_time, end_time)
        return self.embed(waveform)


# Global embedder instance (lazy-loaded)
_embedder: Optional[SpeakerEmbedder] = None


def get_embedder() -> SpeakerEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = SpeakerEmbedder()
    return _embedder


# ── Gemini Diarization Parsing ─────────────────────────────────

def parse_diarization_response(response_text: str) -> list[SpeakerSegment]:
    """
    Parse Gemini's structured diarization response.
    Expected format: JSON array of segments with speaker, start, end, text.
    Falls back to regex-based parsing if JSON extraction fails.
    """
    # Try to extract JSON from the response
    segments = _try_parse_json(response_text)
    if segments:
        return segments

    # Fallback: parse text-level speaker labels with approximate timestamps
    return _parse_text_speakers(response_text)


def _try_parse_json(text: str) -> list[SpeakerSegment]:
    """Try to extract and parse JSON segments from the response."""
    # Strategy 1: Markdown code block (most reliable when present)
    md_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if md_match:
        result = _parse_json_data(md_match.group(1).strip())
        if result:
            return result

    # Strategy 2: Find JSON by bracket-counting (handles large nested structures)
    # Try to find a complete JSON object { ... } or array [ ... ]
    for opener, closer in [('{', '}'), ('[', ']')]:
        start_idx = text.find(opener)
        while start_idx != -1:
            depth = 0
            in_string = False
            escape_next = False
            for i in range(start_idx, len(text)):
                ch = text[i]
                if escape_next:
                    escape_next = False
                    continue
                if ch == '\\':
                    escape_next = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == opener:
                    depth += 1
                elif ch == closer:
                    depth -= 1
                    if depth == 0:
                        candidate = text[start_idx:i + 1]
                        result = _parse_json_data(candidate)
                        if result:
                            return result
                        break
            # Try next occurrence of opener
            start_idx = text.find(opener, start_idx + 1)

    return []


def _parse_json_data(raw: str) -> list[SpeakerSegment]:
    """Parse a raw JSON string into a list of SpeakerSegments."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []

    # Handle {segments: [...]} wrapper
    if isinstance(data, dict) and "segments" in data:
        data = data["segments"]

    if not isinstance(data, list):
        return []

    segments = []
    for item in data:
        if not isinstance(item, dict):
            continue
        try:
            seg = SpeakerSegment(
                speaker_label=str(item.get("speaker", item.get("speaker_label", "Unknown"))),
                start_time=float(item.get("start", item.get("start_time", 0))),
                end_time=float(item.get("end", item.get("end_time", 0))),
                text=str(item.get("text", "")),
            )
            if seg.duration > 0:
                segments.append(seg)
        except (KeyError, TypeError, ValueError):
            continue

    return segments if segments else []


def _parse_text_speakers(text: str) -> list[SpeakerSegment]:
    """
    Fallback: Parse speaker labels from plain text transcription.
    Recognizes patterns like 【说话人1】, [Speaker A], etc.
    Creates segments with estimated timestamps based on text length.
    """
    pattern = r'[【\[]([^】\]]+)[】\]]'
    lines = text.split('\n')
    segments = []
    current_time = 0.0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.match(pattern, line)
        if match:
            speaker = match.group(1)
            content = line[match.end():].strip()
            if content:
                # Estimate duration: ~3 chars per second for Chinese
                est_duration = max(2.0, len(content) / 3.0)
                segments.append(SpeakerSegment(
                    speaker_label=speaker,
                    start_time=current_time,
                    end_time=current_time + est_duration,
                    text=content,
                ))
                current_time += est_duration

    return segments


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def merge_cross_chunk_speakers(chunk_results: list[list[SpeakerResult]],
                               threshold: float = 0.85) -> list[SpeakerResult]:
    """
    Merge speakers across chunks using embedding similarity.
    """
    if not chunk_results:
        return []

    # For single chunk, just return the speakers directly
    if len(chunk_results) == 1:
        speakers = chunk_results[0]
        for i, s in enumerate(speakers):
            s.label = f"说话人{i + 1}"
        return speakers

    # Track which chunk each merged speaker came from
    merged: list[SpeakerResult] = []
    merged_chunk_ids: list[set[int]] = []  # tracks which chunks contribute

    for chunk_idx, chunk_speakers in enumerate(chunk_results):
        for speaker in chunk_speakers:
            if speaker.embedding is None:
                speaker.label = f"{speaker.label}_chunk{chunk_idx}"
                merged.append(speaker)
                merged_chunk_ids.append({chunk_idx})
                continue

            # Only match against speakers from DIFFERENT chunks
            best_match_idx = -1
            best_sim = 0.0
            for i, existing in enumerate(merged):
                if existing.embedding is None:
                    continue
                # Skip if speaker came from the same chunk
                if chunk_idx in merged_chunk_ids[i]:
                    continue
                sim = cosine_similarity(speaker.embedding, existing.embedding)
                if sim > best_sim and sim >= threshold:
                    best_sim = sim
                    best_match_idx = i

            if best_match_idx >= 0:
                target = merged[best_match_idx]
                target.segments.extend(speaker.segments)
                target.clip_paths.extend(speaker.clip_paths)
                target.clip_durations.extend(speaker.clip_durations)
                target.total_duration += speaker.total_duration
                merged_chunk_ids[best_match_idx].add(chunk_idx)

                avg = (target.embedding + speaker.embedding) / 2
                target.embedding = avg / np.linalg.norm(avg)

                if len(target.clip_paths) > MAX_CLIPS_PER_SPEAKER:
                    pairs = list(zip(target.clip_paths, target.clip_durations))
                    pairs.sort(key=lambda x: x[1], reverse=True)
                    target.clip_paths = [p[0] for p in pairs[:MAX_CLIPS_PER_SPEAKER]]
                    target.clip_durations = [p[1] for p in pairs[:MAX_CLIPS_PER_SPEAKER]]
            else:
                merged.append(speaker)
                merged_chunk_ids.append({chunk_idx})

    # Re-label
    for i, speaker in enumerate(merged):
        speaker.label = f"说话人{i + 1}"

    return merged


def speaker_result_to_dict(result: SpeakerResult) -> dict:
    """Convert a SpeakerResult to a JSON-serializable dict for the API."""
    return {
        "label": result.label,
        "total_duration": round(result.total_duration, 2),
        "segment_count": len(result.segments),
        "clips": [
            {"filename": fn, "duration": dur}
            for fn, dur in zip(result.clip_paths, result.clip_durations)
        ],
        "has_embedding": result.embedding is not None,
        "matched_profile_id": result.matched_profile_id,
        "matched_name": result.matched_name,
        "match_similarity": round(result.match_similarity, 4),
        "segments": [
            {
                "start": round(s.start_time, 2),
                "end": round(s.end_time, 2),
                "text": s.text,
            }
            for s in result.segments
        ],
    }

class SpeakerService:
    @staticmethod
    def get_user_profiles(user_id: int):
        profiles = get_profiles_for_user(user_id)
        result = []
        for p in profiles:
            clips = get_clips_for_profile(p["id"])
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
        profile = get_profile(profile_id)
        if not profile or profile["user_id"] != user_id:
            return False, "说话人不存在"
        if not name.strip():
            return False, "名称不能为空"

        success = update_profile_name(profile_id, name.strip())
        return success, ""

    @staticmethod
    def delete_profile(profile_id: int, user_id: int):
        profile = get_profile(profile_id)
        if not profile or profile["user_id"] != user_id:
            return False, "说话人不存在"
        success = delete_profile(profile_id)
        return success, ""

    @staticmethod
    def merge_profiles(keep_id: int, merge_id: int, user_id: int):
        p1 = get_profile(keep_id)
        p2 = get_profile(merge_id)
        if not p1 or not p2 or p1["user_id"] != user_id or p2["user_id"] != user_id:
            return False, "说话人不存在"
        success = merge_profiles(keep_id, merge_id)
        return success, ""

    @staticmethod
    def process_speakers(audio_path: str, segments: list[SpeakerSegment],
                         user_id: int) -> list[SpeakerResult]:
        """
        Main pipeline: process diarization segments into speaker results.
        """
        embedder = get_embedder()

        # ── Fix timestamps ──────────────────────────────────────────
        audio = AudioSegment.from_file(audio_path)
        actual_duration = len(audio) / 1000.0  # in seconds

        max_end = max((s.end_time for s in segments), default=0)
        if max_end > 0 and actual_duration > 0:
            coverage_ratio = max_end / actual_duration
            if coverage_ratio < 0.5:
                scale = actual_duration / max_end
                for seg in segments:
                    seg.start_time *= scale
                    seg.end_time *= scale
            elif coverage_ratio > 2.0:
                scale = actual_duration / max_end
                for seg in segments:
                    seg.start_time *= scale
                    seg.end_time *= scale

        total_chars = sum(len(s.text) for s in segments)
        if total_chars > 0 and max_end < 1.0:
            cursor = 0.0
            chars_per_sec = total_chars / actual_duration if actual_duration > 0 else 4.0
            for seg in segments:
                seg_dur = max(1.0, len(seg.text) / chars_per_sec)
                seg.start_time = cursor
                seg.end_time = cursor + seg_dur
                cursor += seg_dur

        # ── Group segments by speaker ─────────────────────────────
        speaker_groups: dict[str, list[SpeakerSegment]] = {}
        for seg in segments:
            if seg.speaker_label not in speaker_groups:
                speaker_groups[seg.speaker_label] = []
            speaker_groups[seg.speaker_label].append(seg)

        results: list[SpeakerResult] = []

        for label, segs in speaker_groups.items():
            result = SpeakerResult(label=label, segments=segs,
                                   total_duration=sum(s.duration for s in segs))

            if result.total_duration < MIN_CLIP_DURATION:
                results.append(result)
                continue

            best_segs = sorted(segs, key=lambda s: s.duration, reverse=True)
            best_segs = [s for s in best_segs if s.duration >= MIN_CLIP_DURATION]
            best_segs = best_segs[:MAX_CLIPS_PER_SPEAKER]

            embeddings = []
            for seg in best_segs:
                try:
                    clip_name = f"{uuid.uuid4().hex[:12]}.mp3"
                    clip_path = CLIPS_DIR / clip_name

                    start_ms = int(seg.start_time * 1000)
                    end_ms = int(seg.end_time * 1000)
                    start_ms = max(0, min(start_ms, len(audio) - 1000))
                    end_ms = max(start_ms + 1000, min(end_ms, len(audio)))

                    clip = audio[start_ms:end_ms]
                    clip_duration = len(clip) / 1000.0

                    if clip_duration > 15.0:
                        clip = clip[:15000]
                        clip_duration = 15.0

                    clip.export(str(clip_path), format="mp3")
                    result.clip_paths.append(clip_name)
                    result.clip_durations.append(round(clip_duration, 2))

                    waveform = _extract_segment_audio(
                        audio_path, start_ms / 1000.0,
                        min(end_ms / 1000.0, start_ms / 1000.0 + 15.0)
                    )
                    emb = embedder.embed(waveform)
                    embeddings.append(emb)

                except Exception as e:
                    print(f"Warning: Failed to process segment for {label}: {e}")
                    continue

            if embeddings:
                avg_emb = np.mean(embeddings, axis=0)
                avg_emb = avg_emb / np.linalg.norm(avg_emb)
                result.embedding = avg_emb

                try:
                    matches = find_matching_profiles(user_id, avg_emb, threshold=MATCH_THRESHOLD)
                    if matches:
                        best = matches[0]
                        result.matched_profile_id = best["profile_id"]
                        result.matched_name = best["name"]
                        result.match_similarity = best["similarity"]
                except Exception as e:
                    print(f"Warning: Speaker matching failed for {label}: {e}")

            results.append(result)

        return results

    @staticmethod
    def save_task_speakers(user_id: int, task_speakers: list, speaker_updates: list):
        """
        task_speakers: list of speaker results from task (with embeddings)
        speaker_updates: list of {label, name, matched_profile_id} from user
        """
        saved = []
        task_spk_map = {s["label"]: s for s in task_speakers}

        for update in speaker_updates:
            label = update.get("label")
            name = update.get("name", label)
            matched_id = update.get("matched_profile_id")

            task_spk = task_spk_map.get(label)
            if not task_spk:
                continue

            if matched_id:
                update_profile_name(matched_id, name)
                existing_clips = get_clips_for_profile(matched_id)
                existing_fns = {c["clip_filename"] for c in existing_clips}
                for c in task_spk.get("clips", []):
                    if c["filename"] not in existing_fns:
                        add_clip(matched_id, c["filename"], c["duration"])
                saved.append({"profile_id": matched_id, "name": name, "action": "updated"})
            elif task_spk.get("has_embedding"):
                try:
                    clips = task_spk.get("clips", [])
                    if not clips:
                        continue

                    embedder = get_embedder()
                    clip_path = str(CLIPS_DIR / clips[0]["filename"])
                    embedding = embedder.embed_from_file(clip_path)

                    profile_id = create_profile(user_id, embedding, name)
                    for c in clips:
                        add_clip(profile_id, c["filename"], c["duration"])
                    saved.append({"profile_id": profile_id, "name": name, "action": "created"})
                except Exception as e:
                    print(f"Error saving speaker {label}: {e}")

        return saved
