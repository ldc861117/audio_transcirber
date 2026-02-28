import os
import uuid
import numpy as np
from pydub import AudioSegment
from typing import List, Dict, Any, Optional

import speaker
from speaker import (
    SpeakerSegment, SpeakerResult, get_embedder, 
    parse_diarization_response, speaker_result_to_dict,
    _extract_segment_audio, MIN_CLIP_DURATION, CLIPS_DIR
)
import speaker_v2
from services.speaker_service import SpeakerService

class DiarizationService:
    def diarize(self, audio_path: str, chunk_results: List[str],
                user_id: int, chunk_paths: List[str]) -> Dict[str, Any]:
        """
        核心编排方法。
        """
        # Step 1: 解析所有 chunk 的 segments
        chunk_segments: List[List[SpeakerSegment]] = []
        for i, (res, path) in enumerate(zip(chunk_results, chunk_paths)):
            segs = parse_diarization_response(res)
            # Adjust segments timestamps relative to chunk start
            # Assuming each chunk is processed independently and Gemini returns timestamps starting from 0 for each chunk
            # However, the task says "merge_cross_chunk_speakers" is needed.
            # If we want to merge them, we need to know the offset.
            # Let's see how much duration each chunk has.
            chunk_audio = AudioSegment.from_file(path)
            chunk_duration = len(chunk_audio) / 1000.0
            
            # For merging, we keep segments as is (within each chunk)
            chunk_segments.append(segs)

        # Step 2: 提取每个 chunk 中每个 speaker 的 embedding
        chunk_speaker_results: List[List[SpeakerResult]] = []
        embedder = get_embedder()
        
        for i, (segs, path) in enumerate(zip(chunk_segments, chunk_paths)):
            audio = AudioSegment.from_file(path)
            
            # Group by speaker within chunk
            speaker_groups: Dict[str, List[SpeakerSegment]] = {}
            for seg in segs:
                if seg.speaker_label not in speaker_groups:
                    speaker_groups[seg.speaker_label] = []
                speaker_groups[seg.speaker_label].append(seg)
                
            chunk_results_list: List[SpeakerResult] = []
            for label, group_segs in speaker_groups.items():
                result = SpeakerResult(
                    label=label, 
                    segments=group_segs,
                    total_duration=sum(s.duration for s in group_segs)
                )
                
                # Extract embeddings for each segment > MIN_CLIP_DURATION
                segment_embeddings = []
                for seg in group_segs:
                    if seg.duration >= MIN_CLIP_DURATION:
                        try:
                            # Extract audio segment for embedding
                            waveform = _extract_segment_audio(path, seg.start_time, seg.end_time)
                            # Only use first 15s for embedding as in speaker.py
                            if len(waveform) > speaker.SAMPLE_RATE * 15.0:
                                waveform = waveform[:int(speaker.SAMPLE_RATE * 15.0)]
                            
                            emb = embedder.embed(waveform)
                            segment_embeddings.append(emb)
                        except Exception as e:
                            print(f"Error embedding segment: {e}")
                
                if segment_embeddings:
                    result.embedding = speaker_v2.aggregate_embeddings(segment_embeddings)
                
                # Also handle clip extraction for consistency with speaker.py's SpeakerResult
                # (Optional but good for UI)
                best_segs = sorted([s for s in group_segs if s.duration >= MIN_CLIP_DURATION], 
                                   key=lambda s: s.duration, reverse=True)[:3]
                for seg in best_segs:
                    try:
                        clip_name = f"{uuid.uuid4().hex[:12]}.mp3"
                        clip_dest = CLIPS_DIR / clip_name
                        start_ms = int(seg.start_time * 1000)
                        end_ms = int(seg.end_time * 1000)
                        clip = audio[start_ms:min(end_ms, start_ms + 15000)]
                        clip.export(str(clip_dest), format="mp3")
                        result.clip_paths.append(clip_name)
                        result.clip_durations.append(len(clip) / 1000.0)
                    except Exception as e:
                        print(f"Error extracting clip: {e}")

                chunk_results_list.append(result)
            chunk_speaker_results.append(chunk_results_list)

        # Step 3: 合并跨 chunk 的同一说话人
        merged_speakers = self._merge_speakers(chunk_speaker_results, chunk_paths)

        # Step 4: 声纹库匹配
        for speaker_res in merged_speakers:
            if speaker_res.embedding is not None:
                match = SpeakerService.match_speaker(user_id, speaker_res.embedding)
                if match:
                    speaker_res.matched_profile_id = match["profile_id"]
                    speaker_res.matched_name = match["name"]
                    speaker_res.match_similarity = match["similarity"]

        # Step 5: 组装最终结果
        return {
            "speakers": [speaker_result_to_dict(s) for s in merged_speakers],
            "transcript": self._generate_transcript(merged_speakers)
        }

    def _merge_speakers(self, chunk_results: List[List[SpeakerResult]], chunk_paths: List[str]) -> List[SpeakerResult]:
        """
        Merge speakers across chunks using embedding similarity.
        Modified version of speaker.merge_cross_chunk_speakers that also handles timestamp offsets.
        """
        if not chunk_results:
            return []

        # Calculate offsets
        offsets = [0.0]
        current_offset = 0.0
        for path in chunk_paths[:-1]:
            audio = AudioSegment.from_file(path)
            current_offset += len(audio) / 1000.0
            offsets.append(current_offset)

        # Apply offsets to segments before merging
        for i, chunk_spks in enumerate(chunk_results):
            offset = offsets[i]
            for spk in chunk_spks:
                for seg in spk.segments:
                    seg.start_time += offset
                    seg.end_time += offset

        # Now merge
        merged: List[SpeakerResult] = []
        merged_chunk_ids: List[set] = []
        threshold = 0.85

        for chunk_idx, chunk_speakers in enumerate(chunk_results):
            for speaker_res in chunk_speakers:
                if speaker_res.embedding is None:
                    # If no embedding, we can't safely merge by similarity.
                    # Maybe merge by label if it's consistent? (Unlikely with Gemini)
                    # For now, keep it separate
                    speaker_res.label = f"Speaker_{len(merged)+1}"
                    merged.append(speaker_res)
                    merged_chunk_ids.append({chunk_idx})
                    continue

                best_match_idx = -1
                best_sim = 0.0
                for i, existing in enumerate(merged):
                    if existing.embedding is None:
                        continue
                    if chunk_idx in merged_chunk_ids[i]:
                        continue
                    
                    sim = speaker_v2.cosine_similarity(speaker_res.embedding, existing.embedding)
                    if sim > best_sim and sim >= threshold:
                        best_sim = sim
                        best_match_idx = i

                if best_match_idx >= 0:
                    target = merged[best_match_idx]
                    
                    # Update aggregated embedding BEFORE updating total_duration for correct weighting
                    old_duration = target.total_duration
                    new_duration = speaker_res.total_duration
                    total = old_duration + new_duration
                    
                    if target.embedding is not None and speaker_res.embedding is not None:
                        avg = (target.embedding * old_duration + speaker_res.embedding * new_duration) / total
                        target.embedding = avg / np.linalg.norm(avg)
                    elif speaker_res.embedding is not None:
                        target.embedding = speaker_res.embedding

                    target.segments.extend(speaker_res.segments)
                    target.clip_paths.extend(speaker_res.clip_paths)
                    target.clip_durations.extend(speaker_res.clip_durations)
                    target.total_duration = total
                    merged_chunk_ids[best_match_idx].add(chunk_idx)
                else:
                    merged.append(speaker_res)
                    merged_chunk_ids.append({chunk_idx})

        # Final labeling
        for i, spk in enumerate(merged):
            # If matched with library, we might want to use that name later, 
            # but speaker_result_to_dict handles matched_name.
            spk.label = f"说话人{i + 1}"
            # Sort segments by time
            spk.segments.sort(key=lambda s: s.start_time)
            
        return merged

    def _generate_transcript(self, speakers: List[SpeakerResult]) -> str:
        """Combine all segments into a single transcript string with speaker labels."""
        all_segments = []
        for spk in speakers:
            display_name = spk.matched_name if spk.matched_name else spk.label
            for seg in spk.segments:
                all_segments.append((seg.start_time, display_name, seg.text))
        
        all_segments.sort(key=lambda x: x[0])
        
        lines = []
        for _, name, text in all_segments:
            lines.append(f"[{name}] {text}")
            
        return "\n".join(lines)
