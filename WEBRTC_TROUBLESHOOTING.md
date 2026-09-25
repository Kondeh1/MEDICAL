# WebRTC Connection Troubleshooting Guide

## Common Issues and Solutions

### 1. Users Can't Join Call

**Symptoms**: 
- Call room loads but shows "Connecting..." indefinitely
- No remote video/audio appears
- WebSocket connects but WebRTC signaling fails

**Debugging Steps**:

1. **Check Browser Console Logs**:
   - Open Developer Tools (F12)
   - Go to Console tab
   - Look for WebRTC-related errors
   - Check WebSocket connection status

2. **Verify Media Permissions**:
   - Ensure browser has camera/microphone access
   - Check browser settings for site permissions
   - Try in incognito/private mode

3. **Network Requirements**:
   - Both users must be on same network or have proper NAT traversal
   - STUN servers should be accessible
   - No firewall blocking WebRTC traffic

### 2. Expected Console Output

When WebRTC is working correctly, you should see:

```
Connecting to WebSocket: ws://127.0.0.1:8000/ws/call/[room-id]/
WebSocket connected - ready for WebRTC signaling
WebSocket readyState: 1
Requesting user media...
Local stream obtained
Initializing WebRTC peer connection...
PeerConnection created successfully
Other user joined: [username]
Caller creating offer... (if caller)
Creating WebRTC offer...
Offer created: [RTCSessionDescription]
Local description set: [RTCSessionDescription]
Offer sent to other peer
Received offer, creating answer... (if receiver)
Answer created: [RTCSessionDescription]
Local description set: [RTCSessionDescription]
Answer sent to caller
ICE candidate generated: [RTCIceCandidate]
Adding ICE candidate: [RTCIceCandidate]
ICE candidate added successfully
Received remote stream!
WebRTC connection established!
Connection state changed: connected
```

### 3. Common Error Messages

**"WebRTC is not supported in your browser"**
- Solution: Use Chrome, Firefox, Edge, or Safari
- Ensure you're using HTTPS or localhost

**"Permission denied" for camera/microphone**
- Solution: Grant permissions in browser
- Check site settings for media access

**"WebSocket error"**
- Solution: Check if Daphne server is running
- Verify ALLOWED_HOSTS includes your domain
- Check network connectivity

**"ICE connection failed"**
- Solution: Check STUN server connectivity
- Verify network firewall settings
- Try different network connection

### 4. Testing Steps

1. **Single User Test**:
   - Log in as provider
   - Start a call with yourself (different browser tab)
   - Verify local video works

2. **Two User Test**:
   - Log in as provider in one browser
   - Log in as patient in another browser/incognito
   - Initiate call from provider to patient
   - Accept call as patient
   - Verify both videos appear

3. **Network Test**:
   - Try on same network first
   - Then try from different networks
   - Check if TURN server is needed for NAT traversal

### 5. Production Considerations

For production deployment:
- Set up TURN server for NAT traversal
- Use HTTPS (required for WebRTC)
- Configure proper STUN/TURN servers
- Set up Redis for WebSocket channel layer
- Configure ALLOWED_HOSTS properly

### 6. Quick Diagnostic Commands

```bash
# Check if required services are running
netstat -an | grep :8000  # Django server
netstat -an | grep :6379  # Redis (if used)

# Test STUN server connectivity
# Visit: https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/
```

### 7. Browser Compatibility

**Supported Browsers**:
- Chrome 70+
- Firefox 60+
- Safari 12+
- Edge 79+

**Minimum Requirements**:
- JavaScript enabled
- WebRTC support
- Camera/microphone access
- WebSocket support