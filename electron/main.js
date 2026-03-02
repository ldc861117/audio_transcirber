/**
 * Audio Transcriber — Electron main process
 *
 * Spawns the Flask backend as a child process, waits for it to become ready,
 * then opens a BrowserWindow pointing at the Flask server.
 *
 * Chromium gives us full getDisplayMedia + MediaRecorder(webm) support.
 */

const { app, BrowserWindow, desktopCapturer, session, systemPreferences, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const net = require('net');
const fs = require('fs');

// Enable system audio loopback for screen sharing
// These Chromium flags enable the ScreenCaptureKit & CoreAudio audio loopback paths
app.commandLine.appendSwitch('enable-features', [
  'MacLoopbackAudioForScreenShare',
  'MacSckSystemAudioLoopbackOverride',
  'MacCatapSystemAudioLoopbackCapture',  // CoreAudio Tap path
  'PulseaudioLoopbackForScreenShare',    // Linux support
].join(','));

const PORT = 5099;
const FLASK_URL = `http://127.0.0.1:${PORT}`;

let mainWindow = null;
let flaskProcess = null;

// ── Locate the Flask binary ─────────────────────────────────
function getFlaskPath() {
  if (app.isPackaged) {
    // In production: flask_dist is in Resources/flask_dist/Audio Transcriber/
    const resourcesPath = process.resourcesPath;
    const path1 = path.join(resourcesPath, 'flask_dist', 'Audio Transcriber', 'Audio Transcriber');
    const path2 = path.join(resourcesPath, 'flask_dist', 'Audio Transcriber'); // fallback
    return fs.existsSync(path1) ? path1 : path2;
  }
  return null;
}

// ── Start Flask ─────────────────────────────────────────────
function startFlask() {
  const flaskBin = getFlaskPath();

  if (flaskBin) {
    // Production: run the PyInstaller binary
    console.log('[Electron] Starting Flask binary:', flaskBin);
    flaskProcess = spawn(flaskBin, [], {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env,
        PATH: `${process.env.PATH}:/usr/local/bin:/opt/homebrew/bin`,
      },
    });
  } else {
    // Development: run python app.py using .venv if available
    const projectRoot = path.join(__dirname, '..');
    const venvPython = path.join(projectRoot, '.venv', 'bin', 'python');
    const pythonBin = fs.existsSync(venvPython) ? venvPython : 'python3';
    console.log('[Electron] Starting Flask in dev mode:', pythonBin);
    flaskProcess = spawn(pythonBin, ['app.py'], {
      cwd: projectRoot,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env },
    });
  }

  flaskProcess.stdout.on('data', (data) => {
    console.log(`[Flask] ${data.toString().trim()}`);
  });

  flaskProcess.stderr.on('data', (data) => {
    console.error(`[Flask] ${data.toString().trim()}`);
  });

  flaskProcess.on('close', (code) => {
    console.log(`[Flask] Process exited with code ${code}`);
    flaskProcess = null;
  });

  flaskProcess.on('error', (err) => {
    console.error('[Flask] Failed to start:', err);
    flaskProcess = null;
  });
}

// ── Wait for Flask TCP port to be open ──────────────────────
function waitForFlask(timeoutMs = 60000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    let resolved = false;

    const check = () => {
      if (resolved) return;
      if (Date.now() - start > timeoutMs) {
        resolved = true;
        reject(new Error(`Flask did not start within ${timeoutMs / 1000}s`));
        return;
      }

      const socket = new net.Socket();
      socket.setTimeout(800);

      socket.on('connect', () => {
        socket.destroy();
        if (!resolved) {
          resolved = true;
          console.log('[Electron] Flask is ready on port', PORT);
          resolve();
        }
      });

      socket.on('error', () => {
        socket.destroy();
        setTimeout(check, 500);
      });

      socket.on('timeout', () => {
        socket.destroy();
        setTimeout(check, 500);
      });

      socket.connect(PORT, '127.0.0.1');
    };

    check();
  });
}

// ── Create the main window ──────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 375,
    minHeight: 600,
    title: 'Audio Transcriber',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Show a loading page while Flask starts
  mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
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
  `)}`);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ── Permissions: allow getDisplayMedia with audio ───────────
function setupPermissions() {
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    const allowed = ['media', 'display-capture', 'audioCapture'];
    callback(allowed.includes(permission));
  });

  session.defaultSession.setPermissionCheckHandler((webContents, permission) => {
    const allowed = ['media', 'display-capture', 'audioCapture'];
    return allowed.includes(permission);
  });

  // ── IPC: enable/disable system audio loopback ──
  // Pattern from electron-audio-loopback: the renderer calls enableLoopbackAudio()
  // before getDisplayMedia(). This dynamically registers the handler that injects
  // audio: 'loopback' into the callback.
  ipcMain.handle('enable-loopback-audio', () => {
    console.log('[Electron] Enabling loopback audio handler');
    session.defaultSession.setDisplayMediaRequestHandler((request, callback) => {
      // Use request.frame as video source — this captures the requesting tab itself
      // (no Screen Recording permission needed). The renderer only wants the audio
      // loopback; it discards video tracks immediately.
      console.log('[Electron] Granting tab capture + loopback audio');
      callback({ video: request.frame, audio: 'loopback' });
    });
  });

  ipcMain.handle('disable-loopback-audio', () => {
    console.log('[Electron] Disabling loopback audio handler');
    session.defaultSession.setDisplayMediaRequestHandler(null);
  });

  // IPC: let renderer check screen recording permission status
  ipcMain.handle('get-screen-permission-status', () => {
    return systemPreferences.getMediaAccessStatus('screen');
  });
}

// ── App lifecycle ───────────────────────────────────────────
app.whenReady().then(async () => {
  setupPermissions();
  startFlask();
  createWindow();

  try {
    await waitForFlask();
    if (mainWindow) {
      mainWindow.loadURL(FLASK_URL);
    }
  } catch (err) {
    console.error('[Electron] Flask startup failed:', err.message);
    if (mainWindow) {
      mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(`
        <html><body style="background:#0f172a;color:#f87171;font-family:system-ui;
        display:flex;justify-content:center;align-items:center;height:100vh;margin:0">
        <div style="text-align:center">
          <h2>⚠️ 启动失败</h2>
          <p>Flask 服务器未能启动。</p>
          <pre style="color:#94a3b8;background:#1e293b;padding:16px;border-radius:8px;
          text-align:left;font-size:12px">${err.message}</pre>
        </div></body></html>
      `)}`);
    }
  }
});

app.on('window-all-closed', () => {
  if (flaskProcess) {
    console.log('[Electron] Killing Flask process...');
    flaskProcess.kill('SIGTERM');
  }
  app.quit();
});

app.on('before-quit', () => {
  if (flaskProcess) {
    flaskProcess.kill('SIGTERM');
  }
});
