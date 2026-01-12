# SafeLabs – The Autonomous Server & Lab Guardian

**Version:** 1.0 (MVP)  
**Status:** In Development  
**Category:** AI + Cloud + IoT  

SafeLabs is an AI-powered facility monitoring and automation platform designated to protect university computer labs and server rooms from environmental hazards (like overheating or gas leaks) and energy wastage. By combining simulated IoT sensors, real-time cloud data, and Generative AI, SafeLabs provides a "Virtual Facility Manager" that converts raw sensor data into clear, actionable, natural-language insights.

## 📂 Project Structure

This repository contains the full MVP codebase, including the firmware for simulated hardware and the admin dashboard.

- **`src/`**: C++ source code for the ESP32 firmware using the Arduino framework. Handles sensor simulation (Temperature, Humidity, Gas, PIR) and data synchronization with Firebase.
- **`include/`**: Configuration credentials for the firmware.
  - `config.h.example`: Template for Wi-Fi and Firebase credentials.
- **`dashboard.py`**: The Admin Dashboard application built with **Streamlit**. It visualizes real-time data, controls the system (AC simulation), and provides AI insights.
- **`platformio.ini`**: Configuration file for PlatformIO (library dependencies, board settings).
- **`diagram.json` & `wokwi.toml`**: Configuration for running the IoT simulation on [Wokwi](https://wokwi.com).
- **`firebase-service-account.json`** (Required, not included): Credentials for the Python Admin SDK to access Firebase.

## Features (MVP)

1.  **IoT Simulation (ESP32 via Wokwi)**:
    - Simulates environmental sensors: DHT22 (Temp/Humidity), MQ-135 (Gas/Smoke), PIR (Motion).
    - **Smart Firmware Logic**:
      - **Motion Extension**: Simulates realistic 15s activity for every motion trigger.
      - **Local Automation**: Auto-turns OFF AC after 15s of inactivity (no server required).
      - **Security Logging**: Instantly pushes "Security Alert" events to cloud upon detecting entry.
    - Syncs data to Firebase Realtime Database.

2.  **Real-Time Monitoring (Streamlit Dashboard)**:
    - Live updates of critical metrics (Temp, Humidity, Gas, Occupancy).
    - Status alerts for safe/warning/critical conditions.

3.  **AI Virtual Facility Manager**:
    - Powered by **Google Gemini Pro**.
    - Generates natural language risk assessments and action recommendations.

4.  **Energy & Security Automation**:
    - **Energy Saver**: AC turns off automatically when room is empty (Firmware-enforced).
    - **Audit Logs**: Tracks all access events (Motion) and Control Actions (AC On/Off) in the cloud.

## Quick Start Guide

Get SafeLabs up and running in 5 minutes!

### Prerequisites Checklist
- [ ] VS Code with PlatformIO extension
- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed (for backend - optional)
- [ ] Firebase project created at [firebase.google.com](https://firebase.google.com)
- [ ] Git installed

### Step 1: Clone & Install Dependencies

```bash
git clone <repository-url>
cd Hardware

# Install Node.js dependencies (optional - for backend)
npm install

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Configure Firmware (ESP32)

1. Navigate to `include/` folder
2. Copy the config template:
   ```bash
   cp include/config.h.example include/config.h
   ```
3. Edit `include/config.h` with your credentials:
   ```cpp
   #define WIFI_SSID "Wokwi-GUEST"        // For Wokwi simulation
   #define WIFI_PASSWORD ""
   #define FIREBASE_HOST "your-project-id-default-rtdb.firebaseio.com"
   #define FIREBASE_API_KEY "AIzaSy..."
   #define FIREBASE_DATABASE_SECRET "your_secret_here"
   ```
4. Build the project:
   ```bash
   pio run
   ```

### Step 3: Get Firebase Service Account

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project → **Settings** → **Service Accounts**
3. Click **"Generate New Private Key"**
4. Save the JSON file as `firebase-service-account.json` in project root

### Step 4: Configure Dashboard

1. Open `dashboard.py`
2. Update the Firebase URL (around line 100):
   ```python
   'databaseURL': 'https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com'
   ```

### Step 5: Run Everything!

**Terminal 1 - Start Wokwi Simulation:**
- Click the green play button in VS Code Wokwi extension
- Or use Wokwi web simulator with `diagram.json`
- Check serial monitor for "WiFi Connected" and "Firebase Ready" messages

**Terminal 2 - Start Backend (Optional):**
```bash
npm start
```

**Terminal 3 - Start Dashboard:**
```bash
python -m streamlit run dashboard.py
```

### Access Your System

- **Dashboard:** http://localhost:8501
- **Backend API:** http://localhost:3000 (if running)
- **Health Check:** http://localhost:3000/health

## First Time Testing

1. **Verify Wokwi Simulation:**
   - Open serial monitor in VS Code
   - Look for connection success messages
   
2. **Test Dashboard:**
   - Dashboard should show live sensor data updating every 5 seconds
   
3. **Test AC Control:**
   - In dashboard, click "Turn AC ON"
   - Watch the green LED light up in Wokwi simulation

4. **Enable AI Insights (Optional):**
   - Get Gemini API key from [Google AI Studio](https://aistudio.google.com/)
   - Enter it in dashboard sidebar
   - View AI-powered facility recommendations

### 🛡️ Security & Automation Testing

**1. Test Energy Saver (Auto-AC Off)**
- **Turn AC ON** via Dashboard.
- **Click PIR Sensor** once (Serial: *"Motion Triggered! Simulating activity..."*).
- **Wait 30s**:
  - 0-15s: System simulates active motion.
  - 15-30s: System detects inactivity.
  - @ 30s: **Green LED turns OFF** automaticallly.

**2. Test Security Logging**
- **Click PIR Sensor** (after it has been idle).
- Check Serial Monitor for: `🚨 Security Event Logged to Firebase!`
- This creates an instant timestamped entry in the `/events` log for security auditing.

## 🔧 Troubleshooting

### "Firebase not initialized"
- Ensure `firebase-service-account.json` exists in root
- Verify Firebase URL is correct in `dashboard.py`

### "No sensor data available"
- Confirm Wokwi simulation is running
- Check serial monitor for errors
- Verify Firebase Realtime Database rules allow read/write

### "Module not found" errors
- Run `npm install` and `pip install -r requirements.txt`
- Ensure Python 3.8+ and Node.js 18+ are installed

## Additional Documentation

- **[Product Requirements](docs/PRD.txt)** - Project goals and specifications
- **[Firebase Setup Guide](docs/FIREBASE_SETUP.md)** - Detailed Firebase configuration
- **[Dashboard Documentation](docs/DASHBOARD_README.md)** - Dashboard features and usage
- **[Security Guidelines](docs/SECURITY.md)** - Credential management best practices
- **[Contributing](CONTRIBUTING.md)** - How to contribute to the project
- **[Changelog](CHANGELOG.md)** - Version history and updates

## Security Notes

- **Never commit** `config.h` or `firebase-service-account.json`
- Use `.gitignore` to protect sensitive files (already configured)
- For production, implement proper Firebase security rules
- Rotate credentials if accidentally exposed

## Technology Stack

**Firmware:** C++, Arduino Framework, PlatformIO  
**Backend:** Node.js, Express.js, Firebase Admin SDK (optional)  
**Dashboard:** Python, Streamlit, Plotly, Firebase Admin  
**AI:** Google Gemini Pro  
**Cloud:** Firebase Realtime Database  
**Simulation:** Wokwi  

## 📊 Features Overview

### IoT Simulation (ESP32 via Wokwi)
- DHT22 sensor for temperature & humidity
- MQ-135 (potentiometer) for gas/smoke levels
- PIR sensor for motion detection
- LED indicator for AC status
- Real-time sync with Firebase every 5 seconds

### Real-Time Monitoring Dashboard
- Live sensor metrics with historical comparisons
- Color-coded status alerts (Safe/Warning/Critical)
- Auto-refresh every 5 seconds
- Historical data visualization with Plotly charts

### AI Virtual Facility Manager
- Natural language risk assessments
- Action recommendations based on sensor data
- Powered by Google Gemini Pro

### Energy Automation
- Motion-based AC control
- Remote on/off via dashboard
- Energy-saving recommendations

---
*SafeLabs - Making lab safety intelligent and accessible*  
*Built for TechSprint | Version 1.0 MVP*
