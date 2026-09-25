# Call Time Restrictions Implementation

## Feature
Implemented time-based call restrictions where:
- **Providers** can call patients at any time
- **Patients** can only call providers during the scheduled appointment time

## How It Works

### For Providers
- No restrictions
- Can initiate video/audio calls anytime
- Call buttons are always enabled

### For Patients
- Can only call during the appointment time window
- Call buttons are disabled outside the scheduled time
- Buttons show helpful messages explaining when calls are available

## Implementation Details

### 1. Appointment Time Data
Added appointment time data to call buttons:
```html
data-appointment-date="{{ appointment.date|date:'Y-m-d' }}"
data-appointment-start="{{ appointment.start_time|time:'H:i' }}"
data-appointment-end="{{ appointment.end_time|time:'H:i' }}"
```

### 2. Permission Check Function
```javascript
function checkCallPermission() {
  const isPatient = startVideoCallBtn.getAttribute('data-is-patient') === 'true';
  
  // Providers can always call
  if (!isPatient) {
    return { allowed: true, message: '' };
  }
  
  // For patients, check appointment time
  const now = new Date();
  const currentDate = now.toISOString().split('T')[0];
  const currentTime = now.toTimeString().split(' ')[0].substring(0, 5);
  
  // Check if it's the appointment date
  if (currentDate !== appointmentDate) {
    return { 
      allowed: false, 
      message: `Call available on ${appointmentDate}` 
    };
  }
  
  // Check if current time is within appointment window
  if (currentTime < appointmentStart) {
    return { 
      allowed: false, 
      message: `Call available at ${appointmentStart}` 
    };
  }
  
  if (currentTime > appointmentEnd) {
    return { 
      allowed: false, 
      message: `Appointment ended at ${appointmentEnd}` 
    };
  }
  
  return { allowed: true, message: '' };
}
```

### 3. Button State Updates
```javascript
function updateCallButtonStates() {
  const permission = checkCallPermission();
  
  if (!permission.allowed) {
    // Disable buttons for patients outside appointment time
    startVideoCallBtn.disabled = true;
    startAudioCallBtn.disabled = true;
    startVideoCallBtn.setAttribute('data-disabled-message', permission.message);
    startAudioCallBtn.setAttribute('data-disabled-message', permission.message);
  } else {
    // Enable buttons
    startVideoCallBtn.disabled = false;
    startAudioCallBtn.disabled = false;
  }
}
```

### 4. Real-Time Updates
- Button states are checked on page load
- States are updated every minute automatically
- Ensures buttons enable/disable at the right time

### 5. Click Prevention
Added permission checks before starting calls:
```javascript
startVideoCallBtn.addEventListener('click', () => {
  const permission = checkCallPermission();
  if (!permission.allowed) {
    alert(permission.message);
    return;
  }
  startCall(true);
});
```

## User Experience

### Patient Before Appointment Time
- Call buttons are disabled (grayed out)
- Hovering shows message: "Call available at HH:MM"
- Clicking shows alert with the same message

### Patient During Appointment Time
- Call buttons are enabled
- Can initiate video/audio calls normally
- Full call functionality available

### Patient After Appointment Time
- Call buttons are disabled
- Hovering shows message: "Appointment ended at HH:MM"
- Clicking shows alert with the same message

### Provider (Anytime)
- Call buttons are always enabled
- No time restrictions
- Can call patients anytime

## Visual Feedback

### Disabled Button Styling
```css
.btn-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

### Tooltip on Hover
```css
.btn-action.disabled-with-message::after {
  content: attr(data-disabled-message);
  /* Tooltip styling */
}
```

## Time Checking Logic

### Date Check
- Compares current date with appointment date
- Format: YYYY-MM-DD

### Time Check
- Compares current time with appointment start/end times
- Format: HH:MM (24-hour)
- Checks if current time is within the window

### Example Scenarios

#### Scenario 1: Too Early
- Appointment: 2026-02-26 14:00-15:00
- Current: 2026-02-26 13:30
- Result: Disabled - "Call available at 14:00"

#### Scenario 2: During Appointment
- Appointment: 2026-02-26 14:00-15:00
- Current: 2026-02-26 14:30
- Result: Enabled - Can call

#### Scenario 3: Too Late
- Appointment: 2026-02-26 14:00-15:00
- Current: 2026-02-26 15:30
- Result: Disabled - "Appointment ended at 15:00"

#### Scenario 4: Wrong Date
- Appointment: 2026-02-26 14:00-15:00
- Current: 2026-02-25 14:30
- Result: Disabled - "Call available on 2026-02-26"

## Benefits

1. **Prevents Unwanted Calls**: Patients can't call outside scheduled times
2. **Clear Communication**: Users know exactly when they can call
3. **Provider Flexibility**: Providers can reach patients anytime
4. **Automatic Updates**: Button states update in real-time
5. **User-Friendly**: Clear messages explain restrictions

## Testing

### Test as Patient

#### Before Appointment Time
1. Open consultation room before appointment start time
2. Verify call buttons are disabled
3. Hover over buttons - should show "Call available at HH:MM"
4. Try clicking - should show alert with message

#### During Appointment Time
1. Open consultation room during appointment window
2. Verify call buttons are enabled
3. Should be able to initiate calls normally

#### After Appointment Time
1. Open consultation room after appointment end time
2. Verify call buttons are disabled
3. Hover over buttons - should show "Appointment ended at HH:MM"

### Test as Provider
1. Open consultation room at any time
2. Verify call buttons are always enabled
3. Should be able to initiate calls anytime

### Test Auto-Update
1. Open consultation room as patient 2 minutes before appointment
2. Wait for appointment time to arrive
3. Buttons should automatically enable after 1 minute

## Files Modified
- `consultations/templates/consultations/room.html`
  - Added appointment time data attributes
  - Added permission check function
  - Added button state update function
  - Added click prevention logic
  - Added disabled button styling

## Status: COMPLETE ✓
Call time restrictions are now enforced for patients while providers can call anytime.
