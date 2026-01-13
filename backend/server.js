/**
 * SafeLabs Backend Server
 * Implements PRD Section 6.4 (Energy Automation) & Section 10 (Logging)
 */

const express = require('express');
const cors = require('cors');
const admin = require('firebase-admin');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Initialize Firebase
try {
  // Try loading service account if available
  const serviceAccount = require('./firebase-service-account.json');
  
  // Clean up database URL if quotes are included by accident
  let dbUrl = process.env.FIREBASE_DATABASE_URL;
  if (dbUrl && (dbUrl.startsWith('"') || dbUrl.startsWith("'"))) {
    dbUrl = dbUrl.slice(1, -1);
  }

  admin.initializeApp({
    credential: admin.credential.cert(serviceAccount),
    databaseURL: dbUrl
  });
  console.log('✓ Firebase Admin initialized');
} catch (error) {
  console.warn('⚠ Firebase Setup skipped (missing credentials file). Backend running in API-only mode.');
}

// --- API ROUTES ---

// 1. Get Logged Events (PRD Sec 10)
app.get('/api/devices/:deviceId/events', async (req, res) => {
  try {
    const { deviceId } = req.params;
    const limit = parseInt(req.query.limit) || 50;
    const db = admin.database();
    
    // Fetch logs from /events node
    const snapshot = await db.ref(`/events/${deviceId}`)
      .orderByChild('timestamp')
      .limitToLast(limit)
      .once('value');
    
    res.json(snapshot.val() || {});
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// 2. Control AC with Audit Logging
app.post('/api/labs/:deviceId/ac', async (req, res) => {
  try {
    const { deviceId } = req.params;
    const { status, source } = req.body; // source: 'dashboard', 'auto', 'api'
    const db = admin.database();
    
    // Set actual hardware status
    await db.ref(`/labs/${deviceId}/ac`).set(Boolean(status));
    
    // Create Audit Log
    await db.ref(`/events/${deviceId}`).push({
      type: 'ACTION',
      message: `AC turned ${status ? 'ON' : 'OFF'}`,
      source: source || 'API',
      timestamp: admin.database.ServerValue.TIMESTAMP
    });

    res.json({ success: true, state: status });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// --- AUTOMATION ENGINE (PRD Sec 6.4) ---
// Runs in background to enforce energy rules

const MONITOR_INTERVAL = 10000; // Check every 10s
const INACTIVITY_THRESHOLD = 30 * 1000; // 30s for Demo (Real world: 15 mins)

// In-memory state tracking
const automationState = {}; 

function startAutomationEngine() {
  if (admin.apps.length === 0) return;

  console.log('✓ Automation Engine: STARTED');
  
  setInterval(async () => {
    try {
      const db = admin.database();
      // Monitor multiple devices/labs
      const devices = [
        process.env.DEFAULT_DEVICE_ID || 'sensor_node_01',
        'sensor_node_02',
        'sensor_node_03'
      ];
      
      for (const deviceId of devices) {
        // Check if we can connect to DB
        if (!db) continue; 

        // Fetch latest state
        const [dataSnap, acSnap] = await Promise.all([
          db.ref(`/devices/${deviceId}/latest`).once('value'),
          db.ref(`/labs/${deviceId}/ac`).once('value')
        ]);

      if (!dataSnap.exists()) continue;

      const data = dataSnap.val();
      const acIsOn = acSnap.val();
      const now = Date.now();

      // Track motion history
      if (!automationState[deviceId]) {
        automationState[deviceId] = { lastMotion: now, lastAlert: 0 };
      }
      if (data.motion_detected) {
        automationState[deviceId].lastMotion = now;
      }

      const msSinceMotion = now - automationState[deviceId].lastMotion;

      // RULE 1: Auto-off AC if empty (Energy Logic)
      if (acIsOn && msSinceMotion > INACTIVITY_THRESHOLD) {
        console.log(`[AUTO] Turning OFF AC for ${deviceId} (Inactive for ${Math.floor(msSinceMotion/1000)}s)`);
        
        // Perform Action
        await db.ref(`/labs/${deviceId}/ac`).set(false);
        
        // Log "Auto-Action"
        await db.ref(`/events/${deviceId}`).push({
          type: 'AUTO_ACTION',
          message: 'AC turned OFF due to inactivity',
          details: `${Math.floor(msSinceMotion/1000)}s without motion`,
          timestamp: admin.database.ServerValue.TIMESTAMP
        });
      }

      // RULE 2: Critical Temperature Alert (Safety Logic)
      if (data.temperature > 30 && (now - automationState[deviceId].lastAlert > 300000)) {
        await db.ref(`/events/${deviceId}`).push({
           type: 'CRITICAL_ALERT',
           message: `Critical Temperature: ${data.temperature}°C`,
           timestamp: admin.database.ServerValue.TIMESTAMP
        });
        automationState[deviceId].lastAlert = now;
      }
      }  // End of device loop

    } catch (err) {
      console.error('Automation Loop Error:', err.message);
    }
  }, MONITOR_INTERVAL);
}

// Start Engine delayed to allow DB init
setTimeout(startAutomationEngine, 3000);

// Basic Health Check
app.get('/health', (req, res) => res.json({ status: 'ok', service: 'SafeLabs Backend' }));

app.listen(PORT, () => {
  console.log(`\nSafeLabs Backend Active on Port ${PORT}`);
  console.log(`- Automation Engine: Ready`);
  console.log(`- Audit Logging: Ready`);
});
