import os
import base64
from openai import OpenAI

try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

# ── Built-in provider configs (API keys from env, rest hardcoded) ────
BUILTIN_PROVIDERS = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-3-flash-preview",
        "api_key_env": "GEMINI_API_KEY",
    },
}

def _get_builtin_key(provider_name: str) -> str:
    """Return the API key for a built-in provider, or empty string."""
    info = BUILTIN_PROVIDERS.get(provider_name, {})
    env_var = info.get("api_key_env", "")
    return os.environ.get(env_var, "") if env_var else ""

# ── Prompt constants ───────────────────────────────────────────
_SYSTEM_PROMPT = (
    "\u4f60\u662f\u4e00\u4f4d\u62e5\u6709 20 \u5e74\u7ecf\u9a8c\u7684\u4e13\u4e1a\u4f1a\u8bae\u901f\u8bb0\u5458\u548c\u7eaa\u8981\u4e13\u5bb6\u3002"
    "\u4f60\u7684\u4efb\u52a1\u662f\u5c06\u97f3\u9891\u5185\u5bb9\u8f6c\u5316\u4e3a\u201c\u667a\u80fd\u9010\u5b57\u7a3f\u201d\uff08Intelligent Verbatim\uff09\u3002"
    "\u6838\u5fc3\u539f\u5219\uff1a\u4fdd\u6301\u5185\u5bb9\u7684\u5b8c\u6574\u6027\u548c\u51c6\u786e\u6027\uff0c\u540c\u65f6\u63d0\u5347\u9605\u8bfb\u4f53\u9a8c\u3002"
    "\u91cd\u8981\uff1a\u8bf7\u59cb\u7ec8\u4f7f\u7528\u7b80\u4f53\u4e2d\u6587\uff08Simplified Chinese\uff09\u8f93\u51fa\uff0c\u4e0d\u8981\u4f7f\u7528\u7e41\u4f53\u4e2d\u6587\u3002"
)

_USER_PROMPT_STANDARD = (
    "\u8bf7\u5bf9\u4ee5\u4e0b\u97f3\u9891\u8fdb\u884c\u4e13\u4e1a\u8f6c\u5199\u3002\u9075\u5faa\u4ee5\u4e0b\u4e1a\u754c\u6807\u51c6\u89c4\u8303\uff1a\n\n"
    "1. **\u667a\u80fd\u51c0\u5316**\uff1a\n"
    "   - \u5254\u9664\u53e3\u8bed\u5e9f\u8bdd\uff08\u5982\u201c\u90a3\u4e2a\u201d\u3001\u201c\u5462\u201d\u3001\u201c\u55ef\u201d\u3001\u201c\u5c31\u662f\u8bf4\u201d\u7b49\uff09\uff0c\u9664\u975e\u8868\u8fbe\u8fdf\u7591\u6216\u5f3a\u8c03\uff1b\n"
    "   - \u4fee\u6b63\u660e\u663e\u7684\u53e3\u8bef\u548c\u91cd\u590d\uff08\u5982\u201c\u6211...\u6211\u4eec\u8ba4\u4e3a\u201d -> \u201c\u6211\u4eec\u8ba4\u4e3a\u201d\uff09\uff1b\n"
    "   - \u4fdd\u6301\u539f\u672c\u7684\u8bed\u5e8f\u548c\u903b\u8f91\uff0c\u4e0d\u8981\u968f\u610f\u6539\u5199\u5185\u5bb9\u3002\n\n"
    "2. **\u683c\u5f0f\u89c4\u8303**\uff1a\n"
    "   - **\u8bf4\u8bdd\u4eba\u6807\u8bb0**\uff1a\u6839\u636e\u58f0\u7eb9\u548c\u4e0a\u4e0b\u6587\u533a\u5206\u8bf4\u8bdd\u4eba\uff0c\u4f7f\u7528\u3010\u8bf4\u8bdd\u4eba1\u3011\u3001\u3010\u8bf4\u8bdd\u4eba2\u3011\u6216\u5177\u4f53\u79f0\u8c13\uff08\u5982\u3010\u4e3b\u6301\u4eba\u3011\u3001\u3010\u7ecf\u7406\u3011\uff09\u6807\u8bb0\uff1b\n"
    "   - **\u6bb5\u843d\u5206\u660e**\uff1a\u4e0d\u540c\u8bf4\u8bdd\u4eba\u5fc5\u987b\u6362\u884c\u3002\u957f\u6bb5\u72ec\u767d\u8bf7\u6839\u636e\u903b\u8f91\u8bed\u4e49\u5408\u7406\u5206\u6bb5\uff1b\n"
    "   - **\u6807\u70b9\u4e13\u4e1a**\uff1a\u4f7f\u7528\u89c4\u8303\u7684\u4e2d\u6587\u5168\u89d2\u6807\u70b9\u3002\u8bed\u6c14\u5f3a\u70c8\u7684\u7528\u611f\u53f9\u53f7\uff0c\u7591\u95ee\u7528\u95ee\u53f7\uff0c\u5e76\u5217\u7528\u987f\u53f7\u3002\n\n"
    "3. **\u5173\u952e\u5185\u5bb9\u7a81\u51fa**\uff1a\n"
    "   - \u5bf9\u4e8e**\u5173\u952e\u6570\u636e**\uff08\u91d1\u989d\u3001\u65f6\u95f4\u3001\u6570\u91cf\uff09\u3001**\u4e13\u6709\u540d\u8bcd**\uff08\u9879\u76ee\u540d\u3001\u90e8\u95e8\u540d\u3001\u6280\u672f\u672f\u8bed\uff09\uff0c\u8bf7\u786e\u4fdd\u51c6\u786e\u65e0\u8bef\uff1b\n"
    "   - \u5982\u9047\u51b3\u7b56\u6027\u7ed3\u8bba\u6216\u5f85\u529e\u4e8b\u9879\uff0c\u4fdd\u6301\u539f\u8bdd\uff0c\u4e0d\u8981\u9057\u6f0f\u3002\n\n"
    "4. **\u6df7\u5408\u8bed\u8a00\u5904\u7406**\uff1a\n"
    "   - \u4e2d\u82f1\u6587\u6df7\u6742\u65f6\uff0c\u82f1\u6587\u5355\u8bcd\u524d\u540e\u4fdd\u7559\u7a7a\u683c\uff08\u5982\u201c\u4f7f\u7528 AI \u6280\u672f\u201d\uff09\u3002\n"
    "   - \u4ec5\u8f93\u51fa\u8f6c\u5199\u6b63\u6587\uff0c\u4e0d\u8981\u5305\u542b\u201c\u597d\u7684\u201d\u3001\u201c\u4ee5\u4e0b\u662f\u8f6c\u5199\u201d\u7b49\u65e0\u5173\u56de\u590d\u3002"
)

