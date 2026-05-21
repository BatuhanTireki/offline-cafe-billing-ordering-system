/**
 * Electron Ana Process
 * Flask backend'i başlatır ve kapatır
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow = null;
let backendProcess = null;
let backendPort = 5000;
let backendReady = false;
let backendLogs = [];  // Backend çıktılarını biriktir

/**
 * Health endpoint'e GET isteği atarak backend'in ayakta olup olmadığını kontrol et
 */
function checkHealth(port) {
    return new Promise((resolve) => {
        const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
            let body = '';
            res.on('data', (chunk) => { body += chunk; });
            res.on('end', () => {
                try {
                    const data = JSON.parse(body);
                    resolve(res.statusCode === 200 && data.app === 'cafe-pos');
                } catch (_) {
                    resolve(false);
                }
            });
        });
        req.on('error', () => resolve(false));
        req.setTimeout(1500, () => { req.destroy(); resolve(false); });
    });
}

/**
 * Backend sağlık kontrolünü belirli aralıklarla tekrarla
 */
function waitForBackend(port, maxAttempts = 30, interval = 1000) {
    return new Promise((resolve) => {
        let attempts = 0;
        const timer = setInterval(async () => {
            attempts++;
            const healthy = await checkHealth(port);
            if (healthy) {
                clearInterval(timer);
                resolve(true);
            } else if (attempts >= maxAttempts) {
                clearInterval(timer);
                console.warn(`Backend ${maxAttempts} denemede hazır olmadı.`);
                resolve(false);
            }
        }, interval);
    });
}

/**
 * Flask backend'i başlat
 */
function startBackend() {
    return new Promise((resolve, reject) => {
        const isDev = !app.isPackaged;
        let backendPath;
        let backendDir;

        if (isDev) {
            backendDir = path.join(__dirname, '..', '..', 'backend');
            backendPath = path.join(backendDir, 'app.py');
            
            console.log('[main] DEV mod - Backend:', backendPath);
            const devEnv = { ...process.env };
            const devCred = path.join(backendDir, 'firebase-service-account.json');
            if (fs.existsSync(devCred)) {
                devEnv.FIREBASE_ENABLED = 'true';
                devEnv.FIREBASE_CREDENTIALS_PATH = devCred;
                devEnv.FIREBASE_BRANCH_ID = devEnv.FIREBASE_BRANCH_ID || 'default';
                devEnv.FIREBASE_SYNC_CORE_ON_START = 'true';
            }

            backendProcess = spawn('python', [backendPath], {
                cwd: backendDir,
                env: devEnv
            });
        } else {
            backendDir = path.join(process.resourcesPath, 'backend');
            backendPath = path.join(backendDir, 'cafe_backend.exe');
            
            console.log('[main] PROD mod - Backend:', backendPath);
            console.log('[main] resourcesPath:', process.resourcesPath);
            console.log('[main] backendDir:', backendDir);
            
            // EXE var mı kontrol et
            if (!fs.existsSync(backendPath)) {
                const errMsg = `Backend EXE bulunamadı: ${backendPath}`;
                console.error('[main]', errMsg);
                
                // Dizin içeriğini logla
                try {
                    if (fs.existsSync(backendDir)) {
                        const files = fs.readdirSync(backendDir);
                        console.log('[main] backendDir içeriği:', files);
                    } else {
                        console.error('[main] backendDir mevcut değil:', backendDir);
                        // resources altını kontrol et
                        if (fs.existsSync(process.resourcesPath)) {
                            const resFiles = fs.readdirSync(process.resourcesPath);
                            console.log('[main] resources içeriği:', resFiles);
                        }
                    }
                } catch (e) {
                    console.error('[main] Dizin okuma hatası:', e.message);
                }
                
                backendLogs.push(`HATA: ${errMsg}`);
                // Yine de devam et, belki farklı bir yoldadır
            }
            
            const backendEnv = { ...process.env };
            const credPath = path.join(backendDir, 'firebase-service-account.json');
            if (fs.existsSync(credPath)) {
                backendEnv.FIREBASE_ENABLED = 'true';
                backendEnv.FIREBASE_CREDENTIALS_PATH = credPath;
                backendEnv.FIREBASE_BRANCH_ID = backendEnv.FIREBASE_BRANCH_ID || 'default';
                backendEnv.FIREBASE_SYNC_CORE_ON_START = 'true';
                console.log('[main] Firebase credentials bulundu:', credPath);
            }
            if (!backendEnv.FIREBASE_FULL_SYNC_ON_START) {
                backendEnv.FIREBASE_FULL_SYNC_ON_START = 'false';
            }

            backendProcess = spawn(backendPath, [], {
                cwd: backendDir,
                env: backendEnv
            });
        }

        backendProcess.stdout.on('data', (data) => {
            const output = data.toString();
            console.log('Backend:', output.trim());
            backendLogs.push(output.trim());
            
            // Port bilgisini yakala
            const portMatch = output.match(/Port: (\d+)/);
            if (portMatch) {
                backendPort = parseInt(portMatch[1], 10);
                console.log('[main] Backend port:', backendPort);
            }
        });

        backendProcess.stderr.on('data', (data) => {
            const text = data.toString();
            backendLogs.push('[ERR] ' + text.trim());
            // Flask/werkzeug access log'ları (200 vs) gerçek hata değil
            if (/HTTP\/1\.1"\s+[2-4]\d\d/.test(text)) {
                return;
            }
            console.error('Backend HATA:', text.trim());
        });

        backendProcess.on('error', (error) => {
            console.error('[main] Backend spawn hatası:', error.message);
            backendLogs.push(`[SPAWN HATA] ${error.message}`);
            reject(error);
        });

        backendProcess.on('close', (code) => {
            console.log('[main] Backend kapandı. Kod:', code);
            backendLogs.push(`[EXIT] Çıkış kodu: ${code}`);
            if (!backendReady && code !== 0) {
                console.error('[main] Backend beklenmedik şekilde kapandı!');
            }
        });

        // 2 saniye sonra health polling başla
        setTimeout(async () => {
            console.log(`[main] Health check başlıyor (port: ${backendPort})...`);
            const ok = await waitForBackend(backendPort);
            backendReady = ok;
            if (ok) {
                console.log('[main] Backend hazır!');
            } else {
                console.error('[main] Backend hazır değil. Toplanan loglar:', backendLogs.join('\n'));
            }
            resolve(backendPort);
        }, 2000);
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
        console.log('[main] Backend kapatılıyor...');
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
        
        // Backend port'unu ve log'ları renderer'a gönder
        mainWindow.webContents.on('did-finish-load', () => {
            mainWindow.webContents.send('backend-ready', { 
                port: backendPort,
                logs: backendLogs 
            });
        });
    } catch (error) {
        console.error('[main] Başlatma hatası:', error);
        // Hata olsa bile pencereyi aç ki kullanıcı bilgi görebilsin
        createWindow();
        mainWindow.webContents.on('did-finish-load', () => {
            mainWindow.webContents.send('backend-ready', { 
                port: backendPort,
                logs: backendLogs,
                error: error.message
            });
        });
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

// IPC: Backend hazır mı kontrol et
ipcMain.handle('check-backend-health', async () => {
    return await checkHealth(backendPort);
});

// IPC: Backend log'larını al (debug için)
ipcMain.handle('get-backend-logs', () => {
    return backendLogs;
});
