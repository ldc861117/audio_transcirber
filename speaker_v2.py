import numpy as np
from typing import Optional, List
import speaker
import speaker_db

# Reuse SpeakerSegment and SpeakerResult from speaker.py
from speaker import SpeakerSegment, SpeakerResult, get_embedder, _extract_segment_audio, SAMPLE_RATE, MIN_CLIP_DURATION

def aggregate_embeddings(embeddings: List[np.ndarray]) -> Optional[np.ndarray]:
    """多段 embedding 平均聚合，比单段更稳定"""
    if not embeddings:
        return None
    
    valid_embeddings = [emb for emb in embeddings if emb is not None and emb.size > 0]
    if not valid_embeddings:
        return None
        
    avg_emb = np.mean(valid_embeddings, axis=0)
    norm = np.linalg.norm(avg_emb)
    if norm > 0:
        avg_emb = avg_emb / norm
    else:
        return None
    return avg_emb

def smart_threshold(embedding: np.ndarray, candidates: List[dict]) -> float:
    """动态阈值：基于候选者间距和方差动态调整"""
    base_threshold = 0.70
    if not candidates:
        return base_threshold
    
    # candidates are sorted by similarity desc from speaker_db.find_matching_profiles
    top_sim = candidates[0]['similarity']
    
    if len(candidates) > 1:
        second_sim = candidates[1]['similarity']
        diff = top_sim - second_sim
        
        # If there's a clear winner, we can be more lenient
        if diff > 0.15:
            return max(0.60, top_sim - 0.05)
        # If it's very close, be stricter
        if diff < 0.03:
            return min(0.85, top_sim + 0.05)
            
    # If only one candidate, but similarity is quite high
    if len(candidates) == 1:
        if top_sim > 0.85:
            return 0.65
            
    return base_threshold

def match_with_library(user_id: int, embedding: np.ndarray,
                       threshold: float = 0.65) -> Optional[dict]:
    """与声纹库匹配，返回 {profile_id, name, similarity} 或 None"""
    if embedding is None or embedding.size == 0:
        return None
        
    # Get candidates with a lower threshold to allow smart_threshold to work
    candidates = speaker_db.find_matching_profiles(user_id, embedding, threshold=0.4)
    if not candidates:
        return None
        
    dynamic_threshold = smart_threshold(embedding, candidates)
    
    best_match = candidates[0]
    if best_match['similarity'] >= dynamic_threshold:
        return best_match
        
    return None

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
