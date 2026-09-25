# 🚀 How to Get REAL Google OAuth Credentials

## ⚠️ IMPORTANT
The current setup uses placeholder credentials which will NOT work for actual Google authentication. You need real credentials from Google Cloud Console.

## 📝 Step-by-Step Guide

### 1. Go to Google Cloud Console
- Visit: https://console.cloud.google.com/
- Sign in with your Google account

### 2. Create a New Project (or Select Existing)
- Click the project dropdown at the top
- Click "New Project"
- Enter project name (e.g., "Telemedicine App")
- Click "Create"

### 3. Enable Google+ API
- In the left sidebar, click "APIs & Services" → "Library"
- Search for "Google+ API"
- Click on it and then click "Enable"

### 4. Create OAuth 2.0 Credentials
- Go to "APIs & Services" → "Credentials"
- Click "Create Credentials" → "OAuth 2.0 Client IDs"
- If prompted, configure the OAuth consent screen:
  - User Type: External
  - App name: Telemedicine App
  - User support email: Your email
  - Developer contact information: Your email
  - Click "Save and Continue" through all steps

### 5. Configure OAuth Client
- Application type: Web application
- Name: Telemedicine App OAuth
- **Authorized redirect URIs** (IMPORTANT - must match exactly):
  ```
  http://127.0.0.1:8006/auth/google/login/callback/
  http://localhost:8006/auth/google/login/callback/
  ```
- Click "Create"

### 6. Get Your Credentials
- After creation, you'll see:
  - **Client ID** (looks like: `1234567890-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com`)
  - **Client Secret** (looks like: `GOCSPX-AbCdEfGhIjKlMnOpQrStUvWxYz123`)
- Copy both values

### 7. Update Your .env File
Replace the placeholder values in your `.env` file:

```env
GOOGLE_CLIENT_ID=your-real-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-real-client-secret-here
```

### 8. Update Database Configuration
Run this command to update the SocialApp in your database:
```bash
python create_google_social_app.py
```

### 9. Test the Setup
1. Start your Django server: `python manage.py runserver 8006`
2. Go to: http://127.0.0.1:8006/accounts/login/
3. Click "Continue with Google"
4. You should now see the real Google OAuth flow!

## 🔧 Troubleshooting

**If you still get "Missing required parameter: client_id":**
- Double-check that your `.env` file has the correct real credentials
- Verify the SocialApp was updated by running the verification script:
  ```bash
  python verify_google_oauth.py
  ```
- Restart your Django development server after updating credentials

**Common Issues:**
1. Using placeholder/fake credentials instead of real ones
2. Redirect URIs don't match exactly (including trailing slash)
3. Not enabling the Google+ API
4. OAuth consent screen not configured properly

## 🎯 Quick Verification
After setting up real credentials, run:
```bash
python verify_google_oauth.py
```

This should show:
- ✅ GOOGLE_CLIENT_ID: SET (with your real client ID)
- ✅ GOOGLE_CLIENT_SECRET: SET (with your real secret)
- ✅ SocialApp exists in database with real credentials

The Google login should then work properly!