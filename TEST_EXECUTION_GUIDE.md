# Whisper API Integration Testing - Execution Guide

This guide provides step-by-step instructions for executing the comprehensive test suite for the Whisper API integration in SokhanNegar.

## Table of Contents

1. [Environment Setup](#environment-setup)
2. [Test Suite Overview](#test-suite-overview)
3. [Running Individual Tests](#running-individual-tests)
4. [Running Complete Test Suite](#running-complete-test-suite)
5. [Interpreting Results](#interpreting-results)
6. [Troubleshooting](#troubleshooting)

---

## Environment Setup

### Prerequisites

1. **Python 3.7+** installed
2. **All dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional performance monitoring**:
   ```bash
   pip install psutil  # For memory/CPU monitoring
   ```

4. **.env file configured**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

### Verify Setup

```bash
# Test Python environment
python --version

# Test required packages
python -c "import speech_recognition; import openai; print('✓ Core packages OK')"

# Test API key configuration
python -c "from config import OPENAI_API_KEY; print('✓ API key configured')" 2>&1
```

---

## Test Suite Overview

The test suite consists of multiple modules, each focusing on different aspects:

| Module | Purpose | Duration |
|--------|---------|----------|
| `test_whisper_integration.py` | API key validation, network handling, usage tracking | 2-3 min |
| `test_network_simulation.py` | Network failures and fallback behavior | 1-2 min |
| `test_quality_comparison.py` | Quality comparison between APIs | 5-10 min |
| `test_performance_monitor.py` | Continuous operation and stability | 10-15 min |
| `test_audio_helper.py` | Audio sample generation and setup | <1 min |

---

## Running Individual Tests

### 1. Test Audio Sample Setup

**Purpose**: Generate test audio samples and create documentation

```bash
# Generate synthetic test samples
python test_audio_helper.py

# Check generated files
ls -la test_samples/
```

**Expected Output**:
```
✓ Test audio samples created successfully
Location: /path/to/test_samples
```

**Generated Files**:
- `test_samples/short_clear.wav` (5s)
- `test_samples/medium_dialogue.wav` (30s)
- `test_samples/long_narration.wav` (5 min)
- `test_samples/noisy_speech.wav` (5s)
- `test_samples/multiple_speakers.wav` (30s)
- `test_samples/fast_speech.wav` (5s)
- `test_samples/README.md` (documentation)

---

### 2. Core Integration Tests

**Purpose**: Validate API key handling, error catching, usage tracking

```bash
# Run with verbose output
python -m pytest test_whisper_integration.py -v

# Or run directly
python test_whisper_integration.py
```

**Test Classes Executed**:
- `TestAPIKeyValidation` (4 tests)
- `TestNetworkHandling` (4 tests)
- `TestFallbackBehavior` (4 tests)
- `TestUsageTracking` (9 tests)
- `TestAudioFormatConversion` (3 tests)
- `TestContinuousOperation` (3 tests)
- `TestEdgeCases` (5 tests)
- `TestIntegration` (1 test)

**Total**: 33 tests

**Expected Output**:
```
Ran 33 tests in X.XXXs
OK
```

---

### 3. Network and Fallback Tests

**Purpose**: Simulate network errors and verify fallback behavior

```bash
python test_network_simulation.py
```

**Tests Performed**:
1. Whisper AuthenticationError → Google fallback
2. Rate limit error → Google fallback
3. Network error handling
4. API timeout (30s) handling
5. DNS error handling
6. Service status visual updates (🟢 → 🟡)

**Expected Output**:
```
✓ AuthenticationError caught, fallback triggered
✓ RateLimitError caught, fallback triggered
✓ ConnectionError caught, fallback triggered
✓ Timeout caught, fallback triggered
✓ DNS error caught, fallback triggered
✓ Status visual update test passed
```

---

### 4. Quality Comparison Tests

**Purpose**: Compare transcription quality between Whisper and Google APIs

```bash
python test_quality_comparison.py
```

**Test Procedure**:
1. Saves template for manual quality testing
2. Runs example comparison with synthetic data
3. Generates quality report (`quality_comparison_report.json`)

**Expected Output**:
```
Quality test template saved: quality_test_template.json
Running example quality comparison test...

QUALITY COMPARISON SUMMARY
Total comparisons: 3
Overall metrics: {...}
```

**For Real Testing**:
Edit `quality_test_template.json` with actual transcriptions from both APIs and re-run.

---

### 5. Performance and Stability Tests

**Purpose**: Monitor continuous operation for memory leaks and stability

```bash
python test_performance_monitor.py
```

**Test Configuration**:
- 120 chunks × 5 seconds = 600 seconds (10 minutes)
- Memory monitoring enabled (requires psutil)
- CPU usage tracking
- Processing consistency verification

**Expected Output**:
```
CONTINUOUS OPERATION TEST
Duration: 120 chunks × 5 seconds = 600 seconds

Progress: 20/120 chunks
Progress: 40/120 chunks
...
Progress: 120/120 chunks

CONTINUOUS OPERATION TEST RESULTS
Duration: XXX.XX seconds
Chunks processed: 120
Memory Usage: Peak: XXX MB, Stable: True
CPU Usage: Average: XX%
Overall Assessment: STABLE
```

**Results File**: `continuous_operation_results.json`

---

## Running Complete Test Suite

### Option 1: Run All Tests Sequentially

```bash
# Setup
python test_audio_helper.py

# Core integration tests
python test_whisper_integration.py

# Network/fallback tests
python test_network_simulation.py

# Quality comparison (requires manual data)
python test_quality_comparison.py

# Performance tests (10-15 minutes)
python test_performance_monitor.py
```

**Total Duration**: 20-35 minutes

### Option 2: Run with Pytest (If Installed)

```bash
# Install pytest if not already installed
pip install pytest pytest-cov

# Run all tests with coverage report
pytest test_*.py -v --tb=short --cov

# Generate coverage report
pytest test_*.py --cov --cov-report=html
```

### Option 3: Create Automated Test Runner

Create `run_all_tests.py`:

```python
#!/usr/bin/env python3
"""Run complete test suite."""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True)
    elapsed = time.time() - start_time
    
    status = "✓ PASSED" if result.returncode == 0 else "✗ FAILED"
    print(f"{description}: {status} ({elapsed:.1f}s)")
    
    return result.returncode == 0

def main():
    """Run all tests."""
    results = {}
    
    tests = [
        ("python test_audio_helper.py", "Audio Sample Setup"),
        ("python test_whisper_integration.py", "Integration Tests"),
        ("python test_network_simulation.py", "Network & Fallback Tests"),
        ("python test_quality_comparison.py", "Quality Comparison"),
        ("python test_performance_monitor.py", "Performance & Stability"),
    ]
    
    total_start = time.time()
    
    for cmd, description in tests:
        results[description] = run_command(cmd, description)
    
    # Print summary
    total_time = time.time() - total_start
    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed
    
    print(f"\n{'='*70}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*70}")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time/60:.1f} minutes")
    
    for test_name, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"{status} {test_name}")
    
    print(f"{'='*70}")
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
```

Run with:
```bash
python run_all_tests.py
```

---

## Interpreting Results

### Test Status Indicators

- ✓ **PASSED**: Test completed successfully, expectations met
- ✗ **FAILED**: Test failed, requirements not met
- ⚠ **WARNING**: Test passed but with warnings or concerns

### Key Metrics to Monitor

#### 1. API Key Validation
- ✓ Valid key → Whisper succeeds
- ✓ Invalid key → Falls back to Google gracefully
- ✓ Missing key → Clear error message

#### 2. Network Handling
- ✓ Connection error → Fallback triggered
- ✓ Timeout (30s) → Handled gracefully
- ✓ DNS error → Fallback initiated

#### 3. Fallback Behavior
- ✓ Service indicator updates: 🟢 → 🟡
- ✓ All chunks processed without loss
- ✓ Transcription continues seamlessly

#### 4. Usage Tracking Accuracy
- ✓ Duration tracking: ±5% tolerance
- ✓ Cost calculation: minutes × $0.006
- ✓ Persistence across restarts

#### 5. Performance Metrics
- ✓ Memory: Peak < baseline + 10%
- ✓ CPU: Average < 50%, Peak < 80%
- ✓ Processing: Consistent ±20% per chunk

#### 6. Quality Comparison
- ✓ Whisper vs Google: Character similarity
- ✓ Target improvement: 50-80%
- ✓ Persian-specific features: Diacritics, punctuation

---

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"

**Solution**:
```bash
# Verify .env file exists
cat .env

# Ensure format is correct
# OPENAI_API_KEY=sk-...

# Regenerate from example
cp .env.example .env
# Edit .env with your actual key
```

### Issue: "No module named 'speech_recognition'"

**Solution**:
```bash
pip install -r requirements.txt

# Or specifically
pip install speechrecognition pyaudio openai python-dotenv numpy sounddevice
```

### Issue: "psutil not available" (performance monitoring)

**Solution**:
```bash
pip install psutil

# Tests will run without it, but CPU/memory monitoring will be limited
```

### Issue: Tests hang or timeout

**Solution**:
```bash
# Check network connectivity
ping api.openai.com

# Verify API key is valid
python -c "import openai; openai.api_key = 'your_key'; print(openai.api_key)"

# Run single test with timeout
timeout 30 python test_whisper_integration.py
```

### Issue: Audio file not found in quality tests

**Solution**:
```bash
# Generate test audio samples first
python test_audio_helper.py

# Verify files were created
ls -la test_samples/
```

### Issue: "Cannot write usage_data.json" (permission error)

**Solution**:
```bash
# Check permissions on home directory
ls -la ~/.sokhan_negar/

# Fix if needed
mkdir -p ~/.sokhan_negar
chmod 755 ~/.sokhan_negar
```

---

## Continuous Integration Setup

For automated testing in CI/CD pipelines:

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest psutil
    
    - name: Configure API key
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        echo "OPENAI_API_KEY=$OPENAI_API_KEY" > .env
    
    - name: Run tests
      run: |
        python test_audio_helper.py
        pytest test_*.py -v
```

---

## Next Steps

After running tests:

1. **Review Results**: Check all test outputs
2. **Update test_report.md**: Document findings
3. **Fix Issues**: Address any failures
4. **Quality Testing**: Replace synthetic samples with real Persian speech
5. **Production Deployment**: When all tests pass

---

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Speech Recognition Library](https://github.com/Uberi/speech_recognition)
- [Whisper API Guide](https://platform.openai.com/docs/guides/speech-to-text)
- [test_report.md](test_report.md) - Detailed test specifications

---

**Last Updated**: 2024
**Status**: Ready for Execution
