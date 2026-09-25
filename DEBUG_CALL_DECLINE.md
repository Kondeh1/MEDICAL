# Call Decline Debugging and Testing Guide

## Current Implementation Status

I've implemented complete call termination when a user declines a call. The system now sends multiple WebSocket messages to ensure both users see the call end properly.

## What Should Happen When User Declines

1. **User clicks "Decline" button** in notification popup
2. **AJAX request sent** to `/messages/call/{call_id}/decline/`
3. **Server processes decline**:
   - Updates call status to MISSED
   - Sends `call_status_update` to caller's personal group (shows notification)
   - Sends `call_ended` to caller's personal group (triggers termination)
   - Sends `call_ended` to call room group (for users who joined)
4. **Both users receive messages**:
   - Declining user: Green "Call declined" confirmation
   - Calling user: Blue "Call ended by [User]" notification
   - Both: Call popups close, audio stops
   - Both: Proper redirection/cleanup

## Debugging Steps

### 1. Check Browser Console (F12 Developer Tools)
Open the browser console and look for:
```
WebSocket message received: call_status_update
WebSocket message received: call_ended
Full message data: {type: "call_ended", message: "Call declined by...", ...}
```

### 2. Check Server Logs
Look for these messages in the terminal:
```
Call details: ID=XX, Room=XXXX-XXXX-XXXX, Caller=username, Decliner=username
Sending decline notification to caller group: user_XX
Sending call_ended to caller group: user_XX
Sending call_ended to room group: call_XXXX-XXXX-XXXX
Successfully sent all WebSocket messages for call termination
```

### 3. Test Scenarios

#### Test 1: Decline from Notification Popup (Most Common)
1. Log in as provider and patient in different browsers
2. Provider initiates call to patient
3. Patient sees incoming call popup
4. Patient clicks "Decline" button
5. **Expected**: Both users see appropriate notifications, popups close, audio stops

#### Test 2: Decline from Call Room
1. Both users join the call room
2. One user clicks the decline/end call button
3. **Expected**: Both users see "Call ended" message and are redirected

#### Test 3: Multiple Users in Call Room
1. Provider initiates call
2. Patient joins call room
3. Additional user joins (if possible)
4. Any user declines
5. **Expected**: All users see termination, all connections closed

## Common Issues and Solutions

### Issue 1: Only Notifications Show, No Call Termination
**Check**: Browser console for `call_ended` message receipt
**Solution**: Verify WebSocket connection is active for both users

### Issue 2: Server Messages Not Sent
**Check**: Server logs for the debugging print statements
**Solution**: Verify Redis is running and channel layer is configured

### Issue 3: One User Doesn't Receive Messages
**Check**: That user's WebSocket connection in browser console
**Solution**: Refresh the page to re-establish WebSocket connection

### Issue 4: Audio Doesn't Stop
**Check**: Console for `stopRingingSound()` calls
**Solution**: Browser audio policies might block autoplay

## Testing with Preview Browser

1. **Click the preview browser button** to open the application
2. **Open two browser windows/tabs** with different user accounts
3. **Initiate a call** from one user to another
4. **Decline the call** and observe both sides
5. **Check browser consoles** in both windows for debugging info

## What to Look For in Console Output

### Successful Decline:
```
WebSocket message received: call_declined
Full message data: {type: "call_declined", message: "Call declined by User"}
Call ended event received by user username: {type: "call_ended", message: "Call declined by User", ...}
```

### Server Side (Terminal):
```
Call details: ID=38, Room=abcd-1234-efgh, Caller=provider, Decliner=patient
Sending decline notification to caller group: user_2
Sending call_ended to caller group: user_2
Sending call_ended to room group: call_abcd-1234-efgh
Successfully sent all WebSocket messages for call termination
```

## If Still Not Working

1. **Hard refresh** both browser windows (Ctrl+F5)
2. **Clear browser cache** and cookies for localhost
3. **Check network tab** in developer tools for failed WebSocket connections
4. **Verify users are properly authenticated** in both sessions
5. **Test with simple audio call** first (easier debugging than video)

The implementation should now provide complete call termination on decline. The debugging output will help identify exactly where the process might be failing.