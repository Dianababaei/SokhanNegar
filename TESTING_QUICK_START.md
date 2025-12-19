# Testing Framework Quick Start Guide

## TL;DR - 30 Second Setup

```bash
# 1. Initialize test data
python test_runner_transcription.py --mode setup

# 2. Run SokhanNegar to transcribe test audio files
# 3. Update ground_truth.json with recognized_text field
# 4. Establish baseline
python test_runner_transcription.py --mode baseline

# 5. After optimizations, measure improvements
python test_runner_transcription.py --mode compare \
  --baseline test_results/baseline_metrics.json
```

---

## What Was Built

✅ **Comprehensive Testing Framework** for transcription accuracy measurement

### Components Created

1. **`test_transcription_accuracy.py`** (622 lines)
   - WordErrorRateCalculator: WER/CER calculation
   - MedicalTermAccuracyChecker: DSM-5 term validation
   - CodeSwitchAccuracyChecker: Persian-English phrase validation  
   - ConfidenceScoreAnalyzer: Google API confidence analysis
   - TranscriptionAccuracyFramework: Main orchestrator

2. **`test_runner_transcription.py`** (387 lines)
   - TestRunnerManager: Test execution orchestration
   - Baseline metric generation
   - Improvement tracking
   - Scenario-specific testing

3. **Documentation**
   - `TESTING_FRAMEWORK_GUIDE.md` - Comprehensive guide (400+ lines)
   - `TESTING_QUICK_START.md` - This file

### Test Data Structure

```
test_data/
├── soft_spoken/                 # 3 samples: Low-volume depressed speech
│   ├── ground_truth.json
│   └── *.wav files
├── emotional/                   # 3 samples: Emotional variations
│   ├── ground_truth.json
│   └── *.wav files
├── code_switching/              # 5 samples: Persian-English mixing
│   ├── ground_truth.json
│   └── *.wav files
├── medical_terms/               # 3 samples: DSM-5 terminology
│   ├── ground_truth.json
│   └── *.wav files
└── background_noise/            # 3 samples: Clinic environment noise
    ├── ground_truth.json
    └── *.wav files

Total: 17 ground truth samples across 5 scenarios
```

---

## Key Metrics

### 1. Word Error Rate (WER)
- **What**: % of words incorrectly transcribed
- **Target**: < 15% (1-2 errors per 10 words acceptable)
- **Calculation**: (Substitutions + Deletions + Insertions) / Total Words

### 2. Medical Term Accuracy  
- **What**: % of DSM-5 psychiatric terms correctly recognized
- **Target**: > 90% (critical for diagnosis)
- **Coverage**: 186 DSM-5 terms (English + Persian)

### 3. Code-Switch Accuracy
- **What**: % of English-Persian phrases correctly transcribed
- **Target**: > 85% (Iranian medical context)
- **Scenarios**: 8 code-switching patterns tested

### 4. Confidence Distribution
- **What**: Google API confidence scores (0.0-1.0)
- **Target**: > 85% average, 60%+ high confidence (≥0.90)
- **Categories**: High (≥0.90), Moderate (0.70-0.89), Low (<0.70)

---

## Test Scenarios

| Scenario | Samples | Challenge | Metric Focus |
|----------|---------|-----------|--------------|
| **Soft-Spoken** | 3 | Low volume depressed speech | WER tolerance |
| **Emotional** | 3 | Hesitation, crying, agitation | Pause handling |
| **Code-Switching** | 5 | Persian + English medical terms | Bilingual recognition |
| **Medical Terms** | 3 | DSM-5 disorder names | Terminology accuracy |
| **Background Noise** | 3 | Clinic environment noise | Noise robustness |
| **TOTAL** | **17** | Comprehensive psychiatric interview scenarios | All metrics |

---

## Improvement Targets

### Primary Targets (Must Achieve)

| Metric | Baseline | Target | Rationale |
|--------|----------|--------|-----------|
| **WER** | TBD | < 0.15 | Overall transcription quality |
| **Medical Accuracy** | TBD | > 0.90 | DSM-5 terminology critical |
| **Code-Switch Accuracy** | TBD | > 0.85 | Iranian medical context |
| **Avg Confidence** | TBD | > 0.85 | API prediction quality |

