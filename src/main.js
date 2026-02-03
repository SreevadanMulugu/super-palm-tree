const path = require('path');

// Debug: Check what require('electron') returns
const electronModule = require('electron');
console.log('Type of electronModule:', typeof electronModule);
console.log('ElectronModule value:', electronModule);
console.log('ElectronModule.default:', electronModule.default);
console.log('ElectronModule keys:', Object.keys(electronModule));

// Try different ways to get Electron API
let app, BrowserWindow;

if (typeof electronModule === 'object' && electronModule.app) {
    // Standard Electron API object
    app = electronModule.app;
    BrowserWindow = electronModule.BrowserWindow;
    console.log('Using standard Electron API object');
} else if (electronModule.default && typeof electronModule.default === 'object') {
    // Try default export
    app = electronModule.default.app;
    BrowserWindow = electronModule.default.BrowserWindow;
    console.log('Using default export');
} else {
    console.error('Cannot find Electron API!');
    console.error('Available properties:', Object.getOwnPropertyNames(electronModule));
    process.exit(1);
}

console.log('app:', app);
console.log('BrowserWindow:', BrowserWindow);

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    mainWindow.loadFile(path.join(__dirname, 'ui/index.html'));

    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(() => {
    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
