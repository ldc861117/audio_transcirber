# [Phase1 Track D] 说话人分离增强

## 目标

重构说话人分析流程：以 AI 模型的说话人分割能力为基础，声纹库匹配作为增强，提高分离准确率。

## 必读文档

- `contracts.yaml` — 理解整体数据结构
- `speaker.py` — **核心**，当前的说话人分析实现 (588 行)，特别关注：
  - `parse_diarization_response()` — Gemini 返回解析
  - `process_speakers()` — 声纹处理
  - `merge_cross_chunk_speakers()` — 跨 chunk 合并
  - `SpeakerEmbedder` 类 — ONNX 声纹提取
- `speaker_db.py` — 声纹数据库 CRUD
- `app.py` — `run_transcription()` 中的 diarization 部分 (line 305-351)

## ⚠️ 严格文件边界

**只能创建/修改：**

- `speaker_v2.py` — 新文件，重构版说话人模块
- `services/diarization_service.py` — 新文件，分离编排服务
- `tests/test_diarization.py`

**绝不修改：**

- `app.py`, `auth.py`, `speaker.py`（保持原文件不动）, `speaker_db.py`
- `static/*`, `contracts.yaml`

**可读取（只读）：**

- `speaker.py` — 复用 `SpeakerEmbedder` 和数据类
- `speaker_db.py` — 复用 `find_matching_profiles()`, `get_profiles_for_user()`

## 架构改进思路

### 当前问题

```
当前流程: Gemini JSON 解析 → 独立声纹分析 → 独立声纹匹配 → 合并
问题: 模型分割和声纹分析是割裂的，声纹匹配不准
```

### 目标流程

```
新流程:
1. 模型分割 (Gemini 原生) → 获取结构化 segments (speaker, start, end, text)
2. 对每个 speaker 的所有 segments → 提取多段 embedding → 平均聚合
3. 聚合后的 embedding → 与声纹库匹配 (cosine similarity)
4. 高于阈值 → 自动标注；低于阈值 → 保留原标签
```

## 子任务

### 1. 重构入口 — `services/diarization_service.py`

```python
class DiarizationService:
    def diarize(self, audio_path: str, chunk_results: list[str],
                user_id: int, chunk_paths: list[str]) -> dict:
        """
        核心编排方法。

        Args:
            audio_path: 原始音频路径
            chunk_results: 每个 chunk 的 Gemini 原始响应
            user_id: 用户 ID（用于声纹库查询）
            chunk_paths: 每个 chunk 的文件路径

        Returns:
            {
                "speakers": [SpeakerResult...],
                "transcript": str (带说话人标注的完整转录)
            }
        """
        # Step 1: 解析所有 chunk 的 segments
        # Step 2: 合并跨 chunk 的同一说话人
        # Step 3: 批量提取 embeddings (多段平均)
        # Step 4: 声纹库匹配
        # Step 5: 组装最终结果
```

### 2. 增强声纹模块 — `speaker_v2.py`

从 `speaker.py` 复用核心组件，新增：

```python
def aggregate_embeddings(embeddings: list[np.ndarray]) -> np.ndarray:
    """多段 embedding 平均聚合，比单段更稳定"""

def match_with_library(user_id: int, embedding: np.ndarray,
                       threshold: float = 0.65) -> dict | None:
    """与声纹库匹配，返回 {profile_id, name, similarity} 或 None"""
    # 使用 speaker_db.find_matching_profiles()

def smart_threshold(embedding: np.ndarray, candidates: list) -> float:
    """动态阈值：基于候选者间距和方差动态调整"""
    # 如果最高相似度远高于第二，可以降低阈值
    # 如果差距很小，提高阈值避免误判
```

### 3. 关键改进点

1. **多段 embedding 聚合**：不再用单个 clip 匹配，收集同一说话人的多段 > 1秒的音频，分别提取 embedding 后取平均
2. **动态阈值**：当前固定 0.70 阈值不够灵活，改为根据候选者的分布动态调整
3. **跨 chunk 合并改进**：利用 embedding 相似度做跨 chunk 的同一说话人合并，而非仅靠 label 名字

### 4. 测试 — `tests/test_diarization.py`

- 测试 `aggregate_embeddings` 的数学正确性
- 测试 `smart_threshold` 边界情况
- 测试 `DiarizationService.diarize` 的整体流程（mock 数据）

## 验收标准

1. `python -m py_compile speaker_v2.py services/diarization_service.py`
2. `python -c "from services.diarization_service import DiarizationService"`
3. `python -c "from speaker_v2 import aggregate_embeddings, match_with_library"`

## 集成点

- 在 `app.py` 的 `run_transcription()` 中，将 diarization 部分替换为调用 `DiarizationService.diarize()`
- 这个集成步骤 **不在本 Track 范围内**

## 环境说明

- Python 3.11+，依赖在 requirements.txt
- 需要 numpy, onnxruntime, scipy (已在 requirements.txt 中)
- 如果依赖安装失败，跳过测试，直接提交代码
