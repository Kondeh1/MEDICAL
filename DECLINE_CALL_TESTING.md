# Call Decline Functionality - Test Guide

## What Was Fixed

The issue was that when a user declined a call, only the declining user received feedback, but the caller didn't see any notification that the call was declined. Now both sides will properly see call status updates.

## Changes Made

1. **Enhanced WebSocket Message Handling**:
   - Added proper handling for `call_status_update` messages with `DECLINED` status
   - Added direct `call_declined` message handling
   - Both message types now show visual notifications to the caller

2. **Improved User Feedback**:
   - Caller now sees a yellow alert: "[User] declined your call"
   - Automatic popup dismissal when call is declined
   - Ringtone stops immediately when call is declined
   - 5-second notification display time

3. **Call Room Integration**:
   - Call room now handles `call_declined` messages properly
   - Shows appropriate "Call was declined" message
   - Ends call cleanly for both users

## How to Test

### Test 1: Basic Decline Functionality
1. **Setup**: Log in as provider and patient in different browser sessions
2. **Initiate call**: Provider starts a video/audio call to patient
3. **Decline call**: Patient clicks the "Decline" button in the incoming call popup
4. **Expected behavior**:
   - **Patient side**: Green confirmation "Call declined" appears, popup closes
   - **Provider side**: Yellow warning appears "Patient declined your call", popup closes, ringtone stops

### Test 2: Call Room Decline
1. **Setup**: Both users join the call room
2. **During call**: One user clicks the decline/end call button
3. **Expected behavior**:
   - Both users see "Call was declined" message
   - Both are redirected appropriately
   - Call timer stops

### Test 3: Multiple Decline Scenarios
1. **Test declining before joining**: Decline from notification popup
2. **Test declining after joining**: Decline from call room interface
3. **Test declining via popup close**: Close popup without accepting
4. **Expected behavior**: All scenarios should show proper notifications on both sides

## Expected Visual Feedback

### For the Declining User:
- Green confirmation: "Call declined" (3 seconds)
- Popup closes automatically
- Audio stops

### For the Calling User:
- Yellow warning: "[User name] declined your call" (5 seconds)
- Popup closes automatically  
- Ringtone stops
- Call state updated in database

## WebSocket Message Flow

```
Patient Declines Call:
1. Patient clicks "Decline" button
2. AJAX request to /messages/call/{call_id}/decline/
3. Server updates call status to MISSED
4. Server sends WebSocket message to caller's user group:
   {
     'type': 'call_status_update',
     'call_id': '...',
     'status': 'DECLINED',
     'message': 'Patient declined your call'
   }
5. Caller's browser receives message and shows notification
```

## Troubleshooting

### If Caller Doesn't See Notification:
1. Check browser console for JavaScript errors
2. Verify WebSocket connection is active
3. Check network tab for the AJAX decline request
4. Ensure both users are properly authenticated

### If Notification Appears but Has Wrong Text:
1. Check the message content in browser console
2. Verify the declining user's name is being retrieved correctly
3. Check the call object in database has correct user references

### If Audio Doesn't Stop:
1. Check that `stopRingingSound()` function is being called
2. Verify audio element exists and is accessible
3. Check browser console for audio-related errors

## Production Considerations

- **Push Notifications**: Consider implementing browser push notifications for declined calls
- **Email Notifications**: Send email notifications for important call events
- **Call History**: Ensure declined calls are properly logged in call history
- **Analytics**: Track decline rates and patterns for quality improvement