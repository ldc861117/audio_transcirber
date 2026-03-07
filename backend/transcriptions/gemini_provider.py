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
    "\u8bf7\u5bf9\u4ee5\u4e0b\u97f3\u9891\u8fdb\u884c\u4e13\u4e1a\u8f6c\u5199\uff0c\u5e76\u8f93\u51fa\u7ed3\u6784\u5316 JSON \u683c\u5f0f\u4ee5\u652f\u6301\u8bf4\u8bdd\u4eba\u8bc6\u5222\u3002\n\n"
    "**\u8f93\u51fa\u8981\u6c42**\uff1a\u4ec5\u8f93\u51fa\u4e00\u4e2a JSON \u5bf9\u8c61\uff0c\u4e0d\u8981\u5305\u542b\u4efb\u4f55\u5176\u4ed6\u6587\u5b57\uff1a\n"
    '{\"segments\": [\n'
    '  {\"speaker\": \"\u8bf4\u8bdd\u4eba1\", \"start\": 0.0, \"end\": 15.3, \"text\": \"\u8f6c\u5199\u5185\u5bb9...\"},\n'
    '  {\"speaker\": \"\u8bf4\u8bdd\u4eba2\", \"start\": 15.3, \"end\": 28.7, \"text\": \"\u8f6c\u5199\u5185\u5bb9...\"}\n'
    ']}\n\n'
    "**\u8f6c\u5199\u89c4\u8303**\uff1a\n"
    "1. **\u8bf4\u8bdd\u4eba\u533a\u5206**\uff1a\u6839\u636e\u58f0\u7eb9\u548c\u4e0a\u4e0b\u6587\u533a\u5206\u4e0d\u540c\u8bf4\u8bdd\u4eba\uff0c\u4f7f\u7528 \"\u8bf4\u8bdd\u4eba1\"\u3001\"\u8bf4\u8bdd\u4eba2\" \u7b49\u6807\u8bb0\uff1b\n"
    "2. **\u65f6\u95f4\u6233**\uff1astart \u548c end \u662f\u8be5\u6bb5\u53d1\u8a00\u5728\u97f3\u9891\u4e2d\u7684\u8fd1\u4f3c\u79d2\u6570\uff0c\u5c3d\u91cf\u51c6\u786e\uff1b\n"
    "3. **\u667a\u80fd\u51c0\u5316**\uff1a\u5254\u9664\u53e3\u8bed\u5e9f\u8bdd\uff0c\u4fee\u6b63\u53e3\u8bef\u548c\u91cd\u590d\uff0c\u4fdd\u6301\u539f\u610f\uff1b\n"
    "4. **\u4fdd\u6301\u5b8c\u6574**\uff1a\u4e0d\u8981\u9057\u6f0f\u4efb\u4f55\u5b9e\u8d28\u5185\u5bb9\uff1b\n"
    "5. **\u7b80\u4f53\u4e2d\u6587**\uff1a\u59cb\u7ec8\u4f7f\u7528\u7b80\u4f53\u4e2d\u6587\u8f93\u51fa\u3002"
)

def transcribe_chunk(chunk_path: str, client, model: str, provider: str = "openai",
                     enable_diarization: bool = False) -> str:
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
        "max_tokens": 8192,
    }

    # Special: Zhipu Thinking parameter
    if provider == "zhipu" and "glm-4.6v" in model:
        kwargs["extra_body"] = {"thinking": True}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()
