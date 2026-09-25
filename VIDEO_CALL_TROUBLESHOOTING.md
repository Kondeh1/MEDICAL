# Video/Audio Call Troubleshooting Guide

## Common Issues and Solutions

### 1. Calls Not Connecting

**Problem**: Video/audio calls fail to establish connection between users.

**Solutions**:
- Ensure both users are using HTTPS or localhost (WebRTC requires secure context)
- Check that browser supports WebRTC (Chrome, Firefox, Edge, Safari)
- Verify camera/microphone permissions are granted
- Make sure both users join the call room

### 2. No Audio/Video Stream

**Problem**: Local stream works but remote stream doesn't appear.

**Solutions**:
- Check browser console for WebRTC errors
- Ensure STUN/TURN servers are properly configured
- Verify both users have working camera/microphone
- Check network connectivity and firewall settings

### 3. WebSocket Connection Issues

**Problem**: WebSocket fails to connect for signaling.

**Solutions**:
- For development: Use `InMemoryChannelLayer` (single process only)
- For production: Set up Redis and use `RedisChannelLayer`
- Check ALLOWED_HOSTS in settings includes your domain
- Verify Daphne is running as ASGI server

### 4. Server Configuration

**Development Setup**:
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python manage.py runserver
```

**Production Setup**:
```bash
# Set environment variables
export REDIS_URL=redis://localhost:6379/0
export ALLOWED_HOSTS=yourdomain.com

# Run with Daphne
daphne config.asgi:application
```

### 5. TURN Server Configuration (For Production)

For production deployments, you'll need a TURN server for NAT traversal:

1. **Install Coturn**:
```bash
# Ubuntu/Debian
sudo apt-get install coturn

# Configure /etc/turnserver.conf
listening-port=3478
tls-listening-port=5349
listening-ip=YOUR_SERVER_IP
relay-ip=YOUR_SERVER_IP
external-ip=YOUR_PUBLIC_IP
realm=yourdomain.com
server-name=yourdomain.com
```

2. **Add to WebRTC config**:
```javascript
const configuration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    {
      urls: 'turn:your-turn-server.com:3478',
      username: 'turnuser',
      credential: 'turnpassword'
    }
  ]
};
```

### 6. Testing Checklist

Before deploying:
- [ ] Test with two browser tabs/windows on localhost
- [ ] Verify audio works in both directions
- [ ] Test video functionality
- [ ] Check connection with users on different networks
- [ ] Test call timeout functionality
- [ ] Verify missed call notifications

### 7. Debugging Tools

**Browser Developer Tools**:
- Network tab: Check WebSocket connections
- Console: Look for WebRTC and JavaScript errors
- Application tab: Check media device permissions

**Server Logs**:
```bash
# Check Django logs
python manage.py runserver --verbosity=2

# Check Daphne logs
daphne config.asgi:application --access-log -
```

### 8. Browser Compatibility

**Supported Browsers**:
- Chrome 90+
- Firefox 88+
- Safari 14.1+
- Edge 90+

**Minimum Requirements**:
- JavaScript enabled
- Camera/microphone access
- WebRTC support
- Secure context (HTTPS or localhost)

### 9. Common Error Messages

**"Permission denied"**: User hasn't granted camera/microphone permissions
**"ICE connection failed"**: Network/firewall blocking WebRTC traffic
**"WebSocket connection failed"**: Server configuration issue
**"getUserMedia error"**: Camera/microphone not available or blocked

### 10. Performance Optimization

- Use efficient video codecs (VP8/VP9/H.264)
- Implement bandwidth adaptation
- Consider video resolution constraints
- Use connection quality monitoring

## Need Help?

If issues persist:
1. Check browser console for specific error messages
2. Verify all dependencies are installed
3. Test with different browsers
4. Ensure proper server configuration
5. Check network connectivity and firewall settings