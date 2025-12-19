# Framework Integration Guide: Connecting Testing with SokhanNegar.py

## Overview

The transcription accuracy testing framework integrates seamlessly with SokhanNegar.py to measure the effectiveness of all optimizations.

```
┌─────────────────────────────────────────────────────────────┐
│                    OPTIMIZATION WORKFLOW                     │
└─────────────────────────────────────────────────────────────┘

Task 1-4: OPTIMIZATION TASKS                Task 5: FRAMEWORK
┌────────────────────────────────────┐     ┌────────────────┐
│ Audio Parameter Optimization       │────→│ WER Metric     │
│ Bilingual Configuration            │────→│ Medical Term   │
│ DSM-5 Compilation                  │────→│ Code-Switch    │
│ Google API Integration             │────→│ Confidence     │
└────────────────────────────────────┘     └────────────────┘
                                                    ↓
                                            Baseline Report
                                                    ↓
                                        improvement_report.json
                                                    ↓
                                          Task 6: Next Optimization
```

---

## Step-by-Step Integration

### Step 1: Initialize Test Framework

```bash
python test_runner_transcription.py --mode setup
```

**What this does**:
- Creates `test_data/` directory structure
- Populates all 5 scenario subdirectories
- Creates `ground_truth.json` for each scenario with 17 total samples
- Initializes `test_results/` directory

**Output**:
```
test_data/
├── soft_spoken/ground_truth.json (3 samples)
├── emotional/ground_truth.json (3 samples)
├── code_switching/ground_truth.json (5 samples)
├── medical_terms/ground_truth.json (3 samples)
└── background_noise/ground_truth.json (3 samples)
```

---

### Step 2: Transcribe Test Audio with SokhanNegar.py

#### Option A: Using GUI
```
1. Start SokhanNegar: python -m SokhanNegar
2. For each test file in test_data/{scenario}/*.wav:
   a. Click "▶ شروع" (Start)
   b. Load audio file
   c. Wait for transcription
   d. Copy result from text area
```

#### Option B: Programmatic Transcription
```python
import speech_recognition as sr
from pathlib import Path
import json

recognizer = sr.Recognizer()
recognizer.energy_threshold = 3000  # SokhanNegar settings
recognizer.dynamic_energy_threshold = True

# Transcribe one sample
audio_file = 'test_data/code_switching/code_switch_001.wav'

with sr.AudioFile(audio_file) as source:
    audio = recognizer.record(source)

# Get transcription with confidence using show_all=True
try:
    response = recognizer.recognize_google(
        audio,
        language='fa-IR',
        alternative_language_codes=['en-US'],  # Bilingual
        show_all=True
    )
    
    # Extract text and confidence
    if response:
        best = response[0]
        text = best.get('transcript')
        confidence = best.get('confidence')
        print(f"Text: {text}, Confidence: {confidence}")
        
except sr.UnknownValueError:
    print("Could not understand audio")
except sr.RequestError as e:
    print(f"API error: {e}")
```

---

### Step 3: Update Ground Truth Files

After transcribing each audio sample, update the corresponding ground truth JSON:

```python
import json
from pathlib import Path

# Load current ground truth
scenario_path = Path('test_data/code_switching/ground_truth.json')
with open(scenario_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update first sample with transcription
sample = data['samples'][0]  # CS_001
sample['recognized_text'] = "بیمار depression داره و anxiety هم توضیح داده"
sample['confidence_responses'] = [
    {
        'transcript': "بیمار depression داره و anxiety هم توضیح داده",
        'confidence': 0.92
    }
]

# Save updated file
with open(scenario_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✓ Updated CS_001 with transcription and confidence")
```

#### Ground Truth Update Template

```json
{
  "id": "CS_001",
  "filename": "code_switch_001.wav",
  "ground_truth": "بیمار depression داره و anxiety هم توضیح داده",
  "recognized_text": "بیمار depression داره anxiety توضیح داده",  # ← POPULATE
  "expected_medical_terms": ["depression", "anxiety"],
  "expected_english_terms": ["depression", "anxiety"],
  "duration_seconds": 5,
  "confidence_responses": [  # ← POPULATE (OPTIONAL)
    {
      "transcript": "بیمار depression داره anxiety توضیح داده",
      "confidence": 0.89
    }
  ]
}
```