### Scenario-Specific Targets

| Scenario | Metric | Target | Notes |
|----------|--------|--------|-------|
| Soft-Spoken | WER | < 0.20 | Most challenging |
| Emotional | WER | < 0.18 | Emotional markers |
| Code-Switching | WER | < 0.15 | Core optimization |
| Medical Terms | WER | < 0.12 | Clean formal speech |
| Background Noise | WER | < 0.18 | Realistic clinic |

---

## How to Use

### Step 1: Setup (One-time)
```bash
python test_runner_transcription.py --mode setup

# Creates test_data/ directory structure and ground truth files
# Output: test_data/{scenario}/ground_truth.json for each scenario
```

### Step 2: Transcribe Audio
```bash
# Using SokhanNegar.py GUI:
# 1. Start the application
# 2. Load audio from test_data/{scenario}/*.wav
# 3. Transcribe each audio file
# 4. Copy transcription results

# OR programmatic:
from speech_recognition import Recognizer, AudioFile
from SokhanNegar import SokhanNegarLive

recognizer = Recognizer()

for audio_file in test_files:
    with AudioFile(audio_file) as source:
        audio = recognizer.record(source)
        # Get transcription with confidence
        result = recognizer.recognize_google(audio, language='fa-IR', show_all=True)
        print(result)  # [(transcript, confidence), ...]
```

### Step 3: Update Ground Truth
```python
import json

# Load ground truth
with open('test_data/code_switching/ground_truth.json') as f:
    data = json.load(f)

# Update with transcriptions
for i, sample in enumerate(data['samples']):
    sample['recognized_text'] = 'transcription from step 2'
    sample['confidence_responses'] = [{'transcript': 'text', 'confidence': 0.95}]

# Save
with open('test_data/code_switching/ground_truth.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

### Step 4: Generate Baseline
```bash
python test_runner_transcription.py --mode baseline

# Output: test_results/baseline_metrics.json
# Shows:
# - WER for each scenario
# - Medical term accuracy
# - Code-switch accuracy
# - Confidence distribution
# - Overall metrics
```

### Step 5: Optimize & Re-test
After applying optimizations (audio tuning, bilingual mode, DSM-5 hints):

```bash
# 1. Re-run SokhanNegar on test audio
# 2. Update ground_truth.json with new recognized_text
# 3. Measure improvements

python test_runner_transcription.py --mode compare \
  --baseline test_results/baseline_metrics.json

# Output: test_results/improvement_report.json
# Shows percentage improvements for each metric
```

### Step 6: Test Specific Scenario
```bash
# Deep dive on one scenario
python test_runner_transcription.py --scenario code-switching

# Tests only code-switching samples, provides detailed analysis
```

---

## Ground Truth File Format

Each scenario has a `ground_truth.json`:

```json
{
  "scenario": "code_switching",
  "description": "Persian-English code-switching with medical terminology",
  "samples": [
    {
      "id": "CS_001",
      "filename": "code_switch_001.wav",
      "ground_truth": "بیمار depression داره و anxiety هم",
      "recognized_text": null,  # ← POPULATE THIS
      "expected_medical_terms": ["depression", "anxiety"],
      "expected_english_terms": ["depression", "anxiety"],
      "duration_seconds": 5,
      "confidence_responses": []  # ← POPULATE THIS (OPTIONAL)
    }
  ]
}
```

### After Transcription:
```json
{
  "recognized_text": "بیمار depression داره anxiety هم",
  "confidence_responses": [
    {
      "transcript": "بیمار depression داره anxiety هم",
      "confidence": 0.92
    }
  ]
}
```

---

## Expected Output

### Baseline Report (test_results/baseline_metrics.json)

```json
{
  "improvement_targets": {
    "wer": {
      "current_baseline": 0.21,
      "target": 0.15,
      "description": "Word Error Rate should be < 15%"
    },
    "medical_term_accuracy": {
      "current_baseline": 0.85,
      "target": 0.90,
      "description": "DSM-5 medical terms should be recognized with >90% accuracy"
    },
    "code_switch_accuracy": {
      "current_baseline": 0.77,
      "target": 0.85,
      "description": "Persian-English code-switched phrases..."
    },
    "average_confidence": {
      "current_baseline": 0.78,
      "target": 0.85,
      "description": "Average confidence score should be > 85%"
    }
  },
  "scenarios": {
    "code_switching": {
      "sample_count": 5,
      "avg_wer": 0.18,
      "avg_medical_accuracy": 0.88,
      "avg_code_switch_accuracy": 0.82,
      "avg_confidence": 0.81,
      "samples": [...]
    }
    // ... other scenarios
  }
}
```

### Improvement Report (test_results/improvement_report.json)

```json
{
  "improvements": {
    "code_switching": {
      "wer_improvement": {
        "baseline": 0.18,
        "current": 0.095,
        "improvement_percent": 47.2  // ✓ IMPROVED
      },
      "medical_accuracy_improvement": {
        "baseline": 0.88,
        "current": 0.95,
        "improvement_percent": 7.95  // ✓ IMPROVED
      },
      "code_switch_improvement": {
        "baseline": 0.82,
        "current": 0.94,
        "improvement_percent": 14.63  // ✓ IMPROVED
      }
    }
    // ... other scenarios
  }
}
```

---

## Console Output Example

```
================================================================================
TRANSCRIPTION ACCURACY TEST RUNNER
================================================================================

