# Prescription Sending Fix

## Issue
When trying to send a prescription in the chat room, the error message "An error occurred while sending the prescription" appeared.

## Root Cause
The consultation view was trying to create a `Prescription` object with fields that don't exist in the model:
- `doctor` (should be `provider`)
- `medication`, `dosage`, `frequency`, `duration` (these belong to `PrescriptionItem`, not `Prescription`)

### Prescription Model Structure
```python
# Prescription (main record)
- patient (ForeignKey)
- provider (ForeignKey)  # NOT 'doctor'
- consultation (ForeignKey, optional)
- notes (TextField)
- created_at (DateTimeField)

# PrescriptionItem (medication details)
- prescription (ForeignKey)
- medication_name (CharField)  # NOT 'medication'
- dosage (CharField)
- frequency (CharField)
- duration (CharField)
- instructions (TextField)
```

## Solution

### Backend Fix (`consultations/views.py`)

**Before** (Incorrect):
```python
prescription = Prescription.objects.create(
    patient=appointment.patient,
    doctor=appointment.provider,  # ❌ Wrong field name
    medication=medication,  # ❌ Field doesn't exist
    dosage=dosage,  # ❌ Field doesn't exist
    frequency=frequency,  # ❌ Field doesn't exist
    duration=duration,  # ❌ Field doesn't exist
    notes=notes
)
```

**After** (Correct):
```python
# Create the prescription
prescription = Prescription.objects.create(
    patient=appointment.patient,
    provider=appointment.provider,  # ✓ Correct field name
    consultation=consultation,  # ✓ Link to consultation
    notes=notes
)

# Create prescription item with medication details
PrescriptionItem.objects.create(
    prescription=prescription,
    medication_name=medication,  # ✓ Correct field name
    dosage=dosage,
    frequency=frequency,
    duration=duration,
    instructions=notes
)
```

### Enhanced Error Handling

Added try-except block to catch and report errors:
```python
try:
    # Create prescription and item
    # ...
    return JsonResponse({'success': True})
except Exception as e:
    logger.error(f"Error creating prescription: {str(e)}")
    return JsonResponse({'success': False, 'error': str(e)}, status=400)
```

Added validation for required fields:
```python
if medication and dosage and frequency and duration:
    # Create prescription
else:
    error_msg = "All fields (medication, dosage, frequency, duration) are required."
    return JsonResponse({'success': False, 'error': error_msg}, status=400)
```

### Frontend Fix (`consultations/templates/consultations/room.html`)

**Enhanced Error Display**:
- Now shows the actual error message from the server
- Displays error as a toast notification (not just console.log)
- Error notification auto-dismisses after 5 seconds

```javascript
.catch(error => {
  console.error('Error:', error);
  
  // Show error message as toast
  const errorMsg = document.createElement('div');
  errorMsg.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
  errorMsg.style.zIndex = '9999';
  errorMsg.innerHTML = `
    <i class="bi bi-exclamation-triangle-fill me-2"></i>
    Error: ${error.message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  document.body.appendChild(errorMsg);
  
  // Remove after 5 seconds
  setTimeout(() => errorMsg.remove(), 5000);
});
```

## Changes Made

### File: `consultations/views.py`

1. **Fixed field names**:
   - Changed `doctor` to `provider`
   - Removed non-existent fields from Prescription creation

2. **Added PrescriptionItem creation**:
   - Properly creates medication details in separate table

3. **Added error handling**:
   - Try-except block catches all errors
   - Returns proper JSON error responses
   - Validates required fields

4. **Added logging**:
   - Logs errors for debugging

### File: `consultations/templates/consultations/room.html`

1. **Enhanced error handling**:
   - Checks response status
   - Extracts error message from response
   - Shows error as toast notification

2. **Better user feedback**:
   - Success notification (green)
   - Error notification (red)
   - Auto-dismiss after timeout

## Testing

### Test 1: Send Valid Prescription
1. Log in as provider
2. Open consultation room
3. Click prescription button (💊)
4. Fill in all fields:
   - Medication: "Amoxicillin"
   - Dosage: "500mg"
   - Frequency: "3 times daily"
   - Duration: "7 days"
   - Notes: "Take with food"
5. Click "Send Prescription"
6. **Expected**:
   - Button shows "Sending..."
   - Modal closes
   - Green success notification appears
   - Prescription appears in chat

### Test 2: Send Prescription with Missing Fields
1. Open prescription modal
2. Fill in only some fields (e.g., just medication)
3. Click "Send Prescription"
4. **Expected**:
   - Red error notification appears
   - Error message: "All fields (medication, dosage, frequency, duration) are required."
   - Modal stays open
   - Form data is preserved

### Test 3: Verify Database
After sending a prescription, check the database:
```python
from prescriptions.models import Prescription, PrescriptionItem

# Check prescription was created
prescription = Prescription.objects.last()
print(f"Patient: {prescription.patient}")
print(f"Provider: {prescription.provider}")
print(f"Consultation: {prescription.consultation}")

# Check prescription item was created
item = prescription.items.first()
print(f"Medication: {item.medication_name}")
print(f"Dosage: {item.dosage}")
print(f"Frequency: {item.frequency}")
print(f"Duration: {item.duration}")
```

### Test 4: Verify Message
Check that the prescription message was created:
```python
from messaging.models import Message

# Check message was created
message = Message.objects.filter(message_type='PRESCRIPTION').last()
print(f"Content: {message.content}")
print(f"Prescription ID: {message.prescription.id}")
```

## Benefits

1. **Correct Data Structure**: Prescriptions now use the proper model structure
2. **Better Error Messages**: Users see specific error messages instead of generic ones
3. **Proper Validation**: Required fields are validated before database operations
4. **Error Logging**: Errors are logged for debugging
5. **Better UX**: Toast notifications instead of alert() dialogs

## Files Modified

1. `consultations/views.py` - Fixed prescription creation logic
2. `consultations/templates/consultations/room.html` - Enhanced error display

## Status: FIXED ✓

Prescriptions can now be sent successfully from the chat room.
