#!/usr/bin/env python
"""
Test script to verify provider registration is working correctly.
Run with: python manage.py shell < test_provider_registration.py
"""

from accounts.models import CustomUser, ProviderProfile
from django.utils import timezone
from datetime import timedelta

print("\n" + "="*60)
print("PROVIDER REGISTRATION TEST")
print("="*60 + "\n")

# Check recent provider registrations
print("1. Checking recent provider registrations (last 24 hours)...")
recent_providers = CustomUser.objects.filter(
    role='PROVIDER',
    date_joined__gte=timezone.now() - timedelta(days=1)
).order_by('-date_joined')

if recent_providers.exists():
    print(f"   ✓ Found {recent_providers.count()} recent provider(s):\n")
    for user in recent_providers:
        print(f"   - Username: {user.username}")
        print(f"     Email: {user.email}")
        print(f"     Name: {user.get_full_name()}")
        print(f"     Registered: {user.date_joined.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if profile exists
        if hasattr(user, 'provider_profile'):
            profile = user.provider_profile
            print(f"     Credentials: {profile.credentials}")
            print(f"     Specialization: {profile.specialization}")
            print(f"     Approval Status: {profile.approval_status}")
            print(f"     Professional Licence: {'✓' if profile.professional_licence else '✗'}")
            print(f"     Academic Certificates: {'✓' if profile.academic_certificates else '✗'}")
            print(f"     ID Documents: {'✓' if profile.identification_documents else '✗'}")
        else:
            print(f"     ✗ WARNING: No provider profile found!")
        print()
else:
    print("   ✗ No recent provider registrations found.\n")

# Check all providers
print("2. Checking all provider accounts...")
all_providers = CustomUser.objects.filter(role='PROVIDER').count()
print(f"   Total providers: {all_providers}\n")

# Check pending approvals
print("3. Checking pending provider approvals...")
pending = ProviderProfile.objects.filter(approval_status='PENDING').count()
approved = ProviderProfile.objects.filter(approval_status='APPROVED').count()
rejected = ProviderProfile.objects.filter(approval_status='REJECTED').count()

print(f"   Pending: {pending}")
print(f"   Approved: {approved}")
print(f"   Rejected: {rejected}\n")

# Check for providers without profiles
print("4. Checking for providers without profiles...")
providers_without_profiles = CustomUser.objects.filter(
    role='PROVIDER'
).exclude(
    id__in=ProviderProfile.objects.values_list('user_id', flat=True)
)

if providers_without_profiles.exists():
    print(f"   ✗ WARNING: {providers_without_profiles.count()} provider(s) without profile:")
    for user in providers_without_profiles:
        print(f"   - {user.username} ({user.email})")
else:
    print("   ✓ All providers have profiles")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60 + "\n")
