# 🔑 How to Get Your Firebase API Key

## Quick Steps:

### 1. Go to Firebase Console

Visit: https://console.firebase.google.com/project/safelabs-monitor/settings/general

### 2. Find Your Web API Key

- Navigate to **Project Settings** (gear icon)
- Scroll down to **"Your apps"** section
- Look for **Web API Key** under the web app configuration
- Copy the value (starts with `AIzaSy...`)

### 3. Update config.h

Replace this line in `include/config.h`:

```cpp
#define FIREBASE_API_KEY "AIzaSyDkVZ5wqFp8vqXn6hLJZk_YourActualAPIKey"
```

With your actual key:

```cpp
#define FIREBASE_API_KEY "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX"  // Your actual key
```

---

## What Got Fixed:

### ✅ Error 1: Variable Name Conflict

**Problem:** Global variable `config` conflicted with Firebase's config usage
**Solution:** Renamed to `fbConfig` throughout the code

### ✅ Error 2: Missing API Key

**Problem:** Only had database secret, but library also needs Web API Key
**Solution:** Added separate `FIREBASE_API_KEY` definition

### ✅ Error 3: Incorrect Authentication Method

**Problem:** Used email/password auth which wasn't needed
**Solution:** Now uses database secret (legacy token) for RTDB authentication

---

## Current Configuration:

```cpp
// What you have now:
#define FIREBASE_HOST "safelabs-monitor-default-rtdb.firebaseio.com"
#define FIREBASE_API_KEY "YOUR_WEB_API_KEY"           // ← Add this!
#define FIREBASE_DATABASE_SECRET "oN56PgK..."          // ✓ Already have this
```

---

## Firebase Console Navigation:

1. **Project Settings** → **General** tab → Scroll to "Your apps"
2. Under "SDK setup and configuration"
3. Select "Config" radio button
4. Copy the `apiKey` value

Example from Firebase Console:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXX", // ← This one!
  authDomain: "safelabs-monitor.firebaseapp.com",
  databaseURL: "https://safelabs-monitor-default-rtdb.firebaseio.com",
  projectId: "safelabs-monitor",
  // ...
};
```

---

## Alternative: If You Don't Want to Use API Key

If you prefer simpler setup for testing, you can modify `main.cpp`:

```cpp
// In initFirebase() function, replace with:
fbConfig.database_url = FIREBASE_HOST;
fbConfig.signer.tokens.legacy_token = FIREBASE_DATABASE_SECRET;

// Remove this line:
// fbConfig.api_key = FIREBASE_API_KEY;
```

Then in `config.h`, you only need:

```cpp
#define FIREBASE_HOST "safelabs-monitor-default-rtdb.firebaseio.com"
#define FIREBASE_DATABASE_SECRET "oN56PgK..."
```

⚠️ **Note:** Using only database secret is simpler but less secure. For production, use proper authentication with API key + Auth.

---

## Test After Configuration:

1. Update the API key in `config.h`
2. Build: `pio run`
3. Run in Wokwi or upload to ESP32
4. Check serial monitor for: `✓ Firebase Ready!`
5. Verify data in Firebase Console

---

## Still Having Issues?

### Enable Firebase Debug Mode:

Add this in `setup()` before `Firebase.begin()`:

```cpp
// Enable Firebase debugging
Firebase.setDebugLevel("info");
Serial.setDebugOutput(true);
```

This will show detailed connection logs to help troubleshoot!
