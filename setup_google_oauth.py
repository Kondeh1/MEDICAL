#!/usr/bin/env python
"""
Interactive Google OAuth Setup Script
"""
import os
import sys
import django
from dotenv import load_dotenv

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    django.setup()

def check_env_file():
    """Check if .env file exists and has Google OAuth credentials"""
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        return False, False
    
    load_dotenv()
    
    client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    has_client_id = bool(client_id and client_id != 'your-google-client-id-here')
    has_client_secret = bool(client_secret and client_secret != 'your-google-client-secret-here')
    
    return has_client_id, has_client_secret

def create_env_file():
    """Create .env file if it doesn't exist"""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return
    
    print("Creating .env file...")
    with open('.env.example', 'r') as f:
        content = f.read()
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print("✅ .env file created from .env.example")

def update_env_credentials():
    """Guide user to update credentials in .env file"""
    print("\n" + "="*50)
    print("📝 GOOGLE OAUTH CREDENTIALS SETUP")
    print("="*50)
    
    print("\n📋 IMPORTANT: You need REAL Google OAuth credentials (not fake/plug numbers)")
    print("To get REAL Google OAuth credentials:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable the Google+ API")
    print("4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client IDs'")
    print("5. Set application type to 'Web application'")
    print("6. Add authorized redirect URIs (EXACTLY as shown):")
    print("   - http://127.0.0.1:8006/auth/google/login/callback/")
    print("   - http://localhost:8006/auth/google/login/callback/")
    print("7. Copy the REAL Client ID and Client Secret (not placeholder values)")
    print("   ❌ Wrong: 1234567890-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com")
    print("   ✅ Right: 1234567890-realactualidfromgoogle.apps.googleusercontent.com")
    
    input("\nPress Enter after you've obtained your credentials...")
    
    client_id = input("Enter your Google Client ID: ").strip()
    client_secret = input("Enter your Google Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Both Client ID and Client Secret are required!")
        return False
    
    # Update .env file
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    with open('.env', 'w') as f:
        for line in lines:
            if line.startswith('GOOGLE_CLIENT_ID='):
                f.write(f'GOOGLE_CLIENT_ID={client_id}\n')
            elif line.startswith('GOOGLE_CLIENT_SECRET='):
                f.write(f'GOOGLE_CLIENT_SECRET={client_secret}\n')
            else:
                f.write(line)
    
    print("✅ Credentials updated in .env file!")
    return True

def create_social_app():
    """Create/update SocialApp in database"""
    print("\nCreating/updating Google SocialApp in database...")
    
    from allauth.socialaccount.models import SocialApp
    from django.contrib.sites.models import Site
    
    # Load updated environment variables
    load_dotenv()
    
    client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    # Get or create site
    site, _ = Site.objects.get_or_create(
        domain='127.0.0.1:8006',
        defaults={'name': 'Local Development'}
    )
    
    # Create or update SocialApp
    app, created = SocialApp.objects.update_or_create(
        provider='google',
        defaults={
            'name': 'Google OAuth',
            'client_id': client_id,
            'secret': client_secret,
            'key': '',
        }
    )
    
    # Associate with site
    if site not in app.sites.all():
        app.sites.add(site)
    
    action = "created" if created else "updated"
    print(f"✅ Google SocialApp {action} successfully!")
    print(f"   App ID: {app.id}")
    print(f"   Client ID: {app.client_id[:20]}...")
    return True

def main():
    """Main setup function"""
    print("🚀 Google OAuth Setup Assistant")
    print("="*40)
    
    # Setup Django
    try:
        setup_django()
        print("✅ Django environment ready")
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False
    
    # Check/create .env file
    create_env_file()
    
    # Check current credentials
    has_client_id, has_client_secret = check_env_file()
    
    if not has_client_id or not has_client_secret:
        print("\n⚠️  Missing Google OAuth credentials in .env file")
        if not update_env_credentials():
            return False
    else:
        print("✅ Google OAuth credentials found in .env file")
    
    # Create SocialApp
    if not create_social_app():
        return False
    
    print("\n" + "="*50)
    print("🎉 SETUP COMPLETE!")
    print("="*50)
    print("\nNext steps:")
    print("1. Start your Django server: python manage.py runserver 8006")
    print("2. Go to http://127.0.0.1:8006/accounts/login/")
    print("3. Click the 'Continue with Google' button")
    print("4. Test the Google login functionality")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            print("\n✅ Google OAuth setup completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Google OAuth setup failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)