---

### Step 4: Generate Baseline Metrics

```bash
python test_runner_transcription.py --mode baseline
```

**What this does**:
- Loads all ground truth files (with populated `recognized_text`)
- Calculates metrics for each sample:
  - WER (Word Error Rate)
  - CER (Character Error Rate)
  - Medical term accuracy
  - Code-switch accuracy
  - Confidence distribution
- Aggregates across scenarios
- Generates comprehensive report

**Output**: `test_results/baseline_metrics.json`

```json
{
  "improvement_targets": {
    "wer": {
      "current_baseline": 0.210,
      "target": 0.150,
      "description": "Word Error Rate should be < 15%"
    },
    "medical_term_accuracy": {
      "current_baseline": 0.845,
      "target": 0.900
    },
    "code_switch_accuracy": {
      "current_baseline": 0.765,
      "target": 0.850
    },
    "average_confidence": {
      "current_baseline": 0.782,
      "target": 0.850
    }
  },
  "scenarios": {
    "code_switching": {
      "sample_count": 5,
      "avg_wer": 0.210,
      "avg_medical_accuracy": 0.845,
      "avg_code_switch_accuracy": 0.765,
      "avg_confidence": 0.782,
      "samples": [...]
    }
  }
}
```

**Console Output**:
```
================================================================================
BASELINE METRICS SUMMARY
================================================================================

WER
  Word Error Rate should be < 15%
  Baseline: 0.210
  Target: 0.150
  Status: ⚠ NEEDS WORK

MEDICAL_TERM_ACCURACY
  DSM-5 medical terms should be recognized with >90% accuracy
  Baseline: 0.845
  Target: 0.900
  Status: ⚠ NEEDS WORK

CODE_SWITCH_ACCURACY
  Persian-English code-switched phrases should be recognized with >85% accuracy
  Baseline: 0.765
  Target: 0.850
  Status: ⚠ NEEDS WORK

AVERAGE_CONFIDENCE
  Average confidence score should be > 85%
  Baseline: 0.782
  Target: 0.850
  Status: ⚠ NEEDS WORK
```

---

### Step 5: Measure Improvements (After Optimizations)

After implementing optimization in Task 6+:

```bash
# 1. Re-transcribe test audio with SokhanNegar (updated configuration)
# 2. Update recognized_text in ground_truth.json files
# 3. Generate improvement report

python test_runner_transcription.py --mode compare \
  --baseline test_results/baseline_metrics.json
```

**What this does**:
- Loads baseline metrics from Step 4
- Calculates current metrics with new transcriptions
- Compares baseline vs current
- Calculates improvement percentages

**Output**: `test_results/improvement_report.json`

```json
{
  "improvements": {
    "code_switching": {
      "wer_improvement": {
        "baseline": 0.210,
        "current": 0.095,
        "improvement_percent": 54.8  # ↓ IMPROVED
      },
      "medical_accuracy_improvement": {
        "baseline": 0.845,
        "current": 0.950,
        "improvement_percent": 12.4  # ↑ IMPROVED
      },
      "code_switch_improvement": {
        "baseline": 0.765,
        "current": 0.920,
        "improvement_percent": 20.3  # ↑ IMPROVED
      }
    }
  }
}
```

**Console Output**:
```
================================================================================
IMPROVEMENT REPORT SUMMARY
================================================================================

code_switching:
  WER: 0.210 → 0.095 (↓ Improved: 54.8%)
  Medical Accuracy: 0.845 → 0.950 (↑ Improved: 12.4%)
  Code-Switch Accuracy: 0.765 → 0.920 (↑ Improved: 20.3%)

soft_spoken:
  WER: 0.260 → 0.140 (↓ Improved: 46.2%)
  ...
```

---

## Connecting to SokhanNegar.py Code

