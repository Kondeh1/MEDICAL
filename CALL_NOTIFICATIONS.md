# Real-time Call Notification System

## Overview
This system implements real-time call notifications for the telemedicine platform, allowing patients to receive immediate notifications when providers initiate calls.

## How It Works

### 1. Call Initiation (Provider Side)
When a provider clicks the call button:
1. A `Call` object is created in the database
2. A `Notification` is created for the patient
3. A WebSocket message is sent to the patient's personal notification group
4. The provider is redirected to the call room

### 2. Real-time Notification (Patient Side)
When a call is initiated:
1. Patient's browser receives WebSocket message via `incoming_call` event
2. An incoming call popup appears with ringing animation
3. Audio ringing sound plays (if browser allows autoplay)
4. Patient can accept or decline the call

### 3. Call Actions
- **Accept**: Redirects to call room URL to join the call
- **Decline**: Sends AJAX request to mark call as declined
- **Close Popup**: Automatically marks call as missed

## Technical Implementation

### WebSocket Consumers
The `CallConsumer` class handles:
- User group management (`user_{user_id}`)
- Call signaling between peers
- Real-time notifications
- Call status updates

### Key Components

#### 1. WebSocket Routes (`messaging/routing.py`)
```python
websocket_urlpatterns = [
    re_path(r'ws/call/(?P<room_name>\w+)/$', consumers.CallConsumer.as_asgi()),
    re_path(r'ws/call/notifications/$', consumers.CallConsumer.as_asgi()),
    re_path(r'ws/consultation_call/(?P<consultation_id>\d+)/$', consumers.ConsultationCallConsumer.as_asgi()),
]
```

#### 2. Notification Sending (`messaging/views.py`)
```python
def send_call_notification(receiver, caller, call_type, room_id, call_id):
    """Send real-time WebSocket notification to receiver"""
    channel_layer = get_channel_layer()
    group_name = f'user_{receiver.id}'
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'incoming_call',
            'recipient_id': str(receiver.id),
            'caller_id': str(caller.id),
            'caller_name': caller.get_full_name() or caller.username,
            'call_type': call_type,
            'room_id': room_id,
            'call_id': call_id,
        }
    )
```

#### 3. Frontend WebSocket Handler (`templates/base.html`)
```javascript
function initWebSocket() {
    const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${wsScheme}://${window.location.host}/ws/call/notifications/`;
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        switch(data.type) {
            case 'incoming_call':
                showIncomingCallPopup(data);
                playRingingSound();
                break;
        }
    };
}
```

## User Experience

### Incoming Call Popup
- **Visual**: Animated ringing icon with gradient background
- **Audio**: Beeping sound that repeats until action is taken
- **Information**: Shows caller name and call type (Video/Audio)
- **Actions**: Accept and Decline buttons

### Automatic Features
- **Reconnection**: WebSocket automatically reconnects if connection drops
- **Popup Dismissal**: Call popups automatically close when call ends
- **Status Updates**: Real-time call status synchronization
- **Notification Count**: Updates notification badge in real-time

## Testing the Feature

### Manual Testing Steps
1. Log in as provider and patient in different browser sessions
2. Navigate to conversation between them
3. As provider, click Video or Audio call button
4. As patient, observe:
   - Incoming call popup appears
   - Ringing animation plays
   - Audio notification sounds
   - Accept/Decline options available

### Expected Behavior
- ✅ Popup appears immediately after call initiation
- ✅ Ringing sound plays (browser-dependent)
- ✅ Accept button redirects to call room
- ✅ Decline button marks call as declined
- ✅ Closing popup marks call as missed
- ✅ Call status updates in real-time

## Error Handling

### WebSocket Issues
- Automatic reconnection attempts every 5 seconds
- Graceful fallback to polling if needed
- Error logging for debugging

### Browser Limitations
- Audio autoplay may be blocked by browser policies
- Notifications work even without audio
- Visual indicators always function

### Network Issues
- Persistent connections with automatic recovery
- Call state synchronization across reconnects
- Timeout handling for abandoned calls

## Security Considerations

- Only authenticated users can receive notifications
- Users only receive notifications for calls directed to them
- CSRF protection on all AJAX endpoints
- Secure WebSocket connections (WSS) in production

## Customization Options

### Ringing Sound
Modify the `playRingingSound()` function in `base.html` to:
- Change frequency and duration
- Use custom audio files
- Adjust volume levels

### Popup Styling
Update the CSS in the modal HTML to:
- Change colors and animations
- Modify sizing and positioning
- Add custom branding elements

### Notification Timing
Adjust the timeout values in:
- WebSocket reconnection intervals
- Call abandonment timeouts
- Ringing sound repetition frequency

## Troubleshooting

### Common Issues

**Popup doesn't appear:**
- Check browser console for WebSocket errors
- Verify user is logged in and authenticated
- Ensure both users are in the same conversation

**No audio sound:**
- Browser may block autoplay (user interaction required first)
- Check browser audio settings
- Test with different browsers

**WebSocket connection fails:**
- Verify Django Channels is properly configured
- Check ALLOWED_HOSTS setting
- Ensure Redis is running (for production)

This implementation provides a robust, real-time call notification system that enhances the user experience for telemedicine consultations.