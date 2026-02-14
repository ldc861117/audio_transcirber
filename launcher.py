import os
import sys
import threading
import webview

# Extend PATH to include common locations for ffmpeg on macOS
# This is crucial for pydub to find ffmpeg when running as a .app
os.environ["PATH"] += os.pathsep + "/usr/local/bin" + os.pathsep + "/opt/homebrew/bin"

from app import app

def run_flask():
    # Run Flask without the reloader
    app.run(host="127.0.0.1", port=5099, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Create a native window
    # Wait slightly to ensure Flask is up, or just let webview retry loading
    webview.create_window("Audio Transcriber", "http://127.0.0.1:5099", width=1024, height=768)
    webview.start()

    sys.exit(0)
