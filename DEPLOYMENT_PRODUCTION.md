# Production Deployment Guide

## Prerequisites

Before deploying to production, ensure you have:

- Domain name with SSL certificate
- Server with Ubuntu 20.04+ or similar Linux distribution
- PostgreSQL database
- Redis server
- TURN server (recommended for NAT traversal)

## 1. Server Setup

### Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv python3-dev -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Redis
sudo apt install redis-server -y

# Install Nginx
sudo apt install nginx -y

# Install system dependencies for Python packages
sudo apt install build-essential libpq-dev libffi-dev libssl-dev -y
```

### Create Application User

```bash
# Create dedicated user for the application
sudo adduser telemedicine
sudo usermod -aG sudo telemedicine
```

### Set Up Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE telemedicine_db;
CREATE USER telemedicine_user WITH PASSWORD 'your_secure_password';
ALTER ROLE telemedicine_user SET client_encoding TO 'utf8';
ALTER ROLE telemedicine_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE telemedicine_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE telemedicine_db TO telemedicine_user;
\q
```

## 2. Application Setup

### Clone and Configure Application

```bash
# Switch to application user
sudo su - telemedicine

# Clone your repository (or copy files)
git clone your-repo-url /home/telemedicine/app
cd /home/telemedicine/app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

Create `.env` file in your project root:

```bash
# Secret key (generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
SECRET_KEY=your-generated-secret-key

# Hosts
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database
DB_NAME=telemedicine_db
DB_USER=telemedicine_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# Email (if using SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# TURN Server (if configured)
TURN_USERNAME=your-turn-username
TURN_PASSWORD=your-turn-password
```

### Run Migrations and Collect Static Files

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

## 3. Redis Configuration

### Configure Redis for Production

```bash
# Edit Redis configuration
sudo nano /etc/redis/redis.conf

# Add these settings:
bind 127.0.0.1
port 6379
timeout 300
tcp-keepalive 60
maxmemory 256mb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

## 4. TURN Server Setup (Recommended)

For production WebRTC calls to work across different networks, you need a TURN server:

### Install Coturn

```bash
# Install coturn
sudo apt install coturn -y

# Configure coturn
sudo nano /etc/turnserver.conf
```

### TURN Server Configuration

```conf
# Basic configuration
listening-port=3478
tls-listening-port=5349
listening-ip=YOUR_SERVER_PUBLIC_IP
relay-ip=YOUR_SERVER_PUBLIC_IP
external-ip=YOUR_SERVER_PUBLIC_IP

# Authentication
realm=yourdomain.com
server-name=yourdomain.com

# Security
lt-cred-mech
user=turnuser:turnpassword

# Network settings
no-loopback-peers
no-multicast-peers

# Logging
log-file=/var/log/turnserver.log
simple-log
```

### Start TURN Server

```bash
# Enable TURN server
sudo systemctl enable coturn
sudo systemctl start coturn

# Check status
sudo systemctl status coturn
```

### Update Application Settings

Add your TURN server to the WebRTC configuration in `production.py`:

```python
WEBRTC_CONFIG = {
    'STUN_SERVERS': [
        'stun:stun.l.google.com:19302',
        'stun:stun1.l.google.com:19302',
    ],
    'TURN_SERVERS': [
        {
            'urls': 'turn:yourdomain.com:3478',
            'username': os.environ.get('TURN_USERNAME', 'turnuser'),
            'credential': os.environ.get('TURN_PASSWORD', 'turnpassword'),
        }
    ],
    'ICE_TRANSPORT_POLICY': 'all',
}
```

## 5. Web Server Configuration

### Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/telemedicine
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates (using Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Media files
    location /media/ {
        alias /home/telemedicine/app/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Static files
    location /static/ {
        alias /home/telemedicine/app/staticfiles/;
        expires 365d;
        add_header Cache-Control "public, immutable";
        location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # WebSocket connections for WebRTC signaling
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### Enable Site and Restart Nginx

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/telemedicine /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 6. SSL Certificate Setup

### Install Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## 7. Process Management

### Using Systemd for Process Management

Create systemd service files:

```bash
# Create service file for Django application
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

```bash
# Create service file for background tasks
sudo nano /etc/systemd/system/telemedicine-worker.service
```

```ini
[Unit]
Description=Telemedicine Background Worker
After=network.target

[Service]
User=telemedicine
Group=telemedicine
WorkingDirectory=/home/telemedicine/app
Environment=PATH=/home/telemedicine/app/venv/bin
ExecStart=/home/telemedicine/app/venv/bin/python manage.py runworker
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable telemedicine-app
sudo systemctl enable telemedicine-worker

# Start services
sudo systemctl start telemedicine-app
sudo systemctl start telemedicine-worker

# Check status
sudo systemctl status telemedicine-app
sudo systemctl status telemedicine-worker
```

## 8. Monitoring and Maintenance

### Set Up Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/telemedicine
```

```conf
/home/telemedicine/app/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 telemedicine telemedicine
    postrotate
        systemctl reload telemedicine-app
    endscript
}
```

### Health Check Script

Create a health check script:

```bash
# Create health check script
sudo nano /home/telemedicine/app/health_check.sh
```

```bash
#!/bin/bash
# Health check script for Telemedicine application

# Check if services are running
if ! systemctl is-active --quiet telemedicine-app; then
    echo "Django application is not running"
    systemctl start telemedicine-app
fi

if ! systemctl is-active --quiet telemedicine-worker; then
    echo "Background worker is not running"
    systemctl start telemedicine-worker
fi

# Check if ports are listening
if ! netstat -tuln | grep -q ":8001 "; then
    echo "Application port 8001 is not listening"
    systemctl restart telemedicine-app
fi

# Check database connectivity
if ! pg_isready -d telemedicine_db -U telemedicine_user > /dev/null 2>&1; then
    echo "Database is not accessible"
fi

# Check Redis connectivity
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Redis is not responding"
    systemctl restart redis-server
fi
```

Make it executable and add to cron:

```bash
chmod +x /home/telemedicine/app/health_check.sh

# Add to cron (runs every 5 minutes)
echo "*/5 * * * * /home/telemedicine/app/health_check.sh" | sudo crontab -
```

## 9. Backup Strategy

### Database Backup Script

```bash
# Create backup script
sudo nano /home/telemedicine/app/backup.sh
```

```bash
#!/bin/bash
# Backup script for Telemedicine application

BACKUP_DIR="/home/telemedicine/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U telemedicine_user -h localhost telemedicine_db > $BACKUP_DIR/db_backup_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /home/telemedicine/app/media/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

Make executable and schedule:

```bash
chmod +x /home/telemedicine/app/backup.sh

# Add to daily cron
echo "0 2 * * * /home/telemedicine/app/backup.sh" | sudo crontab -
```

## 10. Deployment Checklist

Before going live, verify:

- [ ] SSL certificate is valid and auto-renewing
- [ ] All services are running and set to start on boot
- [ ] Database backups are configured
- [ ] Health checks are running
- [ ] Static and media files are accessible
- [ ] WebSocket connections work properly
- [ ] WebRTC calls function between different networks
- [ ] TURN server is properly configured
- [ ] Email notifications work
- [ ] Security headers are properly set
- [ ] All environment variables are set
- [ ] Debug mode is disabled
- [ ] Allowed hosts are properly configured
- [ ] CSRF settings are configured correctly

## 11. Troubleshooting

### Common Issues

**WebRTC Connection Issues**:
- Verify TURN server is running and accessible
- Check firewall settings for UDP ports 3478, 3479
- Ensure ICE servers are properly configured

**WebSocket Connection Issues**:
- Check Nginx proxy configuration
- Verify Daphne is running on port 8001
- Check firewall settings for WebSocket traffic

**Database Connection Issues**:
- Verify PostgreSQL is running
- Check database credentials
- Ensure PostgreSQL is listening on localhost

**Static Files Not Loading**:
- Run `python manage.py collectstatic`
- Check Nginx configuration for static files
- Verify file permissions

**SSL/HTTPS Issues**:
- Verify Let's Encrypt certificate is valid
- Check Nginx SSL configuration
- Test with SSL Labs SSL Test

This deployment guide provides a production-ready setup for your telemedicine application with proper WebRTC support for video and audio calls.