# Firebase Integration - SafeLabs Sensor Node

## ✅ What's Been Implemented

Your ESP32 now sends sensor data to Firebase Realtime Database every 5 seconds with:

- Temperature (°C)
- Humidity (%)
- Gas level (PPM)
- Motion detection (boolean)
- Timestamp
- Device ID

## 📁 Data Structure in Firebase

```
/devices
  /sensor_node_01
    /latest              ← Most recent reading (for real-time monitoring)
      - timestamp
      - temperature
      - humidity
      - gas_ppm
      - motion_detected
      - device_id
    /history             ← Historical data (for analysis)
      /{timestamp_1}
      /{timestamp_2}
      ...
```

## 🔧 Next Steps

### 1. **Configure Firebase Database Rules**

Go to your Firebase Console → Realtime Database → Rules and set:

```json
{
  "rules": {
    "devices": {
      ".read": true,
      ".write": true
    }
  }
}
```

⚠️ **Note**: For production, implement proper authentication! Current rules allow public access.

### 2. **Get Your Firebase Database Secret (Optional but Recommended)**

1. Go to Firebase Console → Project Settings → Service Accounts
2. Click "Database secrets" at the bottom
3. Copy the secret key
4. Update `include/config.h` → `FIREBASE_AUTH` with your secret

### 3. **For Real Hardware (Not Wokwi Simulation)**

Update `include/config.h` with your actual WiFi credentials:

```cpp
#define WIFI_SSID "your_actual_wifi_name"
#define WIFI_PASSWORD "your_actual_wifi_password"
```

### 4. **Build and Upload**

```bash
# Build the project
pio run

# Upload to ESP32 (for real hardware)
pio run --target upload

# For Wokwi: Click the green play button
```

## 🌐 Access Your Data

### Via Web Browser:

```
https://safelabs-monitor-default-rtdb.firebaseio.com/devices/sensor_node_01/latest.json
```

### Via Cloud Run (Python example):

```python
import requests

firebase_url = "https://safelabs-monitor-default-rtdb.firebaseio.com"
device_id = "sensor_node_01"

# Get latest reading
response = requests.get(f"{firebase_url}/devices/{device_id}/latest.json")
data = response.json()

print(f"Temperature: {data['temperature']}°C")
print(f"Humidity: {data['humidity']}%")
print(f"Gas: {data['gas_ppm']} ppm")
print(f"Motion: {data['motion_detected']}")
```

### Via Cloud Run (Node.js example):

```javascript
const admin = require("firebase-admin");

admin.initializeApp({
  databaseURL: "https://safelabs-monitor-default-rtdb.firebaseio.com",
});

const db = admin.database();
const ref = db.ref("devices/sensor_node_01/latest");

ref.on("value", (snapshot) => {
  const data = snapshot.val();
  console.log("Latest sensor data:", data);

  // Calculate risk score
  calculateRiskScore(data);
});
```

## 📊 Risk Score Assessment Integration

Your Cloud Run service can:

1. **Listen to Firebase changes** (using Firebase Admin SDK)
2. **Fetch latest data** via REST API
3. **Query historical data** for trend analysis

Example Cloud Run endpoint structure:

```
GET /api/risk-score?device=sensor_node_01
POST /api/analyze-historical?device=sensor_node_01&hours=24
```

## 🔍 Monitoring

### Serial Monitor Output:

```
=================================
SafeLabs Sensor Node - Firebase Integration
=================================

📡 Connecting to WiFi: Wokwi-GUEST
✓ WiFi Connected!
IP Address: 192.168.1.100

🔥 Initializing Firebase...
✓ Firebase Ready!

✓ System Ready - Starting data collection...

🌡️  Temperature: 24.00 °C
💧 Humidity: 40.00 %
☁️  Gas Level: 484.00 ppm
👤 Occupancy: None
📤 Sending data to Firebase...
✓ Data sent successfully!
--------------------------------
```

## 🛠️ Troubleshooting

### WiFi Not Connecting

- Check SSID and password in `config.h`
- Ensure 2.4GHz network (ESP32 doesn't support 5GHz)

### Firebase Connection Failed

- Verify database URL in `config.h`
- Check Firebase rules allow read/write
- Ensure stable internet connection

### Data Not Appearing in Firebase

- Check Firebase Console for error logs
- Verify database URL is correct
- Check Serial Monitor for error messages

## 📝 Customization

### Change Update Interval

Edit `config.h`:

```cpp
#define READING_INTERVAL 5000  // milliseconds (current: 5 seconds)
```

### Add Multiple Devices

Edit `config.h`:

```cpp
#define DEVICE_ID "sensor_node_02"  // Change for each device
```

### Add More Sensors

1. Define new GPIO pins
2. Read sensor values in `loop()`
3. Add fields to JSON in `sendSensorData()`

## 🎯 Production Recommendations

1. **Implement Authentication**: Use Firebase Auth for secure access
2. **Add SSL/TLS Certificates**: For encrypted communication
3. **Implement Data Validation**: Check sensor ranges before sending
4. **Add Retry Logic**: Handle temporary network failures
5. **Optimize Battery**: For battery-powered devices, use deep sleep
6. **Add OTA Updates**: For remote firmware updates
7. **Implement Watchdog Timer**: For automatic recovery from crashes

## 📧 Support

For issues or questions, check:

- Serial Monitor output for debugging
- Firebase Console for data verification
- PlatformIO build logs for compilation errors
