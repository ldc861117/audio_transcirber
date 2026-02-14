# Audio Transcriber Architecture

## Overview

The Audio Transcriber is a Flask-based web application designed to split large audio files and transcribe them using OpenAI-compatible APIs (e.g., Aliyun SenseVoice, OpenAI Whisper).

## System Components

### 1. Backend (`app.py`)

- **Framework**: Flask.
- **Core Logic**:
  - **Audio Splitting**: Uses `pydub` (ffmpeg) to split audio into chunks based on duration (default 10 mins) and size (default 20MB) to fit API limits.
  - **Transcription**: Uses `openai` python client to send chunks to a compatible API.
  - **Concurrency**: User requests spawn background threads to handle the split-transcribe-merge workflow.
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
    - `split_audio()`: Original file -> Chunk files.
    - `run_transcription()`: Iterate chunks -> API Call -> Text segment.
3.  **Output**: Segments are merged into a single transcript.

## Key Dependencies

- `flask`: Web server.
- `pydub`: Audio processing.
- `openai`: API client.

## Directory Structure

- `/`: Root directory.
- `app.py`: Main entry point.
- `static/`: Frontend assets.
- `docs_local/`: Local documentation and resources.
