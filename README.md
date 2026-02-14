# Audio Transcriber

Audio Transcriber is a Flask-based web application designed for efficient and accurate audio transcription. It leverages OpenAI-compatible APIs (like Google Gemini) to process audio files, supporting large files through intelligent chunking and parallel processing.

## Features

- **Intelligent Audio Splitting**: Automatically splits large audio files based on duration and file size constraints to fit API limits.
- **Multi-Format Support**: Handles a wide range of audio formats including `.wav`, `.mp3`, `.ogg`, `.flac`, `.m4a`, and more.
- **Parallel Processing**: Transcribes multiple chunks concurrently for faster results.
- **OpenAI API Compatibility**: Works with any OpenAI-compatible transcription API.
- **Customizable Prompts**: Uses a system prompt designed for professional meeting minutes and verbatim transcription.
- **User-Friendly Interface**: Simple web interface for uploading files and monitoring progress.

## Prerequisites

- Python 3.8+
- ffmpeg (required by pydub for audio processing)

## Installation

1.  Clone the repository:

    ```bash
    git clone https://github.com/ldc861117/audio_transcirber.git
    cd audio_transcirber
    ```

2.  Create and activate a virtual environment (recommended):

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Start the application:

    ```bash
    python app.py
    ```

2.  Open your browser and navigate to:
    `http://localhost:5099`

3.  Configure your API settings in the web interface:
    - **Base URL**: Your API provider's base URL (e.g., `https://generativelanguage.googleapis.com/v1beta/openai/` for Gemini).
    - **API Key**: Your API key.
    - **Model**: The model name (e.g., `gemini-2.5-flash`).

4.  Upload an audio file and wait for the transcription to complete.

## Configuration

- **Chunk Size**: You can adjust the maximum duration (minutes) and file size (MB) for audio chunks in the web interface.
- **Prompts**: The system prompt is defined in `app.py` and is tailored for Chinese meeting transcription.

## License

[MIT License](LICENSE)
