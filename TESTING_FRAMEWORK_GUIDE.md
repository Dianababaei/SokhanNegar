# Comprehensive Transcription Accuracy Testing Framework

**Status**: ✅ Complete (Task 5/6)
**Purpose**: Measure and validate transcription accuracy improvements across all psychiatric interview scenarios

## Overview

This testing framework measures transcription accuracy using multiple metrics designed to track improvement throughout the project:

1. **Word Error Rate (WER)** - Overall transcription accuracy
2. **Medical Term Accuracy** - DSM-5 terminology recognition
3. **Code-Switch Accuracy** - Persian-English phrase recognition
4. **Confidence Score Distribution** - API confidence in predictions

---

## Test Scenarios

The framework tests **5 distinct psychiatric interview scenarios**:

### 1. Soft-Spoken Speech (SS)
**Challenge**: Low-energy depressed or quiet patients speaking at reduced volume

**Audio Characteristics**:
- Volume: 50-70% of normal speech
- Emotional state: Depressed, withdrawn, hesitant
- Speaking rate: Slower than normal
- Number of samples: 3 test samples

**Expected Metrics**:
- WER: < 20% (more difficult due to low volume)
- Medical term accuracy: > 85%
- Code-switch accuracy: > 75%
- Min confidence: 0.65

**Relevance**: Depression, low mood, suicidal ideation patients

---

### 2. Emotional Variations (EM)
**Challenge**: Speech with emotional variations - hesitation, agitation, crying

**Audio Characteristics**:
- Pause patterns: Longer hesitant pauses (1-2 seconds)
- Volume variations: Fluctuating between quiet and normal
- Speech rate: Inconsistent (starts slow, becomes faster)
- Emotional markers: Sighs, breathing changes, voice cracks
- Number of samples: 3 test samples

**Expected Metrics**:
- WER: < 18% (emotional markers filtered but pauses managed)
- Medical term accuracy: > 85%
- Code-switch accuracy: > 80%
- Min confidence: 0.70

**Relevance**: Anxiety disorders, panic attacks, PTSD

---

### 3. Code-Switching (CS)
**Challenge**: Persian-English medical terminology mixing (primary test scenario)

