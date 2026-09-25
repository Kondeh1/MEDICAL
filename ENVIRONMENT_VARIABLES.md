# Environment Variables Configuration

This file documents all required environment variables for production deployment.

## Required Environment Variables

### Security Settings
```bash
# Django secret key - generate a secure random key
SECRET_KEY=your-very-long-random-secret-key-here

# Debug mode - must be False in production
DEBUG=False
```

### Host Configuration
```bash
# Domain names your application will serve
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,ip-address

# CSRF trusted origins (HTTPS URLs)
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Database Configuration
```bash
# PostgreSQL database settings
DB_NAME=telemedicine_db
DB_USER=telemedicine_user
DB_PASSWORD=your-secure-database-password
DB_HOST=localhost
DB_PORT=5432
```

### Redis Configuration
```bash
# Redis connection for channels and caching
REDIS_URL=redis://127.0.0.1:6379/0
```

### Email Configuration
```bash
# SMTP settings for email notifications
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### TURN Server Configuration (Optional but Recommended)
```bash
# Credentials for your TURN server
TURN_USERNAME=your-turn-username
TURN_PASSWORD=your-turn-password
```

### SSL/Proxy Settings
```bash
# If behind a reverse proxy
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

## Setting Environment Variables

### Method 1: Using .env file
Create a `.env` file in your project root:

```bash
# .env file
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_PASSWORD=your-db-password
# ... other variables
```

### Method 2: System Environment Variables
Set variables in your system:

```bash
# Linux/Unix
export SECRET_KEY="your-secret-key"
export ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"

# Add to ~/.bashrc or ~/.profile for persistence
echo 'export SECRET_KEY="your-secret-key"' >> ~/.bashrc
```

### Method 3: Using systemd service files
Include in your service configuration:

```ini
[Service]
Environment=SECRET_KEY=your-secret-key
Environment=ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## Security Best Practices

1. **Never commit sensitive data** to version control
2. **Use strong, random passwords** for all services
3. **Restrict database access** to application server only
4. **Use environment-specific configurations**
5. **Regularly rotate secrets** and credentials
6. **Monitor access logs** for suspicious activity

## Example Production .env File

```bash
# Security
SECRET_KEY=django-insecure-abcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()
DEBUG=False

# Hosts
ALLOWED_HOSTS=telemedicine.yourcompany.com,api.telemedicine.yourcompany.com
CSRF_TRUSTED_ORIGINS=https://telemedicine.yourcompany.com,https://api.telemedicine.yourcompany.com

# Database
DB_NAME=telemedicine_production
DB_USER=telemedicine_app
DB_PASSWORD=super-secure-password-123!
DB_HOST=127.0.0.1
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@yourcompany.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=noreply@yourcompany.com

# TURN Server
TURN_USERNAME=production-turn-user
TURN_PASSWORD=secure-turn-password-456!

# Optional: Additional settings
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
```

## Loading Environment Variables in Django

The application automatically loads environment variables from:
1. System environment variables
2. `.env` file (if python-dotenv is installed)
3. Default values in settings files

Make sure `python-dotenv` is in your requirements.txt for .env file support.