Loading ground truth samples...
✓ Loaded 3 samples for soft_spoken
✓ Loaded 3 samples for emotional
✓ Loaded 5 samples for code_switching
✓ Loaded 3 samples for medical_terms
✓ Loaded 3 samples for background_noise

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

✓ Baseline report saved: test_results/baseline_metrics.json
```

---

## File Overview

### Core Testing Files
| File | Lines | Purpose |
|------|-------|---------|
| `test_transcription_accuracy.py` | 622 | Main testing framework |
| `test_runner_transcription.py` | 387 | Test orchestration & execution |
| `test_data/*/ground_truth.json` | 5 files | Ground truth samples (17 total) |

### Documentation Files
| File | Purpose |
|------|---------|
| `TESTING_FRAMEWORK_GUIDE.md` | Comprehensive guide (400+ lines) |
| `TESTING_QUICK_START.md` | This quick reference |

### Generated During Testing
| File | Purpose |
|------|---------|
| `test_results/baseline_metrics.json` | Baseline performance metrics |
| `test_results/improvement_report.json` | Improvement comparison |
| `transcription_accuracy_test.log` | Detailed test logs |
| `test_runner.log` | Execution logs |

---

## Troubleshooting

### Issue: No data in baseline metrics
```
Status: ⚠ NO DATA (no samples with recognized_text)
```
**Fix**: Populate `recognized_text` field in ground_truth.json files

### Issue: Medical accuracy showing 0.0
**Fix**: 
1. Check DSM-5 terms in `expected_medical_terms` 
2. Verify term format matches DSM5 terminology
3. Ensure terms are lowercase for comparison

### Issue: Can't find test_data directory
**Fix**: Run `python test_runner_transcription.py --mode setup`

---

## Next Steps

1. **Baseline (Task 5 - Now)**: Establish current performance metrics
2. **Optimization (Tasks 6)**: Apply audio/API tuning, measure improvements
3. **Validation (Tasks 7)**: Verify all targets met, test in production

---

## Command Reference

```bash
# Initialize test structure
python test_runner_transcription.py --mode setup

# Generate baseline metrics
python test_runner_transcription.py --mode baseline

# Compare against baseline
python test_runner_transcription.py --mode compare \
  --baseline test_results/baseline_metrics.json

# Test specific scenario
python test_runner_transcription.py --scenario code-switching
python test_runner_transcription.py --scenario medical_terms
python test_runner_transcription.py --scenario soft_spoken
python test_runner_transcription.py --scenario emotional
python test_runner_transcription.py --scenario background_noise

# Interactive mode
python test_runner_transcription.py --interactive
```

---

## Summary

✅ Framework established with:
- 5 test scenarios
- 17 ground truth samples
- 4 comprehensive metrics
- Baseline & improvement tracking
- Ready for optimization testing

📊 Metrics defined with clear targets for each scenario

🎯 Ready to measure improvements from Tasks 6+ optimizations
