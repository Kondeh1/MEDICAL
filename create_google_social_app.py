import os
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

def create_google_app():
    # Get or create the default site
    site, created = Site.objects.get_or_create(
        domain='127.0.0.1:8006',
        defaults={'name': 'Local Development'}
    )
    
    if created:
        print(f"Created site: {site.domain}")
    
    # Get Google OAuth credentials from environment variables
    client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    if not client_id or not client_secret:
        print("WARNING: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set in .env file")
        print("Using placeholder values. Please update your .env file with actual credentials.")
        client_id = client_id or 'your-google-client-id-here'
        client_secret = client_secret or 'your-google-client-secret-here'
    
    # Create or update the Google SocialApp
    app, created = SocialApp.objects.update_or_create(
        provider='google',
        defaults={
            'name': 'Google OAuth',
            'client_id': client_id,
            'secret': client_secret,
            'key': '',  # This is for Google's legacy key, usually empty
        }
    )
    
    # Associate with the site
    if site not in app.sites.all():
        app.sites.add(site)
    
    # Note: Google-specific settings are now configured in settings.py
    # The scope and other parameters are set in SOCIALACCOUNT_PROVIDERS
    
    print(f"Google SocialApp {'created' if created else 'updated'} successfully!")
    print(f"App ID: {app.id}")
    print(f"Client ID: {app.client_id}")
    print(f"Secret: {app.secret[:10]}...")
    
    if not os.environ.get('GOOGLE_CLIENT_ID') or not os.environ.get('GOOGLE_CLIENT_SECRET'):
        print("\n⚠️  WARNING: Missing Google OAuth credentials!")
        print("Please update your .env file with actual Google OAuth credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project and enable Google+ API")
        print("3. Create OAuth 2.0 credentials")
        print("4. Add these redirect URIs:")
        print("   - http://127.0.0.1:8006/auth/google/login/callback/")
        print("   - http://localhost:8006/auth/google/login/callback/")
        print("5. Update your .env file with the Client ID and Secret")
        print("6. Run this script again")
    else:
        print("\n✅ Google OAuth is configured and ready to use!")

if __name__ == '__main__':
    create_google_app()