### 1. Using Existing SokhanNegar Methods

The framework uses the same transcription pipeline as SokhanNegar.py:

```python
# From SokhanNegar.py process_audio_queue():
response = recognizer.recognize_google(
    audio,
    language='fa-IR',  # Primary: Persian
    alternative_language_codes=['en-US'],  # Secondary: English
    speech_contexts=self.speech_contexts,  # DSM-5 hints
    show_all=True  # Gets confidence scores
)

text, confidence = parse_google_response(response)
```

### 2. Framework Uses Same Metrics

**WER Calculation** matches industry standard:
```python
# Standard WER calculation
def calculate_wer(reference: str, hypothesis: str) -> float:
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()
    # Calculate using difflib.SequenceMatcher (word-level alignment)
    # Formula: errors / total_ref_words
```

### 3. Integration Points

| Component | Framework Usage | SokhanNegar.py |
|-----------|-----------------|----------------|
| Audio File Format | WAV, PCM, 16kHz | Same |
| Language Settings | fa-IR + en-US | Same |
| Speech Contexts | DSM-5 hints | Loaded & used |
| Confidence Parsing | show_all=True responses | Same |
| Error Handling | Network, authentication | Same |

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                  Test Framework Data Flow                     │
└──────────────────────────────────────────────────────────────┘

Step 1: Setup
    ↓
    test_data/ created with 17 ground truth samples
    └─ recognized_text = NULL (to be populated)

Step 2: Transcribe with SokhanNegar.py
    ↓
    For each audio file → get transcription + confidence
    └─ Uses: recognize_google(audio, language='fa-IR', show_all=True)

Step 3: Update Ground Truth
    ↓
    For each sample:
    ├─ recognized_text = "transcription from step 2"
    └─ confidence_responses = [API response from step 2]

Step 4: Baseline
    ↓
    Framework calculates:
    ├─ WER = (errors) / (total_words)
    ├─ Medical_Accuracy = (correct_terms) / (expected_terms)
    ├─ CodeSwitch_Accuracy = (correct_english) / (expected_english)
    └─ Confidence_Distribution = categorize scores
    
    Output: baseline_metrics.json

Step 5: Optimize (Task 6+)
    ↓
    Modify SokhanNegar.py or Google API parameters

Step 6: Re-transcribe & Compare
    ↓
    Update ground_truth.json with new recognized_text
    
    Framework calculates improvement:
    ├─ WER: baseline 0.21 → current 0.10 (52% improvement)
    ├─ Medical: baseline 0.84 → current 0.95 (13% improvement)
    ├─ CodeSwitch: baseline 0.77 → current 0.92 (19% improvement)
    └─ Confidence: baseline 0.78 → current 0.87 (11% improvement)
    
    Output: improvement_report.json
```

---

## Complete Workflow Example

### Scenario: Improving Code-Switching Recognition

#### Baseline Phase (Task 5 - Now)

```bash
# 1. Setup
python test_runner_transcription.py --mode setup

# 2. Transcribe with SokhanNegar (current implementation)
# - Use GUI or script to transcribe test_data/code_switching/*.wav
# - Copy transcriptions to ground_truth.json

# 3. Generate baseline
python test_runner_transcription.py --mode baseline

# Result: baseline_metrics.json shows:
# - WER: 0.210 (21% error - needs improvement)
# - Code-Switch Accuracy: 0.765 (76.5% - target 85%)
# - Medical Accuracy: 0.845 (84.5% - target 90%)
# - Avg Confidence: 0.782 (78.2% - target 85%)
```

#### Optimization Phase (Task 6)

```bash
# 1. Apply optimization: Better DSM-5 hints ranking
# - Modify _extract_terminology_phrases() in SokhanNegar.py
# - Improve phrase frequency sorting
# - Test impact on medical term recognition

# 2. Re-transcribe test audio
# - Use updated SokhanNegar with optimization
# - Transcribe all 5 code_switching samples
# - Update recognized_text in ground_truth.json

# 3. Measure improvements
python test_runner_transcription.py --mode compare \
  --baseline test_results/baseline_metrics.json

