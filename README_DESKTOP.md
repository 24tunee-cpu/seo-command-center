# SEO Cyber Command Center - Desktop Edition

**Standalone Windows Application (.exe)** - No Docker, No MongoDB, No Redis required.

## 🎯 What Changed?

| Component | Before (Web) | After (Desktop) |
|-----------|--------------|-----------------|
| Database | MongoDB Atlas | SQLite Local .db |
| Cache | Redis | In-Memory |
| Backend | FastAPI (Docker) | FastAPI (.exe) |
| Frontend | Next.js (Vercel) | Next.js (Electron) |
| Deployment | Cloud Server | Single .exe File |

## 📦 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Windows 10/11

### Build Instructions

```powershell
# Run the automated build script
.\build.ps1

# Or manually:

# 1. Build Backend
cd backend
pyinstaller backend.spec --clean

# 2. Build Frontend
cd ..\frontend
npm install
npm run build

# 3. Package with Electron
cd ..
npm install
npm run build:win
```

### Output
```
release/
├── SEO Command Center Setup 1.0.0.exe  # Installer
└── SEO Command Center-1.0.0.exe         # Portable
```

## 🏗️ Architecture

```
Electron Main Process
        │
        ├── Spawns ──► backend.exe (FastAPI + SQLite)
        │                  │
        │                  └── Listens on localhost:29761
        │
        └── Loads ──► frontend/out/index.html
                           │
                           └── Calls localhost:29761/api/...
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `electron/main.js` | Electron entry, spawns Python backend |
| `electron/preload.js` | IPC bridge between frontend & main |
| `backend/backend.spec` | PyInstaller configuration |
| `backend/app/database_sqlite.py` | SQLite ORM models |
| `backend/app/main_desktop.py` | FastAPI entry for desktop |
| `build.ps1` | Automated build script |

## 🔧 Technical Details

### Port Configuration
- Backend: Dynamic port (set by Electron via env PORT)
- Default: 29761 (can be changed in main.js)

### Database Location
- Windows: `%APPDATA%/seo-command-center-desktop/seo_command_center.db`
- Portable: Same folder as .exe

### Process Management
- Backend starts automatically when app opens
- Backend kills cleanly when app closes (SIGTERM → SIGKILL)

## 🚀 Development

```powershell
# Dev mode (hot reload)
npm run dev

# Build for production
npm run build:win
```

## 📚 Build Documentation

- `BUILD_GUIDE_TR.md` - Complete Turkish build guide
- `DEPLOYMENT_GUIDE_TR.md` - Original web deployment guide

## 🐛 Troubleshooting

**Port already in use?**
Change `BACKEND_PORT` in `electron/main.js`

**Backend not starting?**
Check logs: `%APPDATA%/seo-command-center-desktop/logs/`

**Missing icon?**
Add `assets/icon.ico` before building

## 📝 License

MIT License - See original repository

---

**Version:** 1.0.0 | **Platform:** Windows x64 | **Size:** ~100MB
