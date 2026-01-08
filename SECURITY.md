# 🔒 Security Setup Instructions

## IMPORTANT: Protect Your Credentials!

This project contains sensitive information that should NEVER be committed to git:

### ✅ What's Protected

The following files are automatically excluded from git (via `.gitignore`):

- ✓ `include/config.h` - Contains WiFi credentials and Firebase keys
- ✓ `*-service-account.json` - Firebase admin credentials
- ✓ `.env` files - Environment variables
- ✓ `node_modules/` - Dependencies

### 🚀 Setup for New Developers

If you clone this repository, follow these steps:

#### 1. Create Your Config File

```bash
# Copy the example config
cp include/config.h.example include/config.h
```

#### 2. Update Your Credentials

Edit `include/config.h` with your actual values:

```cpp
// WiFi Credentials
#define WIFI_SSID "Your_Actual_WiFi_Name"
#define WIFI_PASSWORD "Your_Actual_Password"

// Firebase Configuration
#define FIREBASE_HOST "safelabs-monitor-default-rtdb.firebaseio.com"
#define FIREBASE_API_KEY "AIzaSy_your_actual_key_here"
#define FIREBASE_DATABASE_SECRET "your_actual_secret_here"
```

#### 3. Get Firebase Credentials

**Web API Key:**

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project → Project Settings
3. Scroll to "Your apps" → Copy "Web API Key"

**Database Secret:**

1. Firebase Console → Project Settings → Service Accounts
2. Click "Database secrets" at the bottom
3. Copy the secret key

**Service Account (for proxy server):**

1. Firebase Console → Project Settings → Service Accounts
2. Click "Generate new private key"
3. Save as `firebase-service-account.json` (already in .gitignore)

### ⚠️ Never Commit These Files

```bash
# Check what will be committed
git status

# If you see config.h or any .json files, DO NOT commit them!
```

### 🔍 Verify Before Pushing

```bash
# Check .gitignore is working
git check-ignore include/config.h
# Should output: include/config.h

# View what will be pushed
git diff --cached

# If you accidentally added sensitive files:
git reset HEAD include/config.h
git rm --cached firebase-service-account.json
```

### 📋 Checklist Before Pushing

- [ ] `config.h.example` exists with placeholder values
- [ ] `include/config.h` is NOT in git status
- [ ] No API keys visible in `git diff`
- [ ] `.gitignore` includes all sensitive files
- [ ] No `*-service-account.json` files tracked

### 🛡️ Additional Security Tips

1. **Use Environment Variables** for production
2. **Enable Firebase Security Rules** for your database
3. **Rotate credentials** if accidentally exposed
4. **Use separate Firebase projects** for dev/production

### 🆘 If Credentials Are Leaked

1. **Immediately revoke** the exposed credentials in Firebase Console
2. **Generate new keys** and update your local `config.h`
3. **Remove sensitive data from git history**:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch include/config.h" \
     --prune-empty --tag-name-filter cat -- --all
   ```
4. **Force push** (if repository is private and you have permission)

---

## Ready to Push? ✅

If you've verified everything:

```bash
git add .
git commit -m "Add ESP32 Firebase integration"
git push origin main
```

Your credentials are safe! 🔐
