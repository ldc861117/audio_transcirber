"""
Speaker Census — dedicated LLM pre-pass for speaker identification.

Before transcription, we send a short audio sample (~2 min) to the LLM
with a focused prompt that ONLY asks about speaker identification.
This gives us a "speaker roster" that dramatically improves the accuracy
of the main transcription pass.
"""

import base64
import json
import os
import re
import tempfile
from pathlib import Path
from pydub import AudioSegment


# ── Census prompt — no transcription, ONLY speaker analysis ──────────

_CENSUS_SYSTEM = (
    "你是一位拥有绝对音感的专业声学分析师。"
    "你的唯一任务是分辨音频中有几个不同的人在说话。"
    "不要转写任何内容，不要输出文字稿。"
)

_CENSUS_USER = (
    "请仔细聆听这段音频，分析其中有多少个**不同的说话人**。\n\n"
    "**分析要点**：\n"
    "1. 注意音色差异（男/女、高/低、嗓音特征）\n"
    "2. 注意语速和说话风格的差异\n"
    "3. 注意对话中的一问一答模式（提问者 vs 回答者）\n"
    "4. 即使两个人音色相近，对话逻辑也能帮助你区分\n\n"
    "**仅输出以下纯净 JSON，不要包含代码块标记或任何其他文字**：\n"
    '{"speaker_count": N, "speakers": [\n'
    '  {"id": "说话人1", "gender": "男/女/未知", "characteristics": "简短描述声音特征和角色"},\n'
    '  {"id": "说话人2", "gender": "男/女/未知", "characteristics": "简短描述声音特征和角色"}\n'
    "]}\n\n"
    "**注意**：\n"
    "- 如果只有1个人在说（独白/演讲），speaker_count 为 1\n"
    "- 如果有明显的对话（一问一答），speaker_count 至少为 2\n"
    "- 请务必准确！宁可多检测，也不要漏检。"
)

# How many seconds of audio to sample for census (default: 120s = 2min)
CENSUS_SAMPLE_SECONDS = 120


def _extract_census_sample(audio_path: str) -> str | None:
    """
    Extract a short sample from the audio for census analysis.
    Returns path to temporary file, or None on failure.
    """
    try:
        audio = AudioSegment.from_file(audio_path)
        duration_ms = len(audio)
        sample_ms = min(CENSUS_SAMPLE_SECONDS * 1000, duration_ms)

        # Take from the beginning — usually has the most speaker variety
        sample = audio[:sample_ms]

        # Export as mp3 to keep it small
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        sample.export(tmp.name, format="mp3")
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"⚠️ [Census] Failed to extract sample: {e}")
        return None


def _parse_census_response(raw: str) -> dict | None:
    """Parse the LLM census response into a structured dict."""
    try:
        # Strip markdown code fences if present
        cleaned = raw.strip()
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```\s*$', '', cleaned)
        cleaned = cleaned.strip()

        data = json.loads(cleaned)

        if isinstance(data, dict) and "speaker_count" in data:
            return data
        return None
    except (json.JSONDecodeError, ValueError) as e:
        print(f"⚠️ [Census] Failed to parse response: {e}")
        print(f"   Raw response: {raw[:200]}")
        return None


def run_speaker_census(audio_path: str, client, model: str,
                       provider: str = "openai") -> dict | None:
    """
    Run a dedicated LLM call to identify speakers in the audio.

    Returns:
        dict with keys: speaker_count (int), speakers (list of dicts)
        or None on failure (graceful fallback)
    """
    # Skip census for providers that don't support multimodal chat
    if provider in ("zhipu", "modelscope"):
        print("ℹ️ [Census] Skipping — provider doesn't support multimodal chat")
        return None

    print("🔍 [Census] Starting speaker census pre-pass...")

    # Extract a short sample
    sample_path = _extract_census_sample(audio_path)
    if not sample_path:
        return None

    try:
        # Encode audio
        mime = "audio/mpeg"
        with open(sample_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        # Call LLM with census-only prompt
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _CENSUS_SYSTEM},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _CENSUS_USER},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }
            ],
            max_tokens=1024,  # Census response is short
        )

        raw = response.choices[0].message.content.strip()
        print(f"📋 [Census] Raw response: {raw[:300]}")

        result = _parse_census_response(raw)
        if result:
            count = result.get("speaker_count", 0)
            speakers = result.get("speakers", [])
            print(f"✅ [Census] Detected {count} speaker(s):")
            for sp in speakers:
                print(f"   • {sp.get('id', '?')}: {sp.get('gender', '?')} — {sp.get('characteristics', '?')}")
            return result
        else:
            print("⚠️ [Census] Could not parse response, falling back")
            return None

    except Exception as e:
        print(f"⚠️ [Census] LLM call failed: {e}")
        return None
    finally:
        # Clean up temp sample
        try:
            os.unlink(sample_path)
        except OSError:
            pass


def build_census_context(census: dict | None) -> str:
    """
    Convert census results into a context string for injection
    into the transcription prompt.
    Returns empty string if census is None.
    """
    if not census:
        return ""

    count = census.get("speaker_count", 0)
    speakers = census.get("speakers", [])

    if count <= 0:
        return ""

    lines = [
        f"\n\n**🔍 说话人预分析结果（已通过独立声学分析确认）**：\n"
        f"这段音频中有 **{count}** 位不同的说话人：\n"
    ]
    for sp in speakers:
        sid = sp.get("id", "未知")
        gender = sp.get("gender", "未知")
        chars = sp.get("characteristics", "")
        lines.append(f"- **{sid}**（{gender}）：{chars}")

    lines.append(
        f"\n请严格按照以上 {count} 位说话人进行标注，"
        "不要将不同的人合并为同一个说话人。"
        "如果你在转写过程中发现实际说话人数量与预分析不同，以你的实际判断为准，"
        "但请优先信任预分析结果。"
    )

    return "\n".join(lines)
