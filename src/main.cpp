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

#define DHTTYPE DHT22 // Define sensor type

/* ---------------- OBJECTS ---------------- */
DHT dht(DHT_PIN, DHTTYPE);
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig fbConfig;

/* ---------------- VARIABLES ---------------- */
unsigned long lastSendTime = 0;
bool firebaseReady = false;

/* ---------------- FUNCTION PROTOTYPES ---------------- */
void connectWiFi();
void initFirebase();
void sendSensorData(float temp, float humidity, float gas, bool motion);

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
  analogReadResolution(12);
  dht.begin();

  // Connect to WiFi
  connectWiFi();

  // Initialize Firebase
  initFirebase();

  Serial.println("\n✓ System Ready - Starting data collection...\n");
}

/* ---------------- LOOP ---------------- */
void loop()
{

  // Check if it's time to send data
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

  Serial.print("👤 Occupancy: ");
  Serial.println(motionDetected ? "Detected" : "None");

  /* ---------- SEND TO FIREBASE ---------- */
  sendSensorData(t, h, gasPPM, motionDetected);

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

  // Assign the API key (get from Firebase Console → Project Settings)
  fbConfig.api_key = FIREBASE_API_KEY;

  // Assign the database URL
  fbConfig.database_url = FIREBASE_HOST;

  // Assign the database secret for authentication
  fbConfig.signer.tokens.legacy_token = FIREBASE_DATABASE_SECRET;

  // Initialize Firebase
  Firebase.begin(&fbConfig, &auth);
  Firebase.reconnectWiFi(true);

  // Set database read/write timeout (optional)
  fbdo.setResponseSize(4096);

  firebaseReady = true;
  Serial.println("✓ Firebase Ready!");
}

/* ---------------- SEND DATA TO FIREBASE ---------------- */
void sendSensorData(float temp, float humidity, float gas, bool motion)
{

  if (!firebaseReady || WiFi.status() != WL_CONNECTED)
  {
    Serial.println("❌ Cannot send data - Firebase not ready or WiFi disconnected");
    return;
  }

  Serial.println("📤 Sending data to Firebase...");

  // Create timestamp
  unsigned long timestamp = millis() / 1000; // seconds since boot
  String timestampStr = String(timestamp);

  // Create the path: /devices/sensor_node_01/readings/{timestamp}
  char path[100];
  sprintf(path, "/devices/%s/latest", DEVICE_ID);

  // Create JSON object
  FirebaseJson json;
  json.set("timestamp", timestamp);
  json.set("temperature", temp);
  json.set("humidity", humidity);
  json.set("gas_ppm", gas);
  json.set("motion_detected", motion);
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