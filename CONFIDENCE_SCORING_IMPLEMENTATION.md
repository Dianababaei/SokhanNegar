# Confidence Scoring Implementation

## Overview

This document describes the implementation of confidence scoring from Google Speech Recognition API to help identify uncertain transcriptions that may need doctor review in psychiatric interviews.

## Changes Made

### 1. Backend Configuration

#### Constants and Logging Setup (Lines 35-48)

Added confidence scoring constants and configured a separate logger for low-confidence segments:

```python
# Confidence Scoring Constants
CONFIDENCE_THRESHOLD_LOW = 0.70      # Below 70%: needs review (red)
CONFIDENCE_THRESHOLD_MODERATE = 0.90  # 70-90%: moderate (yellow)

# Configure separate logger for low-confidence segments
confidence_logger = logging.getLogger('confidence_quality')
confidence_handler = logging.FileHandler('confidence_review.log', encoding='utf-8')
confidence_logger.addHandler(confidence_handler)
```

**Key Features:**
- Threshold boundaries clearly defined for quality assessment
- Separate logging file (`confidence_review.log`) for low-confidence segments
- Enables easy filtering and review of uncertain transcriptions

#### Color Constants (Lines 62-67)

Added confidence-based color mapping for UI display:

```python
CONFIDENCE_COLORS = {
    'high': '#00CC00',      # Green for >90% confidence
    'moderate': '#FFFF00',  # Yellow for 70-90% confidence
    'low': '#FF0000',       # Red for <70% confidence (needs review)
}
```

### 2. Google Speech Recognition API Modification

#### Enable show_all Parameter (Line 272)

Changed the recognize_google call from `show_all=False` to `show_all=True`:

```python
response = self.recognizer.recognize_google(
    audio,
    language='fa-IR',
    show_all=True  # Changed from False to enable confidence scores
)
```

**Impact:**
- API now returns a list of alternatives instead of a single best match
- Each alternative includes a confidence score (0.0-1.0)
- Enables extraction of confidence information for quality assessment

#### Response Parsing (Lines 275, 278-281)

Added response parsing and confidence extraction:

```python
text, confidence = self.parse_google_response(response)
if confidence < CONFIDENCE_THRESHOLD_LOW:
    self.log_low_confidence_segment(text, confidence)
```

### 3. Frontend Display

#### Text Widget Color Tags (Lines 164-169)

Configured tkinter text tags for color-coded confidence display:

```python
self.text_area.tag_config('confidence_high', foreground='#00CC00', background='#1a3a1a')
self.text_area.tag_config('confidence_moderate', foreground='#FFFF00', background='#3a3a1a')
self.text_area.tag_config('confidence_low', foreground='#FF0000', background='#3a1a1a')
```

**Features:**
- Three confidence levels with distinct colors
- Background highlighting for better visibility
- Non-intrusive design within existing text display area

#### Enhanced add_text Method (Lines 342-389)

Modified to display confidence inline with text:

```python
def add_text(self, text, confidence=None):
    # Insert text
    # If confidence available, append formatted indicator
    if confidence is not None and 0.0 <= confidence <= 1.0:
        confidence_pct = confidence * 100
        confidence_text = f" [{confidence_pct:.0f}%]"
        
        # Apply color tag based on threshold
        if confidence >= CONFIDENCE_THRESHOLD_MODERATE:
            tag = 'confidence_high'
        elif confidence >= CONFIDENCE_THRESHOLD_LOW:
            tag = 'confidence_moderate'
        else:
            tag = 'confidence_low'
        
        self.text_area.tag_add(tag, conf_start, conf_end)
```

**Display Format:**
- Example: `"Hello world [85%]"` with yellow coloring
- Percentage displayed inline for quick visual assessment
- Color coding indicates confidence level at a glance

### 4. Helper Functions

#### parse_google_response() (Lines 473-514)

Extracts text and confidence from Google Speech Recognition response:

```python
def parse_google_response(self, response):
    """
    Parse response to extract text and confidence score.
    When show_all=True, response is a list of alternatives.
    """
    best_alternative = response[0]
    text = best_alternative.get('transcript', '')
    confidence = best_alternative.get('confidence', None)
    
    # Validate and clamp confidence to 0.0-1.0 range
    if confidence is not None:
        confidence = float(confidence)
        confidence = max(0.0, min(1.0, confidence))
    else:
        confidence = 0.5  # Default for missing data
    
    return text, confidence
```

**Robustness Features:**
- Handles missing confidence data gracefully
- Validates confidence range (0.0-1.0)
- Returns sensible defaults on errors
- Logs warnings for debugging

#### log_low_confidence_segment() (Lines 516-534)

Logs low-confidence segments to file for quality review:

```python
def log_low_confidence_segment(self, text, confidence):
    """
    Log low-confidence transcription segments to file.
    Format: timestamp - confidence% - text
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    confidence_pct = confidence * 100
    log_entry = f"{timestamp} - Confidence: {confidence_pct:.1f}% - Text: {text}"
    confidence_logger.info(log_entry)
```

**Output Example:**
```
2024-01-15 14:23:45 - Confidence: 65.3% - Text: unclear audio segment
```

**Usage:**
- File: `confidence_review.log`
- Format: Human-readable with timestamps
- Enables easy filtering and review by clinicians

## Validation

### Confidence Value Range
- **Validated:** 0.0 to 1.0 (converted to 0-100% for display)
- **Clamping:** Values outside range are bounded
- **Default:** 0.5 (50%) if not provided by API

### Threshold Definitions
- **Low (<70%):** Red color, logged to `confidence_review.log`
- **Moderate (70-90%):** Yellow color, displayed inline
- **High (≥90%):** Green color, standard display

### Error Handling
- Missing confidence data: Gracefully fallback to default
- Invalid confidence values: Clamped to valid range
- API failures: System continues with fallback options

## Files Modified

1. **SokhanNegar.py**
   - Added confidence constants and logger configuration
   - Modified Google Speech Recognition API call
   - Enhanced text display with confidence indicators
   - Added helper functions for parsing and logging

## Files Created

1. **confidence_review.log** (automatically created)
   - Low-confidence segments logged with timestamps
   - Format: `YYYY-MM-DD HH:MM:SS - Confidence: XX.X% - Text: ...`

## Success Criteria Met

✅ Confidence scores display correctly alongside all transcriptions
✅ Color coding updates in real-time as text is transcribed
✅ Low-confidence segments (<70%) are logged to file with timestamps
✅ System handles missing confidence data without crashes
✅ Thresholds are configurable and clearly documented

## Configuration

To adjust confidence thresholds, modify these constants in SokhanNegar.py:

```python
CONFIDENCE_THRESHOLD_LOW = 0.70       # Adjust as needed
CONFIDENCE_THRESHOLD_MODERATE = 0.90   # Adjust as needed
```

## Usage Notes

### For Clinicians
- Green indicators [90%+]: High confidence, minimal review needed
- Yellow indicators [70-90%]: Moderate confidence, review recommended
- Red indicators [<70%]: Low confidence, careful review required
- All red-marked segments automatically saved to `confidence_review.log`

### For Developers
- Confidence values always in range 0.0-1.0
- Display converts to percentage format: `value * 100`
- Inline format: `text [XX%]` where XX is 0-100
- Color tags: `confidence_high`, `confidence_moderate`, `confidence_low`

## Future Enhancements

Potential improvements for future versions:
- Adjustable threshold sliders in UI
- Export confidence report functionality
- Batch review interface for flagged segments
- Confidence trend analysis over time
- Integration with Electronic Health Records (EHR)
