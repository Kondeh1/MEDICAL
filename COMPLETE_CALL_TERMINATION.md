# Complete Call Termination on Decline - Test Guide

## What Was Implemented

When one user declines a call, the system now completely terminates the call for both users instead of just showing notifications. This ensures a clean end to the call experience.

## Key Changes Made

### 1. **Server-Side Changes** (`messaging/views.py`)
- Modified `decline_call` function to send both `call_status_update` and `call_ended` WebSocket messages
- The `call_ended` message triggers complete termination on both sides
- Call status properly updated in database

### 2. **Frontend Changes** (`templates/base.html`)
- Added `call_ended` message handler that:
  - Shows blue "Call ended" notification to both users
  - Automatically closes any call popups
  - Stops ringing audio immediately
  - Redirects users from call pages back to messaging

### 3. **Call Room Integration** (`messaging/templates/messaging/call_room.html`)
- Enhanced `call_ended` handler to show custom decline messages
- Proper call termination with cleanup of WebRTC connections
- Redirects both users appropriately

## How It Works Now

```
Patient Declines Call:
1. Patient clicks "Decline" button
2. AJAX request to /messages/call/{call_id}/decline/
3. Server updates call status to MISSED
4. Server sends TWO WebSocket messages:
   a. call_status_update (shows notification to caller)
   b. call_ended (terminates call for both users)
5. Both users receive call_ended message
6. Both users see "Call ended" notification
7. Both users are redirected/cleaned up appropriately
```

## Complete Test Scenarios

### Test 1: Decline Before Joining Call Room
1. **Setup**: Provider initiates call to patient
2. **Action**: Patient declines from notification popup
3. **Expected Results**:
   - **Patient**: Green "Call declined" confirmation (3 seconds)
   - **Provider**: Blue "Call ended by Patient" notification (5 seconds)
   - **Both**: Popups close, audio stops
   - **Provider**: Redirected to conversation if on call page

### Test 2: Decline After Joining Call Room
1. **Setup**: Both users join call room
2. **Action**: One user clicks decline/end call button
3. **Expected Results**:
   - **Declining user**: Blue "Call ended" notification
   - **Other user**: Blue "Call ended by [User]" notification
   - **Both**: Call terminates, WebRTC connections closed
   - **Both**: Redirected to messaging page

### Test 3: Multiple User Scenarios
1. **Test with 2+ users in call room**: Decline should end for all
2. **Test with user closing popup**: Should mark as missed and end call
3. **Test with network disconnection**: Should handle gracefully

## Expected User Experience

### For the Declining User:
- Immediate visual confirmation (green "Call declined")
- Call popup closes automatically
- Audio stops immediately
- Clean exit from call interface

### For the Calling User:
- Clear notification (blue "Call ended by [User]")
- Call popup closes automatically
- Ringtone stops immediately
- Redirected to safe page if needed

### For Both Users:
- No lingering call state
- No zombie connections
- Consistent experience across scenarios
- Proper database state updates

## WebSocket Message Flow

```
Complete Termination Flow:
decline_call() → 
  Database update (MISSED) → 
  WebSocket: call_status_update (notification) → 
  WebSocket: call_ended (termination) → 
  Both clients: endCall() → 
  Cleanup and redirect
```

## Troubleshooting

### If Call Doesn't End Completely:
1. **Check browser console** for JavaScript errors
2. **Verify WebSocket connections** are active for both users
3. **Check network tab** for the decline AJAX request
4. **Ensure both users** receive the call_ended message

### If Redirect Doesn't Work:
1. **Check URL patterns** in browser console
2. **Verify user authentication** is still valid
3. **Check for JavaScript errors** preventing redirect

### If Audio Doesn't Stop:
1. **Verify stopRingingSound()** is being called
2. **Check browser console** for audio errors
3. **Test with different browsers** if needed

## Production Considerations

- **TURN Server**: Required for production NAT traversal
- **HTTPS**: Required for WebRTC functionality
- **Error Logging**: Monitor decline/termination rates
- **User Experience**: Consider adding undo functionality for accidental declines
- **Analytics**: Track decline patterns for service improvement

## Edge Cases Handled

- ✅ User declines while still in notification popup
- ✅ User declines after joining call room
- ✅ Multiple users in same call room
- ✅ Network disconnections during decline
- ✅ Browser tab closures
- ✅ Mobile vs desktop browser differences