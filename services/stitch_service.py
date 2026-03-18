"""
Stitch Service — LLM-based overlap transcript stitching.

When audio is split with overlapping segments, the same ~2 minutes of audio
appear in both consecutive chunks.  Because LLM transcription is non-deterministic,
the overlapping region may produce *slightly different* wording in each chunk.
Pure text-matching (longest common substring, diff, etc.) fails in this case.

This service sends each pair of adjacent transcripts to the LLM and asks it
to identify the semantically duplicated overlap region and merge them into a
single, seamless transcript.
"""

from __future__ import annotations

_STITCH_SYSTEM_PROMPT = (
    "你是一位专业的文字编辑。你的任务是将两段有重叠的转写文本拼接成一段连贯的完整文本。"
)

_STITCH_USER_PROMPT_TEMPLATE = (
    "以下是一段长音频被分成两个有重叠的片段后分别转写的结果。"
    "两段文本的末尾和开头有大约 2 分钟的重叠内容——"
    "即 text_a 的末尾部分和 text_b 的开头部分描述的是同一段音频，"
    "但由于分别转写，措辞可能略有不同（同义词替换、标点差异、语气词有无等）。\n\n"
    "请你：\n"
    "1. 识别出 text_a 末尾和 text_b 开头的重叠区域；\n"
    "2. 保留 text_a 中重叠区域的版本（因为它有更多前文上下文，通常更准确）；\n"
    "3. 去除 text_b 中重复的开头部分；\n"
    "4. 将 text_a 和去重后的 text_b 自然拼接，输出完整文本。\n\n"
    "**关键规则**：\n"
    "- 不要对内容做任何修改、润色、总结或删减，仅做拼接去重；\n"
    "- 如果无法确定重叠区域，就直接将两段文本拼接返回；\n"
    "- 仅输出拼接后的正文，不要包含任何解释性文字。\n\n"
    "---\n\n"
    "**text_a**:\n{text_a}\n\n"
    "---\n\n"
    "**text_b**:\n{text_b}"
)


def stitch_pair(text_a: str, text_b: str, client, model: str) -> str:
    """Use LLM to merge two overlapping transcripts into one seamless text."""
    prompt = _STITCH_USER_PROMPT_TEMPLATE.format(text_a=text_a, text_b=text_b)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _STITCH_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=16384,
    )
    return response.choices[0].message.content.strip()


def stitch_transcripts(transcripts: list[str], client, model: str) -> str:
    """
    Sequentially stitch a list of overlapping transcripts.

    For N transcripts, performs N-1 LLM calls, each merging the accumulated
    result with the next transcript.
    """
    if not transcripts:
        return ""
    if len(transcripts) == 1:
        return transcripts[0]

    # Filter out empty/error transcripts
    valid = [t for t in transcripts if t and t.strip()]
    if not valid:
        return ""
    if len(valid) == 1:
        return valid[0]

    accumulated = valid[0]
    for i in range(1, len(valid)):
        print(f"🔗 [Stitch] Merging segment {i}/{len(valid)-1} ...")
        accumulated = stitch_pair(accumulated, valid[i], client, model)

    return accumulated
