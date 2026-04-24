# SEO Command Center - Desktop Uygulama Build Rehberi

Bu rehber, web tabanlı SEO Command Center'ın **standalone Windows .exe** uygulamasına dönüştürülmesi için adım adım talimatlar içerir.

## 📋 Mimari Değişiklikler Özeti

```
Web Stack:                     Desktop Stack:
├─ MongoDB (external)   →      ├─ SQLite (local .db file)
├─ Redis (external)     →      ├─ In-Memory / Disabled
├─ FastAPI (Docker)     →      ├─ FastAPI (.exe)
├─ Next.js (Vercel)     →      ├─ Next.js (Static Export)
└─ Browser Access       →      └─ Electron Wrapper

Final Output: SEO-Command-Center-Setup-1.0.0.exe
```

## 🛠️ Gereksinimler

### Python Backend Build
```bash
# PyInstaller
pip install pyinstaller

# UPX (compression) - Optional but recommended
# Download: https://upx.github.io/
# Add to PATH
```

### Node.js/Electron Build
```bash
# Node.js 20+
npm install -g electron electron-builder
```

## 📦 Build Adımları

### Adım 1: SQLite Migration Kontrolü

`app/database_sqlite.py` dosyasının var olduğundan emin olun:
- ✅ SQLAlchemy modelleri tanımlı
- ✅ Local SQLite database desteği
- ✅ Tüm endpoint'ler SQLite uyumlu

### Adım 2: Backend'i .exe'ye Dönüştür (PyInstaller)

```powershell
# Backend dizinine git
cd C:\Users\vedat\CascadeProjects\seo-command-center\backend

# Virtual environment aktive et (varsa)
.\venv\Scripts\activate

# PyInstaller'ı çalıştır
pyinstaller backend.spec --clean

# Output: backend/dist/backend.exe
```

**PyInstaller Config Dosyası (`backend.spec`):**
- `console=False` → Konsol penceresi gösterme
- `upx=True` → UPX ile sıkıştırma
- `hiddenimports` → Tüm bağımlılıklar dahil

### Adım 3: Frontend'i Statik Export Et

```powershell
# Frontend dizinine git
cd C:\Users\vedat\CascadeProjects\seo-command-center\frontend

# Dependencies yükle
npm install

# Statik HTML export et
npm run build

# Output: frontend/out/
```

### Adım 4: Electron ile Paketle

```powershell
# Root dizine git
cd C:\Users\vedat\CascadeProjects\seo-command-center

# Electron dependencies yükle
npm install

# .exe oluştur
npm run build:win

# Output: release/SEO Command Center Setup 1.0.0.exe
```

## 📁 Önemli Dosya Yapısı

```
seo-command-center/
├── electron/
│   ├── main.js          # Electron main process
│   ├── preload.js       # IPC bridge
│   └── ...
├── backend/
│   ├── app/
│   │   ├── main.py      # FastAPI entry
│   │   ├── database_sqlite.py  # SQLite models
│   │   └── ...
│   ├── backend.spec     # PyInstaller config
│   └── dist/
│       └── backend.exe  # Compiled backend
├── frontend/
│   ├── out/             # Static export
│   └── ...
├── assets/
│   ├── icon.ico         # Windows icon
│   └── ...
├── package.json         # Electron builder config
└── release/
    └── SEO Command Center Setup 1.0.0.exe
```

## ⚙️ Electron Yapılandırması

### main.js Özellikleri

1. **Backend Otomatik Başlatma:**
   ```javascript
   // Random port seç
   const BACKEND_PORT = 29761;
   
   // Python executable spawn
   backendProcess = spawn(BACKEND_PATH, [], {
     windowsHide: true,  // Konsol gizli
     env: { PORT: BACKEND_PORT }
   });
   ```

2. **Backend Otomatik Durdurma:**
   ```javascript
   app.on('before-quit', () => {
     backendProcess.kill('SIGTERM');
     // 5sn sonra force kill
   });
   ```

