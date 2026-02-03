const { contextBridge, ipcRenderer } = require('electron');

// Expose protected APIs to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // Status APIs
    getStatus: () => ipcRenderer.invoke('get-status'),
    getHardware: () => ipcRenderer.invoke('get-hardware'),

    // Ollama APIs
    startOllama: () => ipcRenderer.invoke('start-ollama'),
    stopOllama: () => ipcRenderer.invoke('stop-ollama'),

    // Message APIs
    sendMessage: (message) => ipcRenderer.invoke('send-message', message),

    // Browser APIs
    startBrowser: () => ipcRenderer.invoke('browser-start'),
    stopBrowser: () => ipcRenderer.invoke('browser-stop'),

    // Event listeners
    onStatusResponse: (callback) => {
        ipcRenderer.on('status-response', (event, data) => callback(data));
    },
    onHardwareResponse: (callback) => {
        ipcRenderer.on('hardware-response', (event, data) => callback(data));
    },
    onMessageResponse: (callback) => {
        ipcRenderer.on('message-response', (event, data) => callback(data));
    },
    onOllamaStarted: (callback) => {
        ipcRenderer.on('ollama-started', (event, data) => callback(data));
    },
    onOllamaStopped: (callback) => {
        ipcRenderer.on('ollama-stopped', (event, data) => callback(data));
    },
    onBrowserStarted: (callback) => {
        ipcRenderer.on('browser-started', (event, data) => callback(data));
    },
    onBrowserStopped: (callback) => {
        ipcRenderer.on('browser-stopped', (event, data) => callback(data));
    }
});