**Audio Characteristics**:
- Pattern: Persian sentence with embedded English medical terms
- Examples:
  - "بیمار depression داره" (Patient has depression)
  - "cognitive behavioral therapy شروع کنیم" (Let's start cognitive behavioral therapy)
  - "medication adherence مشکل است" (Medication adherence is difficult)
- Number of samples: 5 test samples

**Expected Metrics**:
- WER: < 15%
- Medical term accuracy: > 90% ✓ (Primary focus with DSM-5 hints)
- Code-switch accuracy: > 85% ✓ (Primary focus with bilingual mode)
- Min confidence: 0.80

**Relevance**: Iranian psychiatric interviews where English terminology is standard

---

### 4. Medical Terminology (MT)
**Challenge**: DSM-5 psychiatric disorder recognition (Persian and English)

**Audio Characteristics**:
- Content: Disorder names and psychiatric terminology
- Languages: Both Persian translations and English terms
- Examples:
  - "اختلال افسردگی اساسی" (Major Depressive Disorder)
  - "اختلال اضطراب فراگیر" (Generalized Anxiety Disorder)
  - "PTSD" (Post-Traumatic Stress Disorder)
- Number of samples: 3 test samples

**Expected Metrics**:
- WER: < 12% (clean, formal medical terminology)
- Medical term accuracy: > 92% ✓ (Primary focus with speech hints)
- Code-switch accuracy: 100% (no code-switching in this scenario)
- Min confidence: 0.85

**Relevance**: Direct testing of DSM-5 terminology integration

---

### 5. Background Noise (BN)
**Challenge**: Speech with clinical environment background noise

**Audio Characteristics**:
- Noise types:
  - Medical equipment sounds (beeps, monitors)
  - Office conversation/chatter
  - Traffic noise
- SNR (Signal-to-Noise Ratio): 10-15 dB
- Number of samples: 3 test samples

**Expected Metrics**:
- WER: < 18% (noise degrades accuracy)
- Medical term accuracy: > 85% (medical terms help with noise robustness)
- Code-switch accuracy: > 80%
- Min confidence: 0.70 (noise reduces confidence)

**Relevance**: Realistic Iranian psychiatric clinic environment

---

## Improvement Targets

### Primary Targets (Must Achieve)

| Metric | Target | Baseline | Rationale |
|--------|--------|----------|-----------|
| **WER (Overall)** | < 15% | TBD | Standard speech recognition benchmark; <10% excellent, <15% acceptable |
| **Medical Term Accuracy** | > 90% | TBD | Critical for psychiatric diagnosis; 186 DSM-5 terms must be recognized |
| **Code-Switch Accuracy** | > 85% | TBD | Essential for Iranian medical context; 8 test code-switching patterns |
| **Avg Confidence Score** | > 0.85 | TBD | API confidence above 85% indicates high-quality predictions |

### Secondary Targets (Should Achieve)

| Metric | Target | Category | Notes |
|--------|--------|----------|-------|
| **Soft-Spoken WER** | < 20% | Scenario-specific | Depressed patients are lowest fidelity |
| **Emotional Variations WER** | < 18% | Scenario-specific | Emotional speech is challenging |
| **Code-Switching WER** | < 15% | Scenario-specific | Code-switching is core optimization |
| **Medical Terms WER** | < 12% | Scenario-specific | Clean medical terminology should be highest accuracy |
| **Background Noise WER** | < 18% | Scenario-specific | Realistic clinic noise |
| **High Confidence Distribution** | > 60% | Distribution | At least 60% of predictions should have >90% confidence |

---

## Metrics Explanation

### 1. Word Error Rate (WER)

**Formula**: 
```
WER = (Substitutions + Deletions + Insertions) / Total_Reference_Words
```

**Interpretation**:
- 0.0 = Perfect transcription (0% error)
- 0.10 = 10% error (1 error per 10 words) - Excellent
- 0.15 = 15% error (1-2 errors per 10 words) - Acceptable
- 0.30 = 30% error - Poor
- 1.0+ = More errors than words - Unusable

**Example**:
- Reference: "بیمار depression داره و anxiety هم" (5 words)
- Hypothesis: "بیمار depressed داره anxiety" (4 words)
- Errors: 1 substitution (depression→depressed), 1 deletion (و هم)
- WER = 2 / 5 = 0.40 (40% error)

### 2. Character Error Rate (CER)

**Formula**: Similar to WER but at character level instead of word level

**Interpretation**: More sensitive to minor typos; used alongside WER

---

### 3. Medical Term Accuracy

**Definition**: Percentage of DSM-5 psychiatric terms correctly recognized

**Calculation**:
```
Medical_Accuracy = (Correctly_Recognized_Terms) / (Total_Expected_Terms)
```

**Example**:
- Ground truth: "بیمار depression داره و bipolar disorder"
- Expected terms: ["depression", "bipolar disorder"]
- Recognized: "بیمار depression داره و bipolar disorder"
- Terms found: 2/2 = 100% accuracy

**Importance**: 
- Directly impacts clinical accuracy
- Tests DSM-5 hints integration
- Tracks speech_contexts effectiveness

---

### 4. Code-Switch Accuracy

**Definition**: Percentage of Persian-English code-switched phrases correctly transcribed

**Calculation**:
```
CodeSwitch_Accuracy = (Correctly_Recognized_English_Terms) / (Total_English_Terms)
```

**Example**:
- Ground truth: "cognitive behavioral therapy شروع کنیم"
- English terms expected: ["cognitive", "behavioral", "therapy"]
- Recognized: "cognitive behavioral therapy شروع کنیم"
- English terms found: 3/3 = 100% accuracy

**Importance**:
- Tests bilingual recognition (fa-IR + en-US)
- Validates code-switching configuration
- Tracks English-Persian language model performance

---

### 5. Confidence Score Distribution

**Definition**: How Google API confidence scores are distributed across predictions

**Thresholds**:
- **High Confidence**: score ≥ 0.90 (green - trust completely)
- **Moderate Confidence**: 0.70 ≤ score < 0.90 (yellow - review recommended)
- **Low Confidence**: score < 0.70 (red - doctor review required)

**Interpretation**:
- High % of high-confidence scores → Good recognition
- High % of low-confidence scores → Poor recognition or difficult audio
- Distribution shift over optimization rounds → Improvement tracking

---

## Testing Workflow

### Phase 1: Setup (One-time)
```bash
# Initialize test data structure
python test_runner_transcription.py --mode setup

# Creates:
# - test_data/soft_spoken/ground_truth.json
# - test_data/emotional/ground_truth.json
# - test_data/code_switching/ground_truth.json
# - test_data/medical_terms/ground_truth.json
# - test_data/background_noise/ground_truth.json
# - test_results/ (for reports)
```

### Phase 2: Baseline Establishment (Task 5)
```bash
# 1. Run SokhanNegar.py to transcribe all test audio files
# 2. Add recognized_text to each sample in ground_truth.json files
# 3. Establish baseline metrics

python test_runner_transcription.py --mode baseline

# Creates: test_results/baseline_metrics.json
# Example output:
# - WER (baseline): 0.25 (25% error)
# - Medical Accuracy (baseline): 0.75 (75%)
# - Code-Switch Accuracy (baseline): 0.70 (70%)
# - Avg Confidence: 0.78
```

### Phase 3: Optimization (Tasks 6 onwards)
```bash
# After applying optimizations (audio tuning, bilingual mode, DSM-5 hints):
# 1. Re-transcribe test audio with SokhanNegar.py
# 2. Update recognized_text in ground_truth.json files
# 3. Measure improvements

python test_runner_transcription.py --mode compare \
  --baseline test_results/baseline_metrics.json

# Creates: test_results/improvement_report.json
# Example output:
# WER improvement: 0.25 → 0.12 (52% improvement)
# Medical Accuracy improvement: 0.75 → 0.92 (22.7% improvement)
# Code-Switch Accuracy improvement: 0.70 → 0.88 (25.7% improvement)
```

### Phase 4: Scenario-Specific Testing
```bash
# Test individual scenarios for deep analysis
python test_runner_transcription.py --scenario code-switching

# Tests only:
# - 5 code-switching samples
# - Code-switch accuracy metric
# - English term recognition
```

---

## Framework Files

### Main Testing Module
- **`test_transcription_accuracy.py`** (Main implementation)
  - `WordErrorRateCalculator`: WER/CER calculation
  - `MedicalTermAccuracyChecker`: DSM-5 term validation
  - `CodeSwitchAccuracyChecker`: Persian-English phrase validation
  - `ConfidenceScoreAnalyzer`: Confidence distribution analysis
  - `TranscriptionAccuracyFramework`: Main framework orchestrator
  - Test data setup functions

- **`test_runner_transcription.py`** (Test execution)
  - `TestRunnerManager`: Test orchestration
  - Baseline generation
  - Improvement comparison
  - Interactive testing mode

### Test Data
- **`test_data/`** (Directory structure)
  - `soft_spoken/ground_truth.json` - 3 samples
  - `emotional/ground_truth.json` - 3 samples
  - `code_switching/ground_truth.json` - 5 samples
  - `medical_terms/ground_truth.json` - 3 samples
  - `background_noise/ground_truth.json` - 3 samples
  - Total: **17 ground truth samples**

### Output Reports
- **`test_results/`** (Generated during testing)
  - `baseline_metrics.json` - Initial baseline metrics
  - `improvement_report.json` - Comparison after optimizations
  - `transcription_accuracy_test.log` - Detailed test logs
  - `test_runner.log` - Execution logs

---

## Ground Truth Sample Structure

Each ground truth JSON file contains samples in this format:

```json
{
  "scenario": "code_switching",
  "description": "Persian-English code-switching with medical terminology",
  "samples": [
    {
      "id": "CS_001",
      "filename": "code_switch_001.wav",
      "ground_truth": "بیمار depression داره و anxiety هم توضیح داده",
      "recognized_text": "[EMPTY or NULL initially, populated after transcription]",
      "expected_medical_terms": ["depression", "anxiety"],
      "expected_english_terms": ["depression", "anxiety"],
      "duration_seconds": 5,
      "confidence_responses": "[Optional: API response with confidence scores]"
    }
  ]
}
```

### Populating recognized_text

After running SokhanNegar.py on test audio:

```bash
# 1. For each audio file: code_switch_001.wav
# 2. Run through SokhanNegar.py to get transcription
# 3. Update ground_truth.json:

{
  "id": "CS_001",
  "ground_truth": "بیمار depression داره و anxiety هم توضیح داده",
  "recognized_text": "بیمار depression داره anxiety توضیح داده",  # ← ADD THIS
  "expected_medical_terms": ["depression", "anxiety"],
  "expected_english_terms": ["depression", "anxiety"]
}
```

---

## Integration with SokhanNegar.py

### Step 1: Prepare Audio Files
Place test audio files in test_data subdirectories:
```
test_data/
  ├── code_switching/
  │   ├── ground_truth.json
  │   ├── code_switch_001.wav
  │   ├── code_switch_002.wav
  │   └── ...
  ├── soft_spoken/
  │   ├── ground_truth.json
  │   ├── soft_spoken_001.wav
  │   └── ...
```

### Step 2: Transcribe with SokhanNegar.py
```python
# Option A: Use SokhanNegar GUI
# - Start the GUI
# - Load and transcribe each audio file
# - Copy transcription results

# Option B: Programmatic usage
import speech_recognition as sr
from SokhanNegar import SokhanNegarLive

app = SokhanNegarLive()

# For each test audio file:
with sr.AudioFile('test_data/code_switching/code_switch_001.wav') as source:
    audio = recognizer.record(source)
    result = app.parse_google_response(
        recognizer.recognize_google(audio, language='fa-IR', show_all=True)
    )
    print(result)  # Returns (text, confidence)
```

### Step 3: Update Ground Truth Files
```python
import json

# Read ground truth
with open('test_data/code_switching/ground_truth.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Update with transcriptions
for i, sample in enumerate(data['samples']):
    sample['recognized_text'] = '[transcription from SokhanNegar]'
    sample['confidence_responses'] = '[confidence data from API]'

# Save updated
with open('test_data/code_switching/ground_truth.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

### Step 4: Generate Baseline
```bash
python test_runner_transcription.py --mode baseline
```

---

## Running Baseline Test

### Command
```bash
python test_runner_transcription.py --mode baseline
```

### Output Example
```
================================================================================
TRANSCRIPTION ACCURACY TEST RUNNER
================================================================================

Setting up test data structure...
✓ Test data initialization complete

Initializing transcription accuracy framework...

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

## Comparing Improvements

### Command
```bash
python test_runner_transcription.py --mode compare \
  --baseline test_results/baseline_metrics.json
```

### Output Example
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
  Medical Accuracy: 0.810 → 0.920 (↑ Improved: 13.6%)
  Code-Switch Accuracy: 0.720 → 0.810 (↑ Improved: 12.5%)

[Additional scenarios...]

================================================================================
```

---

## Troubleshooting

### Issue: "No samples with recognized_text"
**Cause**: Ground truth files don't have recognized_text populated
**Solution**: 
1. Run SokhanNegar.py on test audio files
2. Update ground_truth.json with recognized_text field
3. Re-run baseline test

### Issue: "Ground truth file not found"
**Cause**: test_data directory not created
**Solution**: 
```bash
python test_runner_transcription.py --mode setup
```

### Issue: Medical term accuracy showing 0.0
**Cause**: DSM-5 terms not in expected_medical_terms field
**Solution**: 
1. Verify DSM-5 terms match terminology in dsm5_terminology.json
2. Ensure terms are lowercased for comparison
3. Check that expected_medical_terms is populated in ground truth

### Issue: Code-switch accuracy showing 0.0
**Cause**: English terms not in expected_english_terms field
**Solution**: 
1. Verify English terms in ground truth matches what's in recognized_text
2. Ensure expected_english_terms is populated
3. Check for case sensitivity issues

---

## Next Steps (Tasks 6+)

### Task 6: Performance Optimization Testing
- Use framework to measure impact of each optimization
- Track WER, medical accuracy, confidence improvements
- Document regressions and trade-offs

### Task 7: Validation & Production Readiness
- Achieve all primary targets (WER <15%, Medical >90%, Code-Switch >85%)
- Verify no regressions in any scenario
- Establish monitoring metrics for production

---

## Summary

✅ **Framework Complete**
- 5 test scenarios with 17 total ground truth samples
- 4 core metrics (WER, Medical, Code-Switch, Confidence)
- Baseline establishment and improvement tracking
- Integration with SokhanNegar.py

🎯 **Improvement Targets Defined**
- Primary: WER <15%, Medical >90%, Code-Switch >85%, Confidence >0.85
- Secondary: Scenario-specific targets for edge cases

📊 **Ready for Testing**
- Run baseline: `python test_runner_transcription.py --mode baseline`
- Track improvements: `python test_runner_transcription.py --mode compare`
- Detailed testing: `python test_runner_transcription.py --scenario code-switching`
