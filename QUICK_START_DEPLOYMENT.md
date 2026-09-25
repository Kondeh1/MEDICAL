# Production Deployment Quick Start

## 🚀 Getting Started

This guide will help you deploy your telemedicine application to production with full WebRTC video/audio call support.

## 📋 Prerequisites

1. **Server**: Ubuntu 20.04+ with root access
2. **Domain**: Registered domain name with DNS access
3. **SSL Certificate**: Will be obtained via Let's Encrypt

## 🛠️ Quick Setup Steps

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3 python3-pip python3-venv postgresql redis-server nginx -y
```

### 2. Create Application User

```bash
sudo adduser telemedicine
sudo usermod -aG sudo telemedicine
```

### 3. Database Setup

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE telemedicine_db;
CREATE USER telemedicine_user WITH PASSWORD 'your_secure_password';
ALTER ROLE telemedicine_user SET client_encoding TO 'utf8';
ALTER ROLE telemedicine_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE telemedicine_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE telemedicine_db TO telemedicine_user;
\q
```

### 4. Application Deployment

```bash
# Switch to application user
sudo su - telemedicine

# Create application directory
mkdir -p /home/telemedicine/app
cd /home/telemedicine/app

# Upload your application code here
# (Use git clone, scp, or rsync)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Environment Configuration

Create `.env` file:
```bash
# Generate secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Create .env file
nano .env
```

Add these variables:
```bash
SECRET_KEY=your-generated-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=telemedicine_db
DB_USER=telemedicine_user
DB_PASSWORD=your_secure_password
REDIS_URL=redis://127.0.0.1:6379/0
```

### 6. Initial Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

### 7. Service Configuration

Create systemd service:
```bash
sudo nano /etc/systemd/system/telemedicine-app.service
```

```ini
[Unit]
Description=Telemedicine Django Application
After=network.target

[Service]
User=telemedicine
Group=telemedicine
WorkingDirectory=/home/telemedicine/app
Environment=PATH=/home/telemedicine/app/venv/bin
ExecStart=/home/telemedicine/app/venv/bin/daphne -b 127.0.0.1 -p 8001 config.asgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 8. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/telemedicine
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL configuration (will be updated after Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    location /media/ {
        alias /home/telemedicine/app/media/;
    }
    
    location /static/ {
        alias /home/telemedicine/app/staticfiles/;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 9. Enable Services

```bash
# Enable nginx site
sudo ln -s /etc/nginx/sites-available/telemedicine /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Enable application service
sudo systemctl daemon-reload
sudo systemctl enable telemedicine-app
sudo systemctl start telemedicine-app
```

### 10. SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 🔍 Verification

Run the verification script:
```bash
python verify_production.py
```

This will check:
- ✅ Python version
- ✅ Environment variables
- ✅ System services
- ✅ Python packages
- ✅ Django settings
- ✅ File permissions
- ✅ Network connectivity

## 🎯 Post-Deployment

### Enable Monitoring
```bash
# Test the application
curl -I https://yourdomain.com

# Check service status
sudo systemctl status telemedicine-app

# View logs
sudo journalctl -u telemedicine-app -f
```

### Test WebRTC Functionality
1. Open two browser windows
2. Log in as different users
3. Navigate to a conversation
4. Test video and audio calls
5. Verify TURN server works across networks

## 🆘 Troubleshooting

### Common Issues

**Service won't start**:
```bash
# Check logs
sudo journalctl -u telemedicine-app

# Check configuration
sudo systemctl status telemedicine-app
```

**WebRTC issues**:
- Verify TURN server configuration
- Check firewall settings
- Ensure SSL certificate is valid

**Database connection errors**:
- Verify PostgreSQL is running
- Check database credentials
- Ensure database user has proper permissions

## 📚 Additional Resources

- Full deployment guide: `DEPLOYMENT_PRODUCTION.md`
- Environment variables: `ENVIRONMENT_VARIABLES.md`
- Troubleshooting: `VIDEO_CALL_TROUBLESHOOTING.md`
- Deployment checklist: `DEPLOYMENT_CHECKLIST.md`

Your telemedicine application is now ready for production with secure WebRTC video and audio calls!