_USER_PROMPT_DIARIZATION = (
    "请对以下音频进行专业且高精度的转写，并按说话人切分输出结构化 JSON。\n\n"
    "**⚠️ 核心任务：精准识别不同的说话人 ⚠️**\n"
    "这段音频通常包含两人或多人的对话（如访谈、会议、一问一答）。"
    "你必须仔细辨别不同说话人的声音特征（男/女、音调、语速），**绝对不能把明显的对话内容错误地归为同一个说话人**。\n\n"
    "**区分说话人的关键线索**：\n"
    "1. 🎵 **音色与音调**：男女声音色的明显差异、嗓音特征。\n"
    "2. 🗣️ **语速和节奏**：个人的说话习惯、语气词使用频率。\n"
    "3. 💬 **对话逻辑**：一问一答、提问者 vs 回答者、赞同与反驳。\n"
    "4. 🔄 **发言交替**：在明显的话题交锋或被打断时，必然是不同人在说话。\n\n"
    "**输出格式**：仅输出一个纯净的 JSON 对象，不包含代码块标记或其他文字：\n"
    '{"segments": [\n'
    '  {"speaker": "说话人1", "start": 0.0, "end": 15.3, "text": "这是第一个人的发言..."},\n'
    '  {"speaker": "说话人2", "start": 15.3, "end": 28.7, "text": "这是另一个人（比如被采访者）的回应..."},\n'
    '  {"speaker": "说话人1", "start": 28.7, "end": 45.0, "text": "第一个人继续提问或补充..."}\n'
    ']}\n\n'
    "**转写规范**：\n"
    "1. **说话人切分**：只要说话人发生切换，必须新建一个 segment。\n"
    "2. **时间戳**：提供该段发言的开始和结束秒数（尽可能准确）。\n"
    "3. **智能净化**：剔除无意义的口语废话（嗯、啊、那个），修正口误，保持原意。\n"
    "4. **完整性**：绝不遗漏实质性内容，确保转写文本完整。\n"
    "5. **统一语言**：使用简体中文输出。\n\n"
    "**最高优先级强制要求**：仔细聆听，只要有两个人或以上在交替说话，**必须**使用不同的 speaker 标签（说话人1, 说话人2 等）将其区分开来！！！"
)

def transcribe_chunk(chunk_path: str, client, model: str, provider: str = "openai",
                     enable_diarization: bool = False,
                     census_context: str = "") -> str:
    """Send a single audio chunk to the appropriate API and return text."""
    if provider == "zhipu" and ZhipuAI and isinstance(client, ZhipuAI) and ("asr" in model.lower() or model == "glm-asr-2512"):
        with open(chunk_path, "rb") as f:
            response = client.audio.transcriptions.create(model=model, file=f)
        return response.text

    if provider == "modelscope":
        with open(chunk_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model=model, file=f, response_format="text"
            )
        return response if isinstance(response, str) else response.text

    # Default: OpenAI-compatible Multimodal Chat completion
    mime = "audio/mpeg" if chunk_path.endswith(".mp3") else "audio/mp4"
    with open(chunk_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    user_prompt = _USER_PROMPT_DIARIZATION if enable_diarization else _USER_PROMPT_STANDARD

    # Inject census context into diarization prompt (if available)
    if enable_diarization and census_context:
        user_prompt = user_prompt + census_context

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": 65536,
    }

    # Special: Zhipu Thinking parameter
    if provider == "zhipu" and "glm-4.6v" in model:
        kwargs["extra_body"] = {"thinking": True}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()
