#include <Arduino.h>
#include <DHT.h>
#include <WiFi.h>
#include <Firebase_ESP_Client.h>
#include "addons/TokenHelper.h" // Provide the token generation process info
#include "addons/RTDBHelper.h"  // Provide the RTDB payload printing info
#include "config.h"

/* ---------------- GPIO DEFINITIONS ---------------- */
#define DHT_PIN 4  // Safe GPIO for DHT22
#define GAS_PIN 34 // ADC-only pin
#define PIR_PIN 27 // Digital input pin

// NEW: AC Control and Avg definitions
#define LED_AC_PIN 26 // LED for AC status
#define AVG_TEMP_PIN 32 // Potentiometer for Avg Temp
#define AVG_HUM_PIN 33  // Potentiometer for Avg Humidity

#define DHTTYPE DHT22 // Define sensor type

/* ---------------- OBJECTS ---------------- */
DHT dht(DHT_PIN, DHTTYPE);
FirebaseData fbdo;         // For sending data
FirebaseData fbdo_control; // For reading AC control
FirebaseAuth auth;
FirebaseConfig fbConfig;

/* ---------------- VARIABLES ---------------- */
unsigned long lastSendTime = 0;
unsigned long lastACCheckTime = 0;
unsigned long lastMotionTime = 0; // Track last motion
bool firebaseReady = false;
bool isACOn = false; // Local AC state

// AUTOMATION SETTINGS
const unsigned long MOTION_SIMULATION_DURATION = 15000; // 15 seconds of forced motion
const unsigned long AUTOMATION_TIMEOUT = 15000; // 15 seconds of inactivity before OFF
unsigned long motionSimulationStartTime = 0;
bool isSimulatingMotion = false;

/* ---------------- FUNCTION PROTOTYPES ---------------- */
void connectWiFi();
void initFirebase();
void sendSensorData(float temp, float humidity, float gas, bool motion, float avgTemp, float avgHum);
void checkACStatus();

/* ---------------- SETUP ---------------- */
void setup()
{
  Serial.begin(115200);
  delay(2000);

  Serial.println("\n=================================");
  Serial.println("SafeLabs Sensor Node - Firebase Integration");
  Serial.println("=================================\n");

  // Initialize sensors
  pinMode(PIR_PIN, INPUT);
  pinMode(LED_AC_PIN, OUTPUT);
  pinMode(AVG_TEMP_PIN, INPUT);
  pinMode(AVG_HUM_PIN, INPUT);
  
  analogReadResolution(12);
  dht.begin();
  
  // Default AC OFF
  digitalWrite(LED_AC_PIN, LOW);

  // Connect to WiFi
  connectWiFi();

  // Initialize Firebase
  initFirebase();

  Serial.println("\n✓ System Ready - Starting data collection...\n");
}

/* ---------------- LOOP ---------------- */
void loop()
{
  
  // 1. Check AC Status (Every 1 second)
  // We use a separate FirebaseData object to avoid conflict
  if (millis() - lastACCheckTime > 1000)
  {
    lastACCheckTime = millis();
    checkACStatus();
  }

  // 2. Send Sensor Data (Every READING_INTERVAL)
  if (millis() - lastSendTime < READING_INTERVAL)
  {
    return;
  }
  lastSendTime = millis();

  /* ---------- DHT22 ---------- */
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  if (isnan(h) || isnan(t))
  {
    Serial.println("❌ DHT22 read failed!");
    h = 0.0;
    t = 0.0;
  }
  else
  {
    Serial.print("🌡️  Temperature: ");
    Serial.print(t);
    Serial.println(" °C");

    Serial.print("💧 Humidity: ");
    Serial.print(h);
    Serial.println(" %");
  }

  /* ---------- GAS SENSOR ---------- */
  int gasRaw = analogRead(GAS_PIN);
  float gasPPM = map(gasRaw, 0, 4095, 200, 1000);

  Serial.print("☁️  Gas Level: ");
  Serial.print(gasPPM);
  Serial.println(" ppm");

  /* ---------- PIR SENSOR ---------- */
  int motion = digitalRead(PIR_PIN);
  bool motionDetected = (motion == HIGH);

  // LOGIC: If real PIR is triggered, start the 15-second simulation timer
  if (motionDetected) {
    if (!isSimulatingMotion) {
      Serial.println("🏃 Motion Triggered! Simulating activity for 15 seconds...");
      isSimulatingMotion = true;
      motionSimulationStartTime = millis();
      
      // IMMEDIATE SECURITY LOG ENTRY
      if (firebaseReady) {
        char eventPath[100];
        sprintf(eventPath, "/events/%s", DEVICE_ID);
        FirebaseJson eventJson;
        eventJson.set("type", "SECURITY_ALERT");
        eventJson.set("message", "Motion Detected in Lab");
        eventJson.set("source", "PIR_SENSOR");
        eventJson.set("timestamp", millis() / 1000); // Simple timestamp
        Firebase.RTDB.pushJSON(&fbdo, eventPath, &eventJson);
        Serial.println("🚨 Security Event Logged to Firebase!");
      }
    }
    // Always update last motion time while triggered
    lastMotionTime = millis();
  }

  // LOGIC: Keep "motionDetected" true if we are in the 15-second simulation window
  if (isSimulatingMotion) {
    if (millis() - motionSimulationStartTime < MOTION_SIMULATION_DURATION) {
      motionDetected = true; // FORCE motion to be true
      lastMotionTime = millis(); // Keep resetting the inactivity timer
    } else {
      isSimulatingMotion = false;
      Serial.println("✋ Motion Simulation Ended. Starting Inactivity Timer...");
    }
  }

  // Energy Automation: Auto-turn OFF AC if no motion for X time (15s)
  if (isACOn && (millis() - lastMotionTime > AUTOMATION_TIMEOUT)) {
      Serial.println("📉 Auto-Optimization: Turning OFF AC due to inactivity");
      
      // 1. Turn off Local AC
      digitalWrite(LED_AC_PIN, LOW);
      isACOn = false;

      // 2. Sync to Firebase (so Dashboard updates)
      if (firebaseReady) {
        char path[100];
        sprintf(path, "/labs/%s/ac", DEVICE_ID);
        Firebase.RTDB.setBool(&fbdo_control, path, false);
      }
  }

  Serial.print("👤 Occupancy: ");
  Serial.println(motionDetected ? "Detected (Sim)" : "None");

  /* ---------- AVERAGE PARAMETERS (SIMULATED) ---------- */
  // Read Potentiometers for Avg Temp and Hum
  int avgTempRaw = analogRead(AVG_TEMP_PIN);
  int avgHumRaw = analogRead(AVG_HUM_PIN);

  // Map to reasonable values
  // Temp: 10C to 40C
  float avgTemp = map(avgTempRaw, 0, 4095, 1000, 4000) / 100.0; 
  // Hum: 20% to 90%
  float avgHum = map(avgHumRaw, 0, 4095, 2000, 9000) / 100.0;

  Serial.print("🌡️  Avg Temp (1h): ");
  Serial.print(avgTemp);
  Serial.println(" °C");
  
  Serial.print("💧 Avg Hum (1h): ");
  Serial.print(avgHum);
  Serial.println(" %");

  /* ---------- SEND TO FIREBASE ---------- */
  sendSensorData(t, h, gasPPM, motionDetected, avgTemp, avgHum);

  Serial.println("--------------------------------\n");
}

