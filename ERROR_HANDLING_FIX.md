# Error Handling Fix for ISO Diff System

## Problem
When users upload incompatible ISO standards (e.g., different parts like ISO 10993-18 and ISO 10993-17), they see a generic error message: "Failed to process differences"

This doesn't explain WHY the diff failed or what to do about it.

## Root Cause
1. Backend correctly identifies incompatible documents and raises ValueError
2. API endpoint was catching this as generic Exception and returning HTTP 500
3. Frontend was only showing generic "Failed to process differences" message

## Solution Implemented

### Backend Changes (`regulatory_upload.py`)

**Before:**
```python
except Exception as e:
    logger.error(f"Failed to process ISO diff: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

**After:**
```python
except ValueError as ve:
    # ValueError is raised for incompatible documents
    error_msg = str(ve)
    logger.warning(f"Document compatibility issue: {error_msg}")
    
    raise HTTPException(
        status_code=400,  # Bad Request, not Internal Error
        detail={
            'error': 'INCOMPATIBLE_DOCUMENTS',
            'message': error_msg,
            'hint': 'Please ensure you are uploading two different versions (years) of the same ISO standard part.',
            'examples': [
                '✅ Valid: ISO 10993-18:2005 and ISO 10993-18:2020',
                '❌ Invalid: ISO 10993-18:2020 and ISO 10993-17:2023 (different parts)',
                '❌ Invalid: ISO 10993-18:2020 and ISO 14971:2019 (different series)'
            ]
        }
    )
```

### Frontend Changes (`RegulatoryDashboard.js`)

**Before:**
```javascript
} catch (error) {
  console.error(error);
  toast.error('Failed to process differences', { id: 'diff' });
}
```

**After:**
```javascript
} catch (error) {
  console.error('Diff processing error:', error);
  
  // Extract detailed error message from API response
  let errorMessage = 'Failed to process differences';
  
  if (error.response?.data) {
    const errorData = error.response.data;
    
    if (typeof errorData === 'object' && errorData.detail) {
      if (typeof errorData.detail === 'object') {
        // Structured error with message and examples
        errorMessage = errorData.detail.message || errorMessage;
        
        // Show hint if available
        if (errorData.detail.hint) {
          toast.error(errorMessage, { id: 'diff', duration: 6000 });
          setTimeout(() => {
            toast.info(errorData.detail.hint, { duration: 8000 });
          }, 500);
        }
      } else {
        // Simple error string
        errorMessage = errorData.detail;
      }
    }
  }
  
  toast.error(errorMessage, { id: 'diff', duration: 6000 });
}
```

## Expected User Experience

### Scenario 1: Valid Diff (Same Part, Different Years)
```
User uploads: ISO 10993-18:2005 and ISO 10993-18:2020
Result: ✅ Diff generated successfully
Message: "Found 33 changes"
```

### Scenario 2: Invalid Diff (Different Parts)
```
User uploads: ISO 10993-18:2020 and ISO 10993-17:2023
Result: ❌ Error with explanation
Message: "Cannot diff ISO 10993-18:2020 and ISO 10993-17:2023. 
         Standards ISO 10993-18:2020 and ISO 10993-17:2023 are 
         companion documents. These should not be diffed against 
         each other. They serve different purposes in the regulatory process."
         
Hint: "Please ensure you are uploading two different versions (years) 
       of the same ISO standard part."
```

### Scenario 3: Invalid Diff (Different Series)
```
User uploads: ISO 10993-18:2020 and ISO 14971:2019
Result: ❌ Error with explanation
Message: "Cannot compare ISO 10993-18:2020 with ISO 14971-1:2019.
         Different standard series: ISO 10993 vs ISO 14971"
```

## Testing

### Manual Test
1. Login to the application
2. Navigate to Tab 1 (Regulatory Analysis)
3. Upload ISO 10993-18:2020 as "Old"
4. Upload ISO 10993-17:2023 as "New"
5. Click "Generate Diff"
6. Verify error message is clear and helpful

### Expected Result
- Error toast appears with detailed explanation
- Follow-up hint toast provides guidance
- No generic "Failed to process differences" message

## Files Modified
- `/app/backend/api/regulatory_upload.py` - Enhanced error handling
- `/app/frontend/src/components/RegulatoryDashboard.js` - Better error display

## Status
✅ Backend changes implemented
✅ Frontend changes implemented
⏳ Ready for user testing

