# Google OAuth 2.0 Setup Guide

## 🚀 Quick Setup (Recommended)

1. **Get Google OAuth Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google+ API
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Set application type to "Web application"
   - Add authorized redirect URIs:
     - `http://127.0.0.1:8006/auth/google/login/callback/`
     - `http://localhost:8006/auth/google/login/callback/`
   - Copy the Client ID and Client Secret

2. **Configure Environment Variables:**
   - Open the `.env` file in your project root
   - Replace these lines with your actual credentials:
     ```
     GOOGLE_CLIENT_ID=your-actual-client-id-here
     GOOGLE_CLIENT_SECRET=your-actual-client-secret-here
     ```

3. **Update Database Configuration:**
   ```bash
   python create_google_social_app.py
   ```

4. **Test the Setup:**
   - Start your Django server: `python manage.py runserver 8006`
   - Go to http://127.0.0.1:8006/accounts/login/
   - Click the "Continue with Google" button

## 🛠️ Alternative: Manual Admin Setup

If you prefer to configure via Django Admin:

1. Go to http://127.0.0.1:8006/admin/
2. Login with your admin credentials
3. Navigate to "Social Applications"
4. Click "Add Social Application"
5. Fill in:
   - Provider: Google
   - Name: Google OAuth
   - Client ID: [your client ID]
   - Secret Key: [your client secret]
   - Sites: Add your site (127.0.0.1:8006)
6. Save

## 🔧 Troubleshooting

**Common Issues:**

1. **"SocialApp.DoesNotExist" Error:**
   - Run `python create_google_social_app.py`
   - Ensure `.env` file has correct credentials

2. **Redirect URI Mismatch:**
   - Check that redirect URIs in Google Console match exactly:
     - `http://127.0.0.1:8006/auth/google/login/callback/`
     - `http://localhost:8006/auth/google/login/callback/`

3. **Invalid Client:**
   - Verify Client ID and Secret are correct
   - Ensure Google+ API is enabled
   - Check that the OAuth consent screen is configured

4. **Environment Variables Not Loading:**
   - Ensure `.env` file is in project root
   - Restart the Django development server
   - Check that `python-dotenv` is installed: `pip install python-dotenv`

## 📁 Project Structure

```
project/
├── .env                  # Your Google OAuth credentials (NOT committed to git)
├── .env.example         # Template for .env file
├── create_google_social_app.py  # Setup script
├── config/
│   └── settings/
│       └── base.py      # Reads GOOGLE_CLIENT_ID/SECRET from .env
└── accounts/
    └── templates/
        └── accounts/
            └── login.html  # Contains Google login button
```

## 🔐 Security Notes

- Never commit your `.env` file to version control
- The `.gitignore` file should exclude `.env`
- Use different credentials for development and production
- Rotate your secrets regularly

## 🎯 Next Steps

After successful setup:
1. Test Google login on your login page
2. Verify user data is properly stored
3. Check that users can access their dashboard
4. Test the logout functionality

Need help? Check the Django allauth documentation: https://django-allauth.readthedocs.io/