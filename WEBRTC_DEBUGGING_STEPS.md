# WebRTC Connection Debugging - Step by Step

## Current Issue
Users can accept calls but the connection stays in "connecting" state and they can't communicate.

## Debugging Steps

### 1. Check WebSocket Connection
First, let's verify the WebSocket connection is working properly:

1. Open browser console (F12) 
2. Look for these messages:
   ```
   Connecting to WebSocket: ws://127.0.0.1:8000/ws/call/XXXX-XXXX-XXXX/
   WebSocket connected - ready for WebRTC signaling
   WebSocket readyState: 1
   ```

### 2. Check Offer/Answer Exchange
Look for these signaling messages in the console:
```
=== CREATING WEBRTC OFFER ===
Offer created successfully: offer
Offer sent to other peer via WebSocket
=== HANDLING RECEIVED OFFER ===
Answer created successfully: answer
Answer sent to caller via WebSocket
```

### 3. Check ICE Candidate Exchange
Look for ICE candidate messages:
```
=== ICE CANDIDATE EVENT ===
Candidate: RTCIceCandidate {...}
Sending ICE candidate via WebSocket...
ICE candidate sent successfully
Adding ICE candidate: {...}
ICE candidate added successfully
```

### 4. Check Connection States
Monitor these connection state changes:
```
=== CONNECTION STATE CHANGE ===
Connection state: connecting
ICE connection state: checking
Signaling state: stable

=== ICE CONNECTION STATE CHANGE ===
ICE connection state: connected
✅ ICE connection established!

=== CONNECTION STATE CHANGE ===
Connection state: connected
✅ WebRTC connection established!
```

## Common Issues to Check

### Issue 1: WebSocket Connection Failure
**Symptoms:** No WebSocket connection messages in console
**Check:** 
- Server logs for WebSocket connection
- Network connectivity
- Browser WebSocket support

### Issue 2: Signaling Message Not Received
**Symptoms:** Offer/answer created but not received by other peer
**Check:**
- Server logs for message forwarding
- Room group names match
- User authentication

### Issue 3: ICE Candidate Issues
**Symptoms:** Connection state stuck at "checking"
**Check:**
- ICE candidates being generated
- Candidates being exchanged
- STUN/TURN server accessibility

### Issue 4: Media Stream Issues
**Symptoms:** Connection established but no audio/video
**Check:**
- Local stream acquisition
- Track addition to peer connection
- Audio/video track states

## Testing Process

### Test 1: Basic Connection
1. Open two browser windows with different users
2. Initiate call from User A to User B
3. Accept call on User B side
4. Monitor both consoles for:
   - WebSocket connection success
   - Offer/answer exchange
   - ICE candidate exchange
   - Connection state changes

### Test 2: Server Log Monitoring
While testing, check server terminal for:
```
CallConsumer received message from user XXX: {...}
Message type: offer/answer/ice_candidate
Forwarding offer/answer/ice_candidate from XXX to room call_XXXX-XXXX-XXXX
Offer/Answer/ICE candidate forwarded successfully
```

### Test 3: Network Inspection
1. Open browser DevTools Network tab
2. Filter for WebSocket connections
3. Check that messages are being sent/received
4. Look for any WebSocket errors

## What to Report

If the issue persists, please provide:
1. Browser console output from both users
2. Server terminal logs during the call attempt
3. Network tab WebSocket frame details
4. Steps taken and what you observed

The enhanced debugging should now show exactly where in the connection process the issue occurs.