/* ---------------- WIFI CONNECTION ---------------- */
void connectWiFi()
{
  Serial.print("📡 Connecting to WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20)
  {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.println("\n✓ WiFi Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  }
  else
  {
    Serial.println("\n❌ WiFi Connection Failed!");
  }
}

/* ---------------- FIREBASE INITIALIZATION ---------------- */
void initFirebase()
{
  Serial.println("\n🔥 Initializing Firebase...");

  // Assign the API key
  fbConfig.api_key = FIREBASE_API_KEY;

  // Assign the database URL
  fbConfig.database_url = FIREBASE_HOST;

  // Assign the database secret
  fbConfig.signer.tokens.legacy_token = FIREBASE_DATABASE_SECRET;

  // Initialize Firebase
  Firebase.begin(&fbConfig, &auth);
  Firebase.reconnectWiFi(true);

  // Set database read/write timeout
  fbdo.setResponseSize(4096);
  fbdo_control.setResponseSize(4096);

  firebaseReady = true;
  Serial.println("✓ Firebase Ready!");
}

/* ---------------- CHECK AC STATUS ---------------- */
void checkACStatus()
{
  if (!firebaseReady || WiFi.status() != WL_CONNECTED) return;

  // Path: /labs/{DEVICE_ID}/ac
  char path[100];
  sprintf(path, "/labs/%s/ac", DEVICE_ID);

  if (Firebase.RTDB.getBool(&fbdo_control, path))
  {
    bool newAcState = fbdo_control.boolData();
    if (newAcState != isACOn) {
        Serial.print("🔄 AC Status Changed to: ");
        Serial.println(newAcState ? "ON" : "OFF");
        isACOn = newAcState;
        digitalWrite(LED_AC_PIN, isACOn ? HIGH : LOW);
        
        // Reset timer when manually turned ON so it doesn't immediately turn off
        if (isACOn) lastMotionTime = millis(); 
    }
  }
}

/* ---------------- SEND DATA TO FIREBASE ---------------- */
void sendSensorData(float temp, float humidity, float gas, bool motion, float avgTemp, float avgHum)
{

  if (!firebaseReady || WiFi.status() != WL_CONNECTED)
  {
    Serial.println("❌ Cannot send data - Firebase not ready or WiFi disconnected");
    return;
  }

  Serial.println("📤 Sending data to Firebase...");

  // Create timestamp
  unsigned long timestamp = millis() / 1000; 
  String timestampStr = String(timestamp);

  // Path: /devices/sensor_node_01/latest
  char path[100];
  sprintf(path, "/devices/%s/latest", DEVICE_ID);

  // Create JSON object
  FirebaseJson json;
  json.set("timestamp", timestamp);
  json.set("temperature", temp);
  json.set("humidity", humidity);
  json.set("gas_ppm", gas);
  json.set("motion_detected", motion);
  json.set("avg_temp_1h", avgTemp);
  json.set("avg_hum_1h", avgHum);
  json.set("device_id", DEVICE_ID);

  // Send to Firebase
  if (Firebase.RTDB.setJSON(&fbdo, path, &json))
  {
    Serial.println("✓ Data sent successfully!");

    // Also store in history
    char historyPath[100];
    sprintf(historyPath, "/devices/%s/history/%s", DEVICE_ID, timestampStr.c_str());
    Firebase.RTDB.setJSON(&fbdo, historyPath, &json);
  }
  else
  {
    Serial.println("❌ Failed to send data");
    Serial.print("Reason: ");
    Serial.println(fbdo.errorReason());
  }
}
