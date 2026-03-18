import os
import time
import logging
import traceback
from datetime import datetime, timezone
from openai import OpenAI

logger = logging.getLogger(__name__)


def _log_event(task: dict, stage: str, message: str, **extra):
    """Append a structured event to the task's pipeline_log."""
    now = datetime.now(timezone.utc)
    entry = {
        "stage": stage,
        "message": message,
        "timestamp": now.isoformat(),
    }
    # Calculate duration since the stage started (if _stage_start is set)
    stage_start = task.get("_stage_start")
    if stage_start:
        entry["duration_ms"] = round((time.monotonic() - stage_start) * 1000)
    entry.update(extra)
    task.setdefault("pipeline_log", []).append(entry)
    logger.info(f"[{task.get('id', '?')}] [{stage}] {message}")


def _start_stage(task: dict, stage: str, message: str):
    """Mark stage start and log it."""
    task["status"] = stage
    task["_stage_start"] = time.monotonic()
    _log_event(task, stage, message)
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
        started_at = datetime.now(timezone.utc).isoformat()
        existing.update({
            "id": task_id,
            "status": "splitting",
            "chunk_results": [],
            "completed_chunks": 0,
            "total_chunks": 0,
            "transcript": "",
            "error": "",
            "speakers": [],
            "pipeline_log": [],
            "started_at": started_at,
            "completed_at": None,
            "elapsed_seconds": 0,
        })
        tasks[user_id][task_id] = existing
        task = existing
        pipeline_t0 = time.monotonic()

        try:
            # -- 1. Split ------------------------------------------------
            _start_stage(task, "splitting", "开始分割音频")
            pref_fmt = "m4a" if provider == "zhipu" else "mp3"
            chunks = split_audio(filepath, max_minutes, max_mb,
                                 overlap_minutes=overlap_minutes, preferred_format=pref_fmt)
            task["total_chunks"] = len(chunks)
            _log_event(task, "splitting", f"分割完成，共 {len(chunks)} 段", chunk_count=len(chunks))

            # -- 2. Transcribe each chunk --------------------------------
            if provider == "zhipu" and ZhipuAI:
                client = ZhipuAI(api_key=api_key)
            else:
                client = OpenAI(base_url=base_url, api_key=api_key)

            # -- 2a. Speaker Census pre-pass (diarization only) ----------
            census_context = ""
            if enable_diarization:
                _start_stage(task, "censusing", "开始说话人普查")
                try:
                    from .speaker_census import run_speaker_census, build_census_context
                    census_result = run_speaker_census(
                        filepath, client, model, provider=provider
                    )
                    census_context = build_census_context(census_result)
                    if census_result:
                        task["census"] = census_result
                        _log_event(task, "censusing", f"普查完成: {census_result.get('speaker_count', '?')} 位说话人")
                    else:
                        _log_event(task, "censusing", "普查无结果，继续处理")
                except Exception as e:
                    _log_event(task, "censusing", f"普查失败: {e}", error=True)

            results: list[str] = []
            chunk_paths_kept: list[str] = []  # keep for diarization

            _start_stage(task, "transcribing", f"开始转写 {len(chunks)} 段音频")
            for i, chunk_path in enumerate(chunks):
                task["current_chunk"] = i + 1
                chunk_t0 = time.monotonic()
                try:
                    text = transcribe_chunk(
                        chunk_path, client, model, provider=provider,
                        enable_diarization=enable_diarization,
                        census_context=census_context,
                    )
                    results.append(text)
                    chunk_ms = round((time.monotonic() - chunk_t0) * 1000)
                    char_count = len(text)
                    task["chunk_results"].append({
                        "index": i + 1,
                        "status": "done",
                        "text": text,
                    })
                    _log_event(task, "transcribing",
                               f"分段 {i+1}/{len(chunks)} 完成 ({chunk_ms/1000:.1f}s, {char_count}字)",
                               chunk_index=i+1, duration_ms=chunk_ms, char_count=char_count)
                except Exception as e:
                    err_msg = str(e)
                    chunk_ms = round((time.monotonic() - chunk_t0) * 1000)
                    task["chunk_results"].append({
                        "index": i + 1,
                        "status": "error",
                        "text": err_msg,
                    })
                    _log_event(task, "transcribing",
                               f"分段 {i+1}/{len(chunks)} 失败: {err_msg[:80]}",
                               chunk_index=i+1, duration_ms=chunk_ms, error=True)
                finally:
                    task["completed_chunks"] = i + 1
                    # Update elapsed time for frontend
                    task["elapsed_seconds"] = round(time.monotonic() - pipeline_t0, 1)
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
                        # Fallback: strip markdown fences and try to extract text
                        import re as _re
                        stripped = r.strip()
                        # Strip markdown code fences (```json ... ``` or ``` ... ```)
                        stripped = _re.sub(r'^```(?:json)?\s*', '', stripped)
                        stripped = _re.sub(r'\s*```\s*$', '', stripped)
                        stripped = stripped.strip()
                        
                        if (stripped.startswith('{') or stripped.startswith('[')) and '"text"' in stripped:
                            # Try parsing stripped JSON first
                            try:
                                import json
                                data = json.loads(stripped)
                                if isinstance(data, dict) and 'segments' in data:
                                    data = data['segments']
                                if isinstance(data, list):
                                    for item in data:
                                        if isinstance(item, dict) and 'text' in item:
                                            speaker = item.get('speaker', '未知')
                                            all_segments_text.append(f"\u3010{speaker}\u3011{item['text']}")
                                    _log_event(task, "transcribing", f"从 markdown 围栏中恢复 {len(data)} 段")
                                    continue
                            except (json.JSONDecodeError, ValueError):
                                pass
                            
                            # Last resort: regex extract
                            text_values = _re.findall(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', stripped)
                            speaker_values = _re.findall(r'"speaker"\s*:\s*"((?:[^"\\]|\\.)*)"', stripped)
                            if text_values:
                                for idx_tv, tv in enumerate(text_values):
                                    tv_clean = tv.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    sp = speaker_values[idx_tv] if idx_tv < len(speaker_values) else '未知'
                                    all_segments_text.append(f"\u3010{sp}\u3011{tv_clean}")
                                _log_event(task, "transcribing", f"通过正则恢复 {len(text_values)} 段文本")
                            else:
                                all_segments_text.append(r)
                        else:
                            all_segments_text.append(r)
                task["transcript"] = "\n\n".join(all_segments_text)
            else:
                # LLM-based stitching for overlapping chunks
                if len(results) > 1 and overlap_minutes > 0:
                    _start_stage(task, "stitching", f"开始拼接 {len(results)} 段重叠文本")
                    try:
                        from services.stitch_service import stitch_transcripts
                        task["transcript"] = stitch_transcripts(results, client, model)
                        _log_event(task, "stitching", "拼接完成")
                    except Exception as stitch_err:
                        _log_event(task, "stitching", f"拼接失败，回退拼接: {stitch_err}", error=True)
                        task["transcript"] = "\n\n".join(results)
                else:
                    task["transcript"] = "\n\n".join(results)

            # -- 4. Speaker diarization (optional) -----------------------
            if enable_diarization:
                _start_stage(task, "diarizing", "开始说话人分离")
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
                        # Build display name for each speaker, collecting
                        # ALL original segment labels (before re-numbering).
                        transcript = task.get("transcript", "")
                        display_names: dict[str, str] = {}  # new_label → display_name
                        original_labels_map: dict[str, set[str]] = {}  # new_label → {orig_labels}

                        for sp_dict in task["speakers"]:
                            new_label = sp_dict["label"]
                            display = sp_dict.get("matched_name") or new_label
                            display_names[new_label] = display
                            # Gather original labels from segments
                            orig_labels = set()
                            for seg in sp_dict.get("segments", []):
                                # The segment text was produced with Gemini's original label
                                pass
                            original_labels_map[new_label] = orig_labels

                        # Collect original labels from merged SpeakerResult objects
                        for sp_result, sp_dict in zip(merged_speakers, task["speakers"]):
                            orig_labels = {seg.speaker_label for seg in sp_result.segments}
                            original_labels_map[sp_dict["label"]] = orig_labels

                        # Check for duplicate display names — if two speakers
                        # would get the same name, keep the generic labels.
                        used_display_names: dict[str, list[str]] = {}
                        for new_label, display in display_names.items():
                            used_display_names.setdefault(display, []).append(new_label)

                        for new_label, display in display_names.items():
                            # Skip if this name is shared by multiple speakers
                            if len(used_display_names.get(display, [])) > 1:
                                _log_event(task, "diarizing", f"显示名 '{display}' 被多个说话人使用，保留通用标签")
                                continue
                            # Replace all original labels with the display name
                            for orig_label in original_labels_map.get(new_label, set()):
                                old_tag = f"\u3010{orig_label}\u3011"
                                new_tag = f"\u3010{display}\u3011"
                                if old_tag != new_tag:
                                    transcript = transcript.replace(old_tag, new_tag)
                            # Also replace the renumbered label itself
                            old_tag = f"\u3010{new_label}\u3011"
                            new_tag = f"\u3010{display}\u3011"
                            if old_tag != new_tag:
                                transcript = transcript.replace(old_tag, new_tag)
                            # Update the sp_dict label to reflect display name
                            sp_dict["label"] = display

                        task["transcript"] = transcript
                    else:
                        task["speakers"] = []

                except Exception as e:
                    logger.warning(f"Diarization failed: {e}")
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

            elapsed = round(time.monotonic() - pipeline_t0, 1)
            task["elapsed_seconds"] = elapsed
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            total_chars = len(task.get("transcript", ""))

            if all_failed:
                task["status"] = "error"
                task["transcript"] = ""
                task["error"] = f"全部 {len(error_chunks)} 个分段转写失败: {error_chunks[0]['text']}"
                _log_event(task, "error", f"转写失败 ({elapsed}s)")
            else:
                task["status"] = "done"
                _log_event(task, "done",
                           f"转写完成: {len(task['chunk_results'])}段, {total_chars}字, 耗时{elapsed}s",
                           total_chars=total_chars)

            # ── Persist final result to DB (via TaskService) ──
            try:
                import json as _json
                from services.task_service import TaskService
                TaskService.update_task(
                    task_id,
                    status=task["status"],
                    transcript=task.get("transcript", ""),
                    speakers=task.get("speakers", []),
                    error=task.get("error", ""),
                    chunk_count=len(task.get("chunk_results", [])),
                    duration_seconds=task.get("duration_seconds", 0.0),
                )
            except Exception as e:
                _log_event(task, "persist", f"保存至数据库失败: {e}", error=True)

        except Exception:
            task["status"] = "error"
            task["error"] = traceback.format_exc()
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
            task["elapsed_seconds"] = round(time.monotonic() - pipeline_t0, 1)
            _log_event(task, "error", f"管道异常: {task['error'][:100]}")
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
