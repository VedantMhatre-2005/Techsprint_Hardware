# SafeLabs - Restructured Multi-Lab IoT System

![SafeLabs](https://img.shields.io/badge/SafeLabs-v1.0-blue)
![ESP32](https://img.shields.io/badge/ESP32-Firmware-green)
![Firebase](https://img.shields.io/badge/Firebase-Realtime-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Autonomous Laboratory Monitoring & Safety System** with multi-lab support, smart automation, and real-time Firebase integration.

---

## 📁 New Repository Structure

```
/
├── firmware/                    # Shared ESP32 code
│   ├── src/main.cpp            # Main firmware (supports all labs)
│   ├── include/config.h        # Symlink to active lab config
│   ├── platformio.ini          # PlatformIO configuration
│   ├── lib/                    # Dependencies
│   └── .pio/                   # Build output (auto-generated)
│
├── configs/                     # Lab-specific configurations
│   ├── lab1_config.h           # sensor_node_01
│   ├── lab2_config.h           # sensor_node_02
│   └── lab3_config.h           # sensor_node_03
│
├── simulations/                 # Wokwi circuits
│   ├── lab1/
│   │   ├── diagram.json
│   │   └── wokwi.toml
│   ├── lab2/
│   │   ├── diagram.json
│   │   └── wokwi.toml
│   └── lab3/
│       ├── diagram.json
│       └── wokwi.toml
│
├── backend/
│   ├── server.js               # Node.js automation engine
│   ├── package.json
│   └── .env.example
│
├── dashboard/
│   ├── dashboard.py            # Streamlit monitoring dashboard
│   └── requirements.txt
│
├── docs/                        # Documentation
│
├── build.bat                    # Windows build script
├── build.sh                     # Linux/Mac build script
└── README.md
```

---

## Initial Setup (First Time Only)

Before running the system, you need to configure your credentials:

### 1. Create Lab Configuration Files

```powershell
# Copy template for each lab
Copy-Item configs\config.h.example configs\lab1_config.h
Copy-Item configs\config.h.example configs\lab2_config.h
Copy-Item configs\config.h.example configs\lab3_config.h
```

**Update each file with your Firebase credentials:**
- **FIREBASE_HOST**: Your Firebase Realtime Database URL  
  (e.g., `https://your-project-default-rtdb.firebaseio.com/`)
- **FIREBASE_API_KEY**: Web API Key (Firebase Console → Project Settings → General)
- **FIREBASE_DATABASE_SECRET**: Database Secret (Project Settings → Service Accounts → Database Secrets)
- **DEVICE_ID**: Keep unique per lab
  - `lab1_config.h`: `"sensor_node_01"`
  - `lab2_config.h`: `"sensor_node_02"`
  - `lab3_config.h`: `"sensor_node_03"`

### 2. Get Firebase Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project →  **Project Settings** → **Service Accounts**
3. Click **"Generate New Private Key"**
4. Save as `firebase-service-account.json` and copy to:
   ```powershell
   # Place in root directory first, then copy to subdirectories
   Copy-Item firebase-service-account.json backend\
   Copy-Item firebase-service-account.json dashboard\
   ```

### 3. Create Backend Environment File

```powershell
Copy-Item backend\.env.example backend\.env
# Edit .env with your credentials
```

**Setup Complete!** These files are excluded from Git via `.gitignore` for security.

---

## Quick Start

### 1️ Build Firmware for a Lab

**Windows:**
```powershell
# Build Lab 1
.\build.bat lab1

# Build Lab 2
.\build.bat lab2

# Build all labs
.\build.bat all
```

**Linux/Mac:**
```bash
chmod +x build.sh

# Build Lab 1
./build.sh lab1

# Build all labs
./build.sh all
```

### 2️ Run Wokwi Simulation

1. Open the lab's diagram: `simulations/lab1/diagram.json` (or lab2, lab3)
2. Press `F1` → **"Wokwi: Start Simulator"**
3. All 3 labs can run simultaneously!

### 3️ Start Dashboard

```powershell
cd dashboard
pip install -r requirements.txt
python -m streamlit run dashboard.py
```

**Dashboard Features:**
-  Real-time sensor monitoring for all 3 labs
-  Online/Offline status indicators
-  Empty metrics display when simulator not running
-  Auto-refresh every 5 seconds
-  AI-powered insights using Google Gemini
-  Historical trend visualization

### 4️ Start Backend (Optional)

```powershell
cd backend
npm install
npm start
```

---

## Features

**Single Codebase** - One firmware for all 3 labs  
**Config-Based Labs** - Switch labs by changing config file  
**Automated Builds** - Build scripts for Windows/Linux  
**Shared Simulations** - All labs use same firmware build  
**Multi-Lab Dashboard** - Monitor all 3 labs in one view  
**Smart Automation** - 15s motion + 15s inactivity AC control  
**Security Logging** - Real-time Firebase event tracking  
**Offline Detection** - Dashboard shows when sensors are offline  
**Empty Metrics Display** - Clear visual distinction for inactive simulators  
**Dual Timestamp Support** - Handles both Unix and boot timestamps  
**Auto-Refresh** - Real-time updates every 5 seconds  

---

## How It Works

### Build Process

1. **Select Lab**: Run `build.bat lab1` (or lab2/lab3)
2. **Copy Config**: Script copies `configs/lab1_config.h` → `firmware/include/config.h`
3. **Build Firmware**: PlatformIO compiles with selected config
4. **Output**: `firmware/.pio/build/esp32doit-devkit-v1/firmware.bin`
5. **Simulate**: All 3 simulations point to same firmware binary

### Multi-Lab Deployment

```
Lab 1 (sensor_node_01) ──┐
Lab 2 (sensor_node_02) ──┼─→ Firebase ─→ Dashboard
Lab 3 (sensor_node_03) ──┘              ↓
                                      Backend
```

Each lab writes to its own Firebase path:
- `/devices/sensor_node_01/latest`
- `/devices/sensor_node_02/latest`
- `/devices/sensor_node_03/latest`

---


## Development Workflow

### Adding a New Lab (Lab 4)

1. Create config: `configs/lab4_config.h`
2. Set `DEVICE_ID "sensor_node_04"`
3. Create simulation: `simulations/lab4/diagram.json`
4. Build: `.\build.bat lab4`

No changes to firmware needed!

---

## Testing

**Run all 3 labs simultaneously:**

1. Build firmware: `.\build.bat all`
2. Open 3 VS Code windows
3. In each window:
   - Open `simulations/lab1/diagram.json` (or lab2, lab3)
   - Press F1 → "Wokwi: Start Simulator"
4. All 3 will push to Firebase independently!

**Dashboard Status Indicators:**
- 🟢 **ONLINE**: Sensor active, real-time values displayed
- ⚫ **OFFLINE**: Simulator stopped, empty metrics shown (-- °C, -- %, -- ppm)
- Offline detection triggers after 30 seconds of no updates
- Auto-refresh continues even when offline (every 5s)

**Serial Monitor Verification:**
- Look for: `✓ Data sent successfully!` every 5 seconds
- If offline: Check WiFi connection, Firebase rules, or rebuild firmware

---

## 🔒 Security & Credentials

**Protected Files (excluded from Git):**
- `firebase-service-account.json` - Firebase Admin SDK credentials
- `configs/lab1_config.h`, `lab2_config.h`, `lab3_config.h` - WiFi passwords & API keys
- `backend/.env` - Environment variables
- `firmware/include/config.h` - Generated during build

**Template Files (safe to commit):**
- `configs/config.h.example` - Lab config template
- `firebase-service-account.json.example` - Firebase credential template
- `backend/.env.example` - Backend environment template


## Firebase Structure

```
devices/
  ├── sensor_node_01/
  │   ├── latest/
  │   └── history/
  ├── sensor_node_02/
  │   ├── latest/
  │   └── history/
  └── sensor_node_03/
      ├── latest/
      └── history/

labs/
  ├── sensor_node_01/ac
  ├── sensor_node_02/ac
  └── sensor_node_03/ac

events/
  ├── sensor_node_01/
  ├── sensor_node_02/
  └── sensor_node_03/
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Credits

**Cloudbuds** - Autonomous Lab Safety System  
Built with ESP32, Firebase, Node.js, Streamlit & Wokwi
