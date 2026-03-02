const { contextBridge, ipcRenderer } = require('electron');

// Preload — contextIsolation is on by default in Electron 12+.
// Expose platform info + screen permission status to the renderer.
contextBridge.exposeInMainWorld('electronAPI', {
  platform: process.platform,
  getScreenPermissionStatus: () => ipcRenderer.invoke('get-screen-permission-status'),
  enableLoopbackAudio: () => ipcRenderer.invoke('enable-loopback-audio'),
  disableLoopbackAudio: () => ipcRenderer.invoke('disable-loopback-audio'),
});
