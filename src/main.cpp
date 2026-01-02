#include <Arduino.h>
#include <DHT.h>       // CHANGE: Use standard Adafruit Library

/* ---------------- GPIO DEFINITIONS ---------------- */
#define DHT_PIN     4      // Safe GPIO for DHT22
#define GAS_PIN     34     // ADC-only pin
#define PIR_PIN     27     // Digital input pin

#define DHTTYPE     DHT22  // Define sensor type

/* ---------------- OBJECTS ---------------- */
DHT dht(DHT_PIN, DHTTYPE); // Initialize library

/* ---------------- SETUP ---------------- */
void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("SafeLabs Virtual Sensor Node Initialized");

  pinMode(PIR_PIN, INPUT);
  analogReadResolution(12);

  dht.begin(); // CHANGE: Standard begin() call
}

/* ---------------- LOOP ---------------- */
void loop() {

  /* ---------- DHT22 ---------- */
  // Reading temperature or humidity takes about 250 milliseconds!
  float h = dht.readHumidity();
  float t = dht.readTemperature();

  // Check if any reads failed and exit early (to try again).
  if (isnan(h) || isnan(t)) {
    Serial.println("DHT22 read failed!");
  } else {
    Serial.print("Temperature (°C): ");
    Serial.println(t);

    Serial.print("Humidity (%): ");
    Serial.println(h);
  }

  /* ---------- GAS SENSOR ---------- */
  int gasRaw = analogRead(GAS_PIN);
  float gasPPM = map(gasRaw, 0, 4095, 200, 1000);

  Serial.print("Gas Level (ppm approx): ");
  Serial.println(gasPPM);

  /* ---------- PIR SENSOR ---------- */
  int motion = digitalRead(PIR_PIN);
  Serial.print("Occupancy: ");
  Serial.println(motion == HIGH ? "Detected" : "None");

  Serial.println("--------------------------------");

  delay(2500);  
}