#!/usr/bin/env python3
"""
Production Environment Verification Script
Run this script to verify all production requirements are met
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version requirement"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Upgrade required (3.8+ needed)")
        return False

def check_environment_variables():
    """Check required environment variables"""
    print("\nChecking environment variables...")
    required_vars = [
        'SECRET_KEY',
        'ALLOWED_HOSTS',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'REDIS_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.environ.get(var):
            print(f"✓ {var} - Set")
        else:
            print(f"✗ {var} - Missing")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def check_system_services():
    """Check if required system services are running"""
    print("\nChecking system services...")
    services = ['postgresql', 'redis-server', 'nginx']
    
    all_running = True
    for service in services:
        try:
            result = subprocess.run(['systemctl', 'is-active', service], 
                                  capture_output=True, text=True)
            if result.stdout.strip() == 'active':
                print(f"✓ {service} - Running")
            else:
                print(f"✗ {service} - Not running")
                all_running = False
        except Exception as e:
            print(f"✗ {service} - Check failed: {e}")
            all_running = False
    
    return all_running

def check_python_packages():
    """Check if required Python packages are installed"""
    print("\nChecking Python packages...")
    required_packages = [
        'django',
        'channels',
        'channels_redis',
        'daphne',
        'psycopg2',
        'redis',
        'PIL'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} - Installed")
        except ImportError:
            print(f"✗ {package} - Not installed")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_django_settings():
    """Check Django settings configuration"""
    print("\nChecking Django settings...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
        import django
        django.setup()
        
        from django.conf import settings
        
        # Check debug mode
        if settings.DEBUG:
            print("✗ DEBUG mode is ON - Should be OFF in production")
            return False
        else:
            print("✓ DEBUG mode is OFF")
        
        # Check allowed hosts
        if settings.ALLOWED_HOSTS and len(settings.ALLOWED_HOSTS) > 0:
            print(f"✓ ALLOWED_HOSTS configured: {settings.ALLOWED_HOSTS}")
        else:
            print("✗ ALLOWED_HOSTS not configured")
            return False
        
        # Check database
        if settings.DATABASES.get('default'):
            print("✓ Database configured")
        else:
            print("✗ Database not configured")
            return False
        
        # Check channels
        if hasattr(settings, 'CHANNEL_LAYERS'):
            print("✓ Channels configured")
        else:
            print("✗ Channels not configured")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Django settings error: {e}")
        return False

def check_file_permissions():
    """Check file and directory permissions"""
    print("\nChecking file permissions...")
    
    base_dir = Path(__file__).resolve().parent
    checks = [
        (base_dir / 'media', 'Media directory'),
        (base_dir / 'staticfiles', 'Static files directory'),
        (base_dir / 'logs', 'Logs directory'),
    ]
    
    all_good = True
    for path, description in checks:
        if path.exists():
            # Check if directory is writable
            if os.access(path, os.W_OK):
                print(f"✓ {description} - Writable")
            else:
                print(f"✗ {description} - Not writable")
                all_good = False
        else:
            print(f"⚠ {description} - Does not exist (will be created)")
    
    return all_good

def check_network_connectivity():
    """Check network connectivity to required services"""
    print("\nChecking network connectivity...")
    
    import socket
    
    connections = [
        ('127.0.0.1', 5432, 'PostgreSQL'),
        ('127.0.0.1', 6379, 'Redis'),
    ]
    
    all_connected = True
    for host, port, service in connections:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✓ {service} - Connected ({host}:{port})")
            else:
                print(f"✗ {service} - Connection failed ({host}:{port})")
                all_connected = False
        except Exception as e:
            print(f"✗ {service} - Connection error: {e}")
            all_connected = False
    
    return all_connected

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("PRODUCTION ENVIRONMENT VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment Variables", check_environment_variables),
        ("System Services", check_system_services),
        ("Python Packages", check_python_packages),
        ("Django Settings", check_django_settings),
        ("File Permissions", check_file_permissions),
        ("Network Connectivity", check_network_connectivity),
    ]
    
    results = []
    for check_name, check_function in checks:
        print(f"\n{check_name}:")
        print("-" * 40)
        try:
            result = check_function()
            results.append((check_name, result))
        except Exception as e:
            print(f"✗ {check_name} - Failed with error: {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status:4} - {check_name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Ready for production deployment.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please address the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())