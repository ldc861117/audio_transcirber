import os
import traceback
from openai import OpenAI
from .audio_utils import split_audio
from .gemini_provider import transcribe_chunk

try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

from backend.speakers.service import SpeakerService, parse_diarization_response, merge_cross_chunk_speakers, speaker_result_to_dict

# In-memory task store for compatibility/live tracking if needed, 
# though ideally everything goes through DB now.
tasks = {}

class TranscriptionService:
    @staticmethod
    def run_transcription(task_id: str, filepath: str,
                          base_url: str, api_key: str, model: str,
                          max_minutes: int, max_mb: int, provider: str = "openai",
                          user_id: int = 0, enable_diarization: bool = False,
                          overlap_minutes: int = 2):
        """Background worker: split -> transcribe -> (optional) diarize -> merge."""
        
        # Integration with Track B QuotaService would go here
        # try:
        #     from backend.subscriptions.service import QuotaService
        #     QuotaService.check_quota(user_id, filepath)
        # except Exception: pass

        original_filepath = filepath
        
        # Initialize in-memory task for progress tracking if not already present
        if user_id not in tasks:
            tasks[user_id] = {}
        
        # Merge with existing task data (upload route pre-populates filename, created_at, etc.)
        existing = tasks[user_id].get(task_id, {})
        existing.update({
            "status": "splitting",
            "chunk_results": [],
            "completed_chunks": 0,
            "total_chunks": 0,
            "transcript": "",
            "error": "",
            "speakers": [],
        })
        tasks[user_id][task_id] = existing
        task = existing

        try:
            # -- 1. Split ------------------------------------------------
            pref_fmt = "m4a" if provider == "zhipu" else "mp3"
            chunks = split_audio(filepath, max_minutes, max_mb,
                                 overlap_minutes=overlap_minutes, preferred_format=pref_fmt)
            task["total_chunks"] = len(chunks)
            task["status"] = "transcribing"

            # -- 2. Transcribe each chunk --------------------------------
            if provider == "zhipu" and ZhipuAI:
                client = ZhipuAI(api_key=api_key)
            else:
                client = OpenAI(base_url=base_url, api_key=api_key)

            results: list[str] = []
            chunk_paths_kept: list[str] = []  # keep for diarization

            for i, chunk_path in enumerate(chunks):
                task["current_chunk"] = i + 1
                try:
                    text = transcribe_chunk(
                        chunk_path, client, model, provider=provider,
                        enable_diarization=enable_diarization,
                    )
                    results.append(text)
                    task["chunk_results"].append({
                        "index": i + 1,
                        "status": "done",
                        "text": text,
                    })
                except Exception as e:
                    err_msg = str(e)
                    task["chunk_results"].append({
                        "index": i + 1,
                        "status": "error",
                        "text": err_msg,
                    })
                finally:
                    task["completed_chunks"] = i + 1
                    if enable_diarization:
                        chunk_paths_kept.append(chunk_path)
                    else:
                        try:
                            os.unlink(chunk_path)
                        except OSError:
                            pass

            # -- 3. Assemble transcript --------------------------------
            if enable_diarization:
                all_segments_text = []
                for r in results:
                    segments = parse_diarization_response(r)
                    if segments:
                        for seg in segments:
                            all_segments_text.append(
                                f"\u3010{seg.speaker_label}\u3011{seg.text}"
                            )
                    else:
                        # Fallback: if response looks like JSON, don't store raw JSON
                        stripped = r.strip()
                        if (stripped.startswith('{') or stripped.startswith('[')) and '"text"' in stripped:
                            # Extract text values via regex as last resort
                            import re as _re
                            text_values = _re.findall(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', r)
                            if text_values:
                                for tv in text_values:
                                    tv_clean = tv.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    all_segments_text.append(tv_clean)
                                print(f"⚠️ [Backend] Recovered {len(text_values)} text segments from raw JSON response")
                            else:
                                all_segments_text.append(r)
                        else:
                            all_segments_text.append(r)
                task["transcript"] = "\n\n".join(all_segments_text)
            else:
                # LLM-based stitching for overlapping chunks
                if len(results) > 1 and overlap_minutes > 0:
                    task["status"] = "stitching"
                    try:
                        from services.stitch_service import stitch_transcripts
                        task["transcript"] = stitch_transcripts(results, client, model)
                    except Exception as stitch_err:
                        print(f"⚠️ LLM stitching failed, falling back to join: {stitch_err}")
                        task["transcript"] = "\n\n".join(results)
                else:
                    task["transcript"] = "\n\n".join(results)

            # -- 4. Speaker diarization (optional) -----------------------
            if enable_diarization:
                task["status"] = "diarizing"
                try:
                    chunk_speaker_results = []
                    for idx, (chunk_path, text) in enumerate(zip(chunk_paths_kept, results)):
                        segments = parse_diarization_response(text)
                        if segments:
                            speaker_results = SpeakerService.process_speakers(
                                chunk_path, segments, user_id
                            )
                            chunk_speaker_results.append(speaker_results)

                    if chunk_speaker_results:
                        merged_speakers = merge_cross_chunk_speakers(chunk_speaker_results)
                        task["speakers"] = [
                            speaker_result_to_dict(s) for s in merged_speakers
                        ]
                        # Auto-replace matched speaker labels in transcript
                        transcript = task.get("transcript", "")
                        for sp_dict in task["speakers"]:
                            if sp_dict.get("matched_name"):
                                old_tag = f"\u3010{sp_dict['label']}\u3011"
                                new_tag = f"\u3010{sp_dict['matched_name']}\u3011"
                                transcript = transcript.replace(old_tag, new_tag)
                        task["transcript"] = transcript
                    else:
                        task["speakers"] = []

                except Exception as e:
                    print(f"\u26a0\ufe0f Diarization failed: {e}")
                    task["speakers"] = []
                    task["diarization_error"] = str(e)
                finally:
                    for cp in chunk_paths_kept:
                        try:
                            os.unlink(cp)
                        except OSError:
                            pass

            # -- 5. Determine final status --------------------------------
            error_chunks = [c for c in task["chunk_results"] if c["status"] == "error"]
            all_failed = len(error_chunks) == len(task["chunk_results"]) and len(task["chunk_results"]) > 0

            if all_failed:
                task["status"] = "error"
                task["transcript"] = ""
                task["error"] = f"全部 {len(error_chunks)} 个分段转写失败: {error_chunks[0]['text']}"
            else:
                task["status"] = "done"

            # ── Persist final result to DB (via TaskService) ──
            # from services.task_service import TaskService
            # TaskService.update_task(...)

        except Exception:
            task["status"] = "error"
            task["error"] = traceback.format_exc()
        finally:
            try:
                os.unlink(original_filepath)
            except OSError:
                pass
            
            # Integration with Track B QuotaService to deduct quota
            # try:
            #     from backend.subscriptions.service import QuotaService
            #     QuotaService.deduct_quota(user_id, task_id)
            # except Exception: pass