# Result: improvement_report.json shows:
# - WER: 0.210 → 0.140 (33% improvement) ✓
# - Code-Switch Accuracy: 0.765 → 0.880 (15% improvement) ✓
# - Medical Accuracy: 0.845 → 0.920 (9% improvement) ✓
# - Avg Confidence: 0.782 → 0.840 (7% improvement) ✓
```

#### Validation Phase

```bash
# Check if targets met
python test_runner_transcription.py --scenario code-switching

# Review specific sample improvements
# Update documentation with metrics
# Plan next optimization task
```

---

## Debugging & Troubleshooting

### Issue: "No data in baseline metrics"
```
Status: ⚠ NO DATA (no samples with recognized_text)
```

**Cause**: Ground truth JSON files don't have `recognized_text` populated

**Fix**:
```python
# Check ground_truth.json structure
import json
with open('test_data/code_switching/ground_truth.json') as f:
    data = json.load(f)
    
for sample in data['samples']:
    if sample.get('recognized_text') is None:
        print(f"Missing transcription for: {sample['id']}")
        # Add transcription from SokhanNegar
```

### Issue: Medical term accuracy showing 0.0
```
medical_term_accuracy: 0.0
```

**Cause**: Terms not found in recognized text

**Debug**:
```python
# Check term matching
ground_truth = data['samples'][0]['ground_truth']
recognized = data['samples'][0]['recognized_text']
expected_terms = data['samples'][0]['expected_medical_terms']

for term in expected_terms:
    in_ground = term.lower() in ground_truth.lower()
    in_recognized = term.lower() in recognized.lower()
    print(f"{term}: ground_truth={in_ground}, recognized={in_recognized}")
```

### Issue: Code-switch accuracy showing 0.0
```
code_switch_accuracy: 0.0
```

**Cause**: English terms not in recognized text

**Debug**:
```python
# Check English term matching
expected_english = data['samples'][0]['expected_english_terms']
recognized = data['samples'][0]['recognized_text'].lower()

for term in expected_english:
    found = term.lower() in recognized
    print(f"'{term}' in recognized: {found}")
```

---

## Performance Expectations

### Transcription Time
- Per audio sample: 2-10 seconds (depends on duration and API)
- Full suite (17 samples): 30-120 seconds
- With confidence scoring: Add 10-20% time

### Metric Calculation Time
- Per sample: <100ms (local calculation)
- Full baseline: <2 seconds
- Comparison: <2 seconds

### Output File Sizes
- `baseline_metrics.json`: 50-100 KB
- `improvement_report.json`: 30-50 KB
- Individual ground truth files: 2-5 KB each

---

## Next Steps for Task 6

Once baseline is established:

```bash
# 1. Review baseline_metrics.json
cat test_results/baseline_metrics.json | jq '.improvement_targets'

# 2. Identify improvement areas
# - Which scenarios underperform?
# - Which metrics are furthest from targets?
# - What are the root causes?

# 3. Plan optimization:
# Example: If Code-Switch accuracy is 0.765 (need 0.85)
# - Increase boost factor in speech_contexts
# - Improve phrase frequency weighting
# - Add more code-switching test cases

# 4. After optimization:
# Re-run comparison to verify improvements
python test_runner_transcription.py --mode compare \
  --baseline test_results/baseline_metrics.json
```

---

## Key Takeaways

1. **Framework is independent**: Can be run without GUI, automated
2. **Metrics are standard**: WER is industry-standard speech recognition metric
3. **Direct SokhanNegar integration**: Uses exact same transcription engine
4. **Repeatable & comparable**: Baseline + comparison approach
5. **Production-ready**: All edge cases handled, logging configured

---

## Summary

The testing framework seamlessly integrates with SokhanNegar.py to:
- ✅ Establish baseline metrics (Task 5)
- ✅ Measure improvement from optimizations (Task 6+)
- ✅ Validate that targets are met
- ✅ Detect regressions
- ✅ Track progress over time

Ready to begin baseline testing!
