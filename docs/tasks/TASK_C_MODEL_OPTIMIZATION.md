# [Phase1 Track C] Gemini 3 智能切分参数优化

## 目标

将 Provider 配置外部化，并利用 Gemini 3 Flash Preview 的大上下文能力，避免不必要的音频切分和多次 API 请求。

## 必读文档

- `contracts.yaml` — 重点看 `provider_config`
- `app.py` — 理解 `BUILTIN_PROVIDERS` (line 68-74), `split_audio()` (line 90-127), `DEFAULT_MAX_CHUNK_MINUTES/MB` (line 57-58)
- `AGENTS.md` — 开发规范

## ⚠️ 严格文件边界

**只能创建/修改：**

- `services/provider_service.py`
- `configs/providers.yaml`
- `tests/test_provider_service.py`

**绝不修改：**

- `app.py`, `auth.py`, `speaker.py`, `speaker_db.py`
- `static/*`, `contracts.yaml`

## 子任务

### 1. Provider 配置文件 — `configs/providers.yaml`

```yaml
providers:
  gemini:
    display_name: "Google Gemini"
    base_url: "https://generativelanguage.googleapis.com/v1beta/openai"
    models:
      gemini-2.5-flash:
        max_input_mb: 20
        max_input_minutes: 15
      gemini-3-flash-preview:
        max_input_mb: 100
        max_input_minutes: 120 # 2小时，几乎不需要切分
    default_model: "gemini-2.5-flash"
    api_key_env: "GEMINI_API_KEY"

  zhipu:
    display_name: "智谱 AI"
    base_url: ""
    models:
      glm-asr-2512:
        max_input_mb: 25
        max_input_minutes: 30
      glm-4.6v-flash:
        max_input_mb: 20
        max_input_minutes: 15
    default_model: "glm-asr-2512"
    api_key_env: "ZHIPU_API_KEY"
    is_sdk: true

  modelscope:
    display_name: "ModelScope (魔搭)"
    base_url: "https://api-inference.modelscope.ai/v1"
    models:
      iic/SenseVoiceSmall:
        max_input_mb: 20
        max_input_minutes: 10
    default_model: "iic/SenseVoiceSmall"

  custom:
    display_name: "自定义"
    base_url: ""
    models: {}
    default_model: ""
```

### 2. 服务层 — `services/provider_service.py`

```python
class ProviderService:
    def __init__(self):
        self._config = None  # lazy load from configs/providers.yaml

    def get_all_providers(self) -> dict
        # 返回所有 provider 配置

    def get_provider_config(self, name: str) -> dict | None
        # 返回单个 provider 的完整配置

    def get_model_limits(self, provider: str, model: str) -> dict
        # 返回 {"max_input_mb": float, "max_input_minutes": float}
        # 如果未知模型，返回保守默认值 {"max_input_mb": 20, "max_input_minutes": 10}

    def get_optimal_chunk_params(self, provider: str, model: str, file_size_mb: float, duration_minutes: float = 0) -> dict
        # 核心方法！根据模型能力和文件实际大小决定是否需要切分
        # 返回 {"max_minutes": int, "max_mb": int, "skip_split": bool}
        # 当文件在模型上限内时，skip_split=True

    def has_server_key(self, provider: str) -> bool
        # 检查服务端是否配置了 API key
```

### 3. 测试 — `tests/test_provider_service.py`

- 测试 YAML 配置加载
- 测试 `get_optimal_chunk_params` 的各种场景：
  - 小文件 + Gemini 3 → skip_split=True
  - 大文件 + 老模型 → 正常切分参数
  - 未知模型 → 保守默认值

## 验收标准

1. `python -m py_compile services/provider_service.py`
2. `python -c "from services.provider_service import ProviderService; ps = ProviderService(); print(ps.get_optimal_chunk_params('gemini', 'gemini-3-flash-preview', 50.0))"`
3. 上述命令应输出 `{"max_minutes": 120, "max_mb": 100, "skip_split": True}` 或类似

## 集成点

- 在 `app.py` 的 `upload()` 中用 `ProviderService.get_optimal_chunk_params()` 替换硬编码的 `DEFAULT_MAX_CHUNK_MINUTES/MB`
- 在前端展示 Provider 列表时用 `get_all_providers()` 替代硬编码
- 这些集成步骤 **不在本 Track 范围内**

## 环境说明

- Python 3.11+，依赖在 requirements.txt
- 需要 `pyyaml` — 已在标准库中或可通过 pip 安装
- 如果依赖安装失败，跳过测试，直接提交代码
