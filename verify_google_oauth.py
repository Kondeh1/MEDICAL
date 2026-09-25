#!/usr/bin/env python
"""
Verification script for Google OAuth setup
"""
import os
import django
from dotenv import load_dotenv

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    django.setup()

def verify_setup():
    """Verify Google OAuth setup"""
    print("🔍 Verifying Google OAuth Setup")
    print("=" * 40)
    
    # Check environment variables
    load_dotenv()
    client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    # Check for real credentials vs placeholders
    has_real_client_id = bool(client_id and 'your-google-client-id-here' not in client_id and 'YOUR-REAL-GOOGLE-CLIENT-ID-HERE' not in client_id and len(client_id) > 20)
    has_real_client_secret = bool(client_secret and 'your-google-client-secret-here' not in client_secret and 'YOUR-REAL-GOOGLE-CLIENT-SECRET-HERE' not in client_secret and len(client_secret) > 20)
    
    client_id_status = '✅ REAL' if has_real_client_id else ('⚠️  PLACEHOLDER' if client_id else '❌ NOT SET')
    client_secret_status = '✅ REAL' if has_real_client_secret else ('⚠️  PLACEHOLDER' if client_secret else '❌ NOT SET')
    
    print(f"✅ GOOGLE_CLIENT_ID: {client_id_status}")
    print(f"✅ GOOGLE_CLIENT_SECRET: {client_secret_status}")
    
    if not has_real_client_id or not has_real_client_secret:
        print("\n⚠️  WARNING: Using placeholder credentials!")
        print("Google OAuth will NOT work with placeholder values.")
        print("Follow GET_GOOGLE_CREDENTIALS.md to get real credentials.")
        return False
    
    # Check SocialApp in database
    try:
        from allauth.socialaccount.models import SocialApp
        app = SocialApp.objects.get(provider='google')
        print(f"✅ SocialApp exists in database (ID: {app.id})")
        print(f"✅ SocialApp client_id: {app.client_id[:30]}...")
        print(f"✅ SocialApp secret: {app.secret[:10]}...")
    except SocialApp.DoesNotExist:
        print("❌ SocialApp not found in database")
        return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Check site configuration
    try:
        from django.contrib.sites.models import Site
        site = Site.objects.get(domain='127.0.0.1:8006')
        print(f"✅ Site configured: {site.domain}")
    except Site.DoesNotExist:
        print("❌ Site not configured for 127.0.0.1:8006")
        return False
    
    # Check if SocialApp is associated with site
    if site in app.sites.all():
        print("✅ SocialApp associated with site")
    else:
        print("❌ SocialApp not associated with site")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 Google OAuth Setup Verification Complete!")
    print("=" * 40)
    print("\n✅ All checks passed! Google OAuth is ready to use.")
    print("\nTo test:")
    print("1. Visit: http://127.0.0.1:8006/accounts/login/")
    print("2. Click the 'Continue with Google' button")
    print("3. You should be redirected to Google's OAuth flow")
    
    return True

if __name__ == '__main__':
    setup_django()
    success = verify_setup()
    
    if not success:
        print("\n❌ Setup verification failed!")
        print("Please run the setup script: python setup_google_oauth.py")