"""
Audio Transcriber — macOS app launcher
Starts Flask in a background thread, then opens a pywebview native window.
"""
import os
import sys
import time
import threading
import traceback
import urllib.request

# ── PyInstaller resource path support ──
if hasattr(sys, '_MEIPASS'):
    os.chdir(sys._MEIPASS)

os.environ["PATH"] += os.pathsep + "/usr/local/bin" + os.pathsep + "/opt/homebrew/bin"

PORT = 5099

LOADING_HTML = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Loading…</title>
<style>
  body { margin:0; display:flex; justify-content:center; align-items:center;
         height:100vh; background:#0f172a; font-family:system-ui; }
  .loader { text-align:center; color:#94a3b8; }
  .loader h2 { font-size:1.4em; margin-bottom:12px; }
  .spinner { width:36px; height:36px; border:4px solid #1e293b;
             border-top-color:#6366f1; border-radius:50%;
             animation: spin 0.8s linear infinite; margin:0 auto 16px; }
  @keyframes spin { to { transform:rotate(360deg); } }
</style>
</head>
<body><div class="loader">
  <div class="spinner"></div>
  <h2>🎙️ Audio Transcriber</h2>
  <p>正在启动…</p>
</div></body>
</html>
"""

# Error page template for when Flask fails to start
ERROR_HTML = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Error</title>
<style>
  body {{ margin:0; display:flex; justify-content:center; align-items:center;
         height:100vh; background:#0f172a; font-family:system-ui; color:#f87171; }}
  .error {{ text-align:center; max-width:600px; padding:24px; }}
  pre {{ text-align:left; font-size:12px; background:#1e293b; padding:16px;
         border-radius:8px; overflow-x:auto; color:#94a3b8; white-space:pre-wrap; }}
</style>
</head>
<body><div class="error">
  <h2>⚠️ 启动失败</h2>
  <p>Flask 服务器启动出错：</p>
  <pre>{error}</pre>
</div></body>
</html>
"""

flask_error = None


def start_flask():
    """Run Flask in a background thread."""
    global flask_error
    try:
        from app import app
        app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)
    except Exception as e:
        flask_error = traceback.format_exc()
        print(f"[FLASK ERROR] {flask_error}", file=sys.stderr, flush=True)


def wait_and_redirect(window):
    """Wait for Flask to become ready, then navigate to it."""
    global flask_error
    url = f"http://127.0.0.1:{PORT}/"
    for i in range(60):  # up to 30 seconds
        if flask_error:
            window.load_html(ERROR_HTML.format(error=flask_error))
            return
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        # Timed out
        window.load_html(ERROR_HTML.format(
            error=f"Flask server did not start within 30 seconds.\n{flask_error or ''}"
        ))
        return
    window.load_url(url)


if __name__ == "__main__":
    import webview

    # Start Flask in a daemon thread
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Create window with loading HTML immediately (no blocking)
    window = webview.create_window(
        "Audio Transcriber",
        html=LOADING_HTML,
        width=1200,
        height=800,
        min_size=(375, 600),
    )

    # webview.start() runs the GUI loop on the main thread (required by Cocoa)
    # The func parameter runs wait_and_redirect in a separate thread
    webview.start(wait_and_redirect, window)
