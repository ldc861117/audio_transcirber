# Audio Transcriber Architecture

## Overview

The Audio Transcriber is a Flask-based web application designed to split large audio files and transcribe them using OpenAI-compatible APIs (e.g., Google Gemini, Zhipu AI, ModelScope SenseVoice).

## System Components

### 1. Backend (`app.py`)

- **Framework**: Flask.
- **Core Logic**:
  - **Audio Splitting**: Uses `pydub` (ffmpeg) to split audio into overlapping chunks based on duration (default 30 mins), size (default 50MB), and overlap (default 2 mins) to fit API limits while ensuring seamless stitching.
  - **Transcription**: Uses `openai` python client to send chunks to a compatible API.
  - **LLM Stitching**: After transcription, overlapping chunk transcripts are merged via LLM-based semantic deduplication (`services/stitch_service.py`). This handles the non-determinism of LLM transcription — the same 2 minutes of audio may produce slightly different wording in each chunk.
  - **Concurrency**: User requests spawn background threads to handle the split-transcribe-stitch-merge workflow.
  - **State Management**: In-memory `tasks` dictionary tracks progress and results.

### 2. Frontend (`static/`)

- **Structure**: `index.html` (Single Page Application feel), `style.css`, `script.js`.
- **Interaction**:
  - Users upload files via a form.
  - Javascript polls the `/api/status/<task_id>` endpoint to show progress bars.
  - Displays final transcription results.

### 3. Data Flow

1.  **Upload**: User uploads audio -> Saved to temp dir (`/tmp/audio_transcriber_uploads` or similar).
2.  **Processing**:
    - `split_audio()`: Original file -> Overlapping chunk files (stride = chunk_duration - overlap).
    - `run_transcription()`: Iterate chunks -> API Call -> Text segment.
    - `stitch_transcripts()`: Sequential LLM-based merge of overlapping transcripts -> Seamless text.
3.  **Output**: Stitched segments form the final transcript.

## Key Dependencies

- `flask`: Web server.
- `pydub`: Audio processing.
- `openai`: API client.

## Directory Structure

- `/`: Root directory.
- `app.py`: Main entry point.
- `services/stitch_service.py`: LLM-based overlap transcript stitching.
- `static/`: Frontend assets.
- `docs_local/`: Local documentation and resources.

