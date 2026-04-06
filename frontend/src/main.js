/**
 * Electron Ana Process
 * Flask backend'i başlatır ve kapatır
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow = null;
let backendProcess = null;
let backendPort = 5000;

/**
 * Flask backend'i başlat
 */
function startBackend() {
    return new Promise((resolve, reject) => {
        const isDev = !app.isPackaged;
        let backendPath;

        if (isDev) {
            // Geliştirme modunda Python scripti çalıştır
            backendPath = path.join(__dirname, '..', '..', 'backend', 'app.py');
            backendProcess = spawn('python', [backendPath]);
        } else {
            // Production modunda exe'yi çalıştır
            backendPath = path.join(process.resourcesPath, 'backend', 'cafe_backend.exe');
            backendProcess = spawn(backendPath);
        }

        console.log('Backend başlatılıyor:', backendPath);

        backendProcess.stdout.on('data', (data) => {
            const output = data.toString();
            console.log('Backend:', output.trim());
            
            // Port bilgisini yakala
            const portMatch = output.match(/Port: (\d+)/);
            if (portMatch) {
                backendPort = parseInt(portMatch[1], 10);
                console.log('Backend port:', backendPort);
            }
            
            // Backend hazır olduğunda resolve
            if (output.includes('Flask sunucusu başlatılıyor')) {
                setTimeout(() => resolve(backendPort), 2000);
            }
        });

        backendProcess.stderr.on('data', (data) => {
            const text = data.toString();
            // Flask/werkzeug access log'ları (200 vs) gerçek hata değil, konsolu kirletmesin
            if (/HTTP\/1\.1"\s+20\d/.test(text)) {
                console.log('Backend:', text.trim());
                return;
            }
            console.error('Backend HATA:', text);
        });

        backendProcess.on('error', (error) => {
            console.error('Backend başlatılamadı:', error);
            reject(error);
        });

        backendProcess.on('close', (code) => {
            console.log('Backend kapandı. Kod:', code);
        });

        // Timeout: 10 saniye içinde başlamazsa hata
        setTimeout(() => {
            resolve(backendPort);
        }, 10000);
    });
}

/**
 * Ana pencereyi oluştur
 */
function createWindow() {
    const windowOptions = {
        width: 1280,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        }
    };
    
    // Icon varsa ekle
    const iconPath = path.join(__dirname, '..', 'assets', 'icon.png');
    const fs = require('fs');
    if (fs.existsSync(iconPath)) {
        windowOptions.icon = iconPath;
    }
    
    mainWindow = new BrowserWindow(windowOptions);

    // Giriş sayfasını yükle
    mainWindow.loadFile(path.join(__dirname, 'pages', 'login.html'));

    // DevTools'u geliştirme modunda aç
    if (!app.isPackaged) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

/**
 * Backend'i kapat
 */
function stopBackend() {
    if (backendProcess) {
        console.log('Backend kapatılıyor...');
        backendProcess.kill();
        backendProcess = null;
    }
}

// Uygulama hazır olduğunda
app.whenReady().then(async () => {
    try {
        // Backend'i başlat
        await startBackend();
        
        // Pencereyi oluştur
        createWindow();
        
        // Backend port'unu renderer'a gönder
        mainWindow.webContents.on('did-finish-load', () => {
            mainWindow.webContents.send('backend-ready', { port: backendPort });
        });
    } catch (error) {
        console.error('Başlatma hatası:', error);
        app.quit();
    }

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

// Tüm pencereler kapandığında
app.on('window-all-closed', () => {
    stopBackend();
    app.quit();
});

// Uygulama kapanmadan önce
app.on('before-quit', () => {
    stopBackend();
});

// IPC: Backend port'unu al
ipcMain.handle('get-backend-port', () => {
    return backendPort;
});