3. **IPC Communication:**
   ```javascript
   // Frontend backend URL'i alır
   ipcMain.handle('get-backend-url', () => {
     return `http://localhost:${BACKEND_PORT}`;
   });
   ```

## 🔧 package.json Build Config

### electron-builder Ayarları

```json
{
  "build": {
    "appId": "com.seocommandcenter.app",
    "productName": "SEO Command Center",
    "asar": true,           // Kodları paketle
    "asarUnpack": [         // Bu dosyaları dışarı çıkar
      "backend.exe"
    ],
    "files": [              // Dahil edilecekler
      "electron/**/*",
      "frontend/out/**/*",
      "backend/dist/backend.exe"
    ],
    "win": {
      "target": [
        "nsis",     // Installer
        "portable"  // Portable .exe
      ]
    }
  }
}
```

## 🚀 Tek Komut ile Build

Her şeyi tek seferde build etmek için:

```powershell
# PowerShell script: build.ps1

# 1. Backend Build
cd backend
pyinstaller backend.spec --clean

# 2. Frontend Build
cd ..\frontend
npm install
npm run build

# 3. Electron Package
cd ..
npm run build:win

Write-Host "Build completed! Check release/ folder"
```

Çalıştır:
```powershell
.\build.ps1
```

## 🐛 Sorun Giderme

### "Backend executable not found"

**Çözüm:** `backend.spec` dosyasının yolunu kontrol edin:
```python
PROJECT_ROOT = os.path.abspath(SPECPATH)
```

### "Port already in use"

**Çözüm:** Electron `main.js` içinde port değiştirin:
```javascript
const BACKEND_PORT = 29761; // Başka bir port deneyin
```

### "Missing DLL files"

**Çözüm:** PyInstaller `--hidden-import` ekle:
```python
hiddenimports=[
    'sqlalchemy.dialects.sqlite',
    'pydantic.deprecated',
]
```

### "Frontend API calls failing"

**Çözüm:** Frontend'de API URL'i dinamik al:
```typescript
// lib/api.ts
const API_BASE = window.electronAPI 
  ? await window.electronAPI.getBackendUrl()
  : process.env.NEXT_PUBLIC_API_URL;
```

## 📊 Boyut Optimizasyonu

| Bileşen | Boyut | Optimizasyon |
|---------|-------|--------------|
| Python Backend | ~150 MB | UPX sıkıştırma: `upx=True` |
| Node Modules | ~200 MB | `asar: true` |
| Frontend | ~5 MB | Statik export |
| **Toplam** | **~100 MB** | Installer sonrası |

## 🔄 Güncelleme Mekanizması

Electron autoUpdater kullanarak OTA güncelleme:

```javascript
const { autoUpdater } = require('electron-updater');

// Güncelleme kontrolü
autoUpdater.checkForUpdatesAndNotify();
```

**GitHub Releases entegrasyonu:**
```json
{
  "build": {
    "publish": {
      "provider": "github",
      "owner": "24tunee-cpu",
      "repo": "seo-command-center"
    }
  }
}
```

## 🎯 Özet Checklist

- [ ] SQLite migration tamamlandı
- [ ] `backend.spec` yapılandırıldı
- [ ] `electron/main.js` backend spawn mantığı eklendi
- [ ] `electron/preload.js` IPC tanımlandı
- [ ] `package.json` electron-builder ayarları yapıldı
- [ ] PyInstaller ile `backend.exe` oluşturuldu
- [ ] Next.js statik export çalıştı (`frontend/out/`)
- [ ] electron-builder ile .exe oluşturuldu
- [ ] Test: Uygulama açılıyor mu?
- [ ] Test: Backend port dinliyor mu?
- [ ] Test: Frontend API'ye bağlanabiliyor mu?

---

**Build Time:** ~5-10 dakika
**Output:** `release/SEO Command Center Setup 1.0.0.exe`
**Runtime Dependencies:** Yok (tümü paket içinde)

Herhangi bir sorun olursa log dosyalarını kontrol edin:
- Windows: `%APPDATA%/seo-command-center-desktop/logs/`
