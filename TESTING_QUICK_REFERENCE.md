# Whisper API Integration Testing - Quick Reference

## Test Files Summary

| File | Purpose | Tests | Duration |
|------|---------|-------|----------|
| `test_whisper_integration.py` | Core integration tests | 33 | 2-3 min |
| `test_network_simulation.py` | Network/fallback tests | 6 | 1-2 min |
| `test_quality_comparison.py` | Quality framework | 3 | 5-10 min |
| `test_performance_monitor.py` | Stability tests | 1 | 10-15 min |
| `test_audio_helper.py` | Sample generation | 6 | <1 min |

**Total**: 49+ tests, ~20-30 minutes

---

## One-Command Test Execution

```bash
# Generate samples first
python test_audio_helper.py

# Run all major test suites
python test_whisper_integration.py && \
python test_network_simulation.py && \
python test_quality_comparison.py && \
python test_performance_monitor.py
```

---

## Individual Test Modules

### 1. Audio Sample Generation
```bash
python test_audio_helper.py
```
**Output**: 6 WAV files in `test_samples/`
**Purpose**: Setup for all other tests

---

### 2. Core Integration Tests (33 tests)
```bash
python test_whisper_integration.py
```

**Test Categories**:
- API Key Validation (4 tests)
  - Valid key, invalid key, missing key, malformed key
- Network Handling (4 tests)
  - Connection errors, timeouts, DNS, socket errors
- Fallback Behavior (4 tests)
  - Auth error fallback, rate limit, API errors
- Usage Tracking (9 tests)
  - Duration accuracy, cost calculation, persistence, recovery
- Audio Format (3 tests)
  - WAV conversion, invalid data, structure validation
- Continuous Operation (3 tests)
  - Multiple chunks, memory stability, thread safety
- Edge Cases (5 tests)
  - Empty audio, short audio, rate limits, invalid durations
- Integration (1 test)
  - Full workflow with tracking

**Expected**: All 33 tests pass ✓

---

### 3. Network & Fallback Tests
```bash
python test_network_simulation.py
```

**Tests**:
1. ✓ AuthenticationError → Fallback
2. ✓ RateLimitError → Fallback
3. ✓ ConnectionError → Fallback
4. ✓ Timeout (30s) → Fallback
5. ✓ DNS Error → Fallback
6. ✓ Service Status Update (🟢 → 🟡)

**Expected**: 6/6 passed

---

### 4. Quality Comparison
```bash
python test_quality_comparison.py
```

**Outputs**:
- `quality_test_template.json` - Manual testing template
- `quality_comparison_report.json` - Comparison results

**For Real Testing**:
1. Record Persian speech samples
2. Transcribe with both Whisper and Google APIs
3. Fill in `quality_test_template.json`
4. Re-run comparison

---

### 5. Performance & Stability
```bash
python test_performance_monitor.py
```

**Metrics Monitored**:
- Memory: Peak, min, average
- CPU: Peak, average
- Processing: Consistency, chunks/second
- Duration: 10 minutes simulated

**Output**: `continuous_operation_results.json`

**Success Criteria**:
- Memory stable (no >10% leak)
- CPU average <50%
- No crashes
- Consistent processing

---

## Key Test Specifications

### API Key Tests
```
✓ Valid key → Whisper succeeds
✓ Invalid key → Google fallback
✓ Missing key → Error + fallback
✓ Malformed key → Caught gracefully
```

### Network Tests
```
✓ Normal operation → Works
✓ Connection error → Fallback triggered
✓ Timeout (30s) → Graceful handling
✓ DNS error → Fallback initiated
```

### Fallback Tests
```
✓ Whisper fails → Google processes request
✓ Smooth transition → No data loss
✓ UI updates → 🟢 → 🟡 indicator
```

### Usage Tracking Tests
```
✓ Duration accuracy: ±5% tolerance
✓ Cost calculation: minutes × $0.006
✓ Persistence: Data survives restarts
✓ Corrupted recovery: Auto-repair
✓ Daily/weekly aggregates: Tracked
```

### Performance Tests
```
✓ Memory: Peak < baseline + 10%
✓ CPU: Average <50%, Peak <80%
✓ Processing: Consistent ±20%
✓ Stability: No crashes/hangs
```

### UI Tests
```
✓ Service indicator updates correctly
✓ Usage stats display accurately
✓ UI stays responsive
✓ Persian text renders correctly
```

---

## Test Results Checklist

After running all tests:

- [ ] `test_whisper_integration.py`: 33 tests passed
- [ ] `test_network_simulation.py`: 6 tests passed
- [ ] `test_quality_comparison.py`: Report generated
- [ ] `test_performance_monitor.py`: Results saved
- [ ] `test_audio_helper.py`: Samples generated
- [ ] No unhandled exceptions
- [ ] All error cases handled gracefully
- [ ] Logs reviewed for issues
- [ ] Metrics within acceptable ranges

---

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| "OPENAI_API_KEY not found" | Set up .env file with your API key |
| "No module named X" | Run `pip install -r requirements.txt` |
| "psutil not available" | Run `pip install psutil` (optional) |
| "Audio file not found" | Run `python test_audio_helper.py` first |
| Tests timeout | Check internet connection and API limits |
| Permission errors | Verify ~/.sokhan_negar directory exists |

---

## Output Files Generated

After running all tests:

```
project_root/
├── transcription.log              (Application logs)
├── test_samples/                  (Generated audio samples)
├── test_results/
│   ├── quality_comparison_report.json
│   └── continuous_operation_results.json
├── quality_test_template.json     (For manual quality testing)
└── .sokhan_negar/
    └── usage_data.json            (Usage tracking data)
```

---

## Success Criteria Summary

| Category | Criterion | Status |
|----------|-----------|--------|
| API Keys | Valid/invalid/missing handling | ✅ Tested |
| Network | Error handling and fallback | ✅ Tested |
| Fallback | Smooth transition, UI updates | ✅ Tested |
| Quality | Comparison framework ready | ✅ Ready |
| Usage | Accuracy ±5%, persistence | ✅ Tested |
| Performance | No leaks, stable CPU | ✅ Tested |
| UI | Responsive, correct display | ✅ Defined |
| Edge Cases | Error handling | ✅ Tested |

---

## Next Steps

1. **Run All Tests** → `python test_audio_helper.py && python test_whisper_integration.py && ...`
2. **Review Results** → Check all output files and logs
3. **Quality Testing** → Use `quality_test_template.json` with real speech samples
4. **Fix Issues** → Address any failures
5. **Document** → Update test_report.md with results
6. **Deploy** → When all tests pass

---

## Documentation Files

- `test_report.md` - Detailed test specifications (33 tests)
- `TEST_EXECUTION_GUIDE.md` - Complete execution instructions
- `TESTING_QUICK_REFERENCE.md` - This file
- `test_samples/README.md` - Audio sample information

---

## Key Files for Reference

**Main Application**:
- `SokhanNegar.py` - Main UI and orchestration
- `whisper_api.py` - Whisper API integration
- `usage_tracker.py` - Usage tracking module
- `config.py` - Configuration management

**Test Files**:
- `test_whisper_integration.py` - 33 core tests
- `test_network_simulation.py` - Network simulation
- `test_quality_comparison.py` - Quality comparison
- `test_performance_monitor.py` - Performance monitoring
- `test_audio_helper.py` - Audio sample generation

---

**Ready to Execute**: All test infrastructure is in place. See TEST_EXECUTION_GUIDE.md for detailed instructions.
