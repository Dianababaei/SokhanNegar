# Persian-English Code-Switching Test Phrases

## Test Suite for Bilingual Recognition (fa-IR + en-US)
Testing Google Speech API recognition accuracy for Persian-English code-switched medical conversations common in Iranian healthcare settings.

---

## Category 1: Common DSM-5 Psychiatric Diagnoses (Code-Switched)

These phrases simulate typical doctor-patient or clinical discussions where English medical terminology is mixed with Persian.

1. **بیمار depression داره** 
   - *Patient has depression*
   - Focus: English noun in Persian sentence structure
   - Expected: "بیمار depression داره" or "بیمار depresion داره"

2. **علائم anxiety disorder رو توضیح بدهید**
   - *Explain the symptoms of anxiety disorder*
   - Focus: English multi-word diagnosis in Persian context
   - Expected: "علائم anxiety disorder رو توضیح بدهید"

3. **این bipolar disorder است**
   - *This is bipolar disorder*
   - Focus: English diagnostic term with Persian article
   - Expected: "این bipolar disorder است"

4. **بیمار PTSD تشخیص داده شده**
   - *Patient diagnosed with PTSD*
   - Focus: English acronym in Persian structure
   - Expected: "بیمار PTSD تشخیص داده شده"

5. **علائم schizophrenia مشهود است**
   - *Symptoms of schizophrenia are apparent*
   - Focus: English term with Persian passive voice
   - Expected: "علائم schizophrenia مشهود است"

---

## Category 2: Psychiatric Symptoms and Clinical Observations (Code-Switched)

These test mixed-language descriptions of emotional and behavioral presentations.

6. **بیمار خیلی depressed به نظر می‌رسد**
   - *Patient seems very depressed*
   - Focus: English adjective modifying Persian descriptor
   - Expected: "بیمار خیلی depressed به نظر می‌رسد"

7. **panic attacks بارها تکرار شده**
   - *Panic attacks have occurred repeatedly*
   - Focus: English term as subject of Persian verb
   - Expected: "panic attacks بارها تکرار شده"

8. **بیمار psychotic episode تجربه می‌کند**
   - *Patient is experiencing a psychotic episode*
   - Focus: English phrase in middle of Persian sentence
   - Expected: "بیمار psychotic episode تجربه می‌کند"

9. **suicidal ideation بسیار جدی است**
   - *Suicidal ideation is very serious*
   - Focus: English technical term as sentence subject
   - Expected: "suicidal ideation بسیار جدی است"

10. **medication adherence مشکل است**
    - *Medication adherence is difficult*
    - Focus: English clinical term describing compliance
    - Expected: "medication adherence مشکل است"

---

## Category 3: Medication and Treatment (Code-Switched)

Testing recognition of medication names and treatment-related code-switching.

11. **sertraline ۵۰ میلی‌گرم روزانه**
    - *Sertraline 50 mg daily*
    - Focus: English medication name with Persian dosage
    - Expected: "sertraline ۵۰ میلی‌گرم روزانه" or "sertraline 50 milligram روزانه"

12. **cognitive behavioral therapy شروع کنیم**
    - *Let's start cognitive behavioral therapy*
    - Focus: English therapeutic approach in Persian request
    - Expected: "cognitive behavioral therapy شروع کنیم"

13. **antidepressants مؤثر نبوده**
    - *Antidepressants have not been effective*
    - Focus: English drug class with Persian verb
    - Expected: "antidepressants مؤثر نبوده"

14. **therapy sessions هفته‌ای یکبار**
    - *Therapy sessions once a week*
    - Focus: English treatment type with Persian frequency
    - Expected: "therapy sessions هفته‌ای یکبار"

15. **hospitalization ضروری است**
    - *Hospitalization is necessary*
    - Focus: English procedure term in Persian statement
    - Expected: "hospitalization ضروری است"

---

## Category 4: Persian-Only Control Phrases (Baseline)

These phrases are entirely in Persian. They serve as a control group to ensure that Persian-only recognition performance is not degraded by bilingual mode.

16. **بیمار خیلی بهتر است**
    - *Patient is much better*
    - Expected accuracy: Should maintain baseline Persian recognition
    - Measurement: Compare with Persian-only mode

17. **علائم کاملاً برطرف شد**
    - *Symptoms have completely resolved*
    - Expected accuracy: Should maintain baseline
    - Measurement: Confidence score comparison

18. **درمان موثر بوده است**
    - *The treatment has been effective*
    - Expected accuracy: Should maintain baseline
    - Measurement: Accuracy vs Persian-only baseline

---

## Test Methodology

### Baseline Measurement (Persian-Only Mode)
1. Test all 18 phrases with `language='fa-IR'` (no alternative languages)
2. Record recognition accuracy percentage
3. Record confidence scores for each phrase
4. Document any misrecognitions

### Bilingual Mode Testing
1. Test all 18 phrases with `language='fa-IR'` and `alternative_language_codes=['en-US']`
2. Record recognition accuracy percentage
3. Record confidence scores for each phrase
4. Document any improvements or regressions

### Performance Metrics

#### For Code-Switched Phrases (1-15):
- **Accuracy Goal**: >90% for English medical terms in Persian sentences
- **Confidence Target**: >0.85 average confidence score
- **Success Criteria**: 
  - English terms recognized correctly
  - Persian context preserved
  - No garbled mixed output

#### For Persian-Only Phrases (16-18):
- **Regression Test**: Accuracy should not drop below baseline
- **Confidence Comparison**: Scores should be similar to Persian-only mode
- **Success Criteria**:
  - No accuracy degradation
  - Confidence scores remain stable

### Expected Results

| Phrase Category | Baseline (fa-IR only) | Bilingual (fa-IR + en-US) | Expected Improvement |
|---|---|---|---|
| Code-Switched (1-15) | 60-80% | 85-95% | +15-25% |
| Persian-Only (16-18) | 95%+ | 93%+ | Maintained |

---

## Actual Test Results

### Baseline (Persian-Only): `language='fa-IR'`
```
[Results to be filled after testing with Persian-only mode]
```

### Bilingual Mode: `language='fa-IR', alternative_language_codes=['en-US']`
```
[Results to be filled after testing with bilingual mode]
```

---

## Notes on Code-Switching in Iranian Medical Contexts

### Why Code-Switching Occurs
1. **Medical Education**: Iranian doctors learn medical terminology in English
2. **International Literature**: Current research published primarily in English
3. **Technical Precision**: English terms often more precise in clinical contexts
4. **Professional Register**: Code-switching signals medical expertise

### Challenges for Speech Recognition
1. **Language Interleaving**: Model must identify language boundaries within sentences
2. **Pronunciation Variations**: English terms pronounced with Persian phonetics
3. **Spelling Variations**: Technical terms may have multiple Persian transliterations
4. **Mixed Morphology**: English stems with Persian grammatical markers

### Bilingual API Advantage
- Recognizes English terms even when embedded in Persian speech
- Improves accuracy for code-switched medical discussions
- Maintains Persian accuracy for non-English segments
- Provides better confidence scores for mixed-language audio

---

## Success Criteria Summary

✓ **Primary Criteria**:
- [ ] English medical terms (depression, anxiety, disorder, PTSD, etc.) recognized correctly in Persian context
- [ ] Persian-only transcription performance matches baseline (no degradation)
- [ ] Code-switched phrases produce coherent, non-garbled transcriptions
- [ ] Average confidence score >0.80 for mixed-language phrases

✓ **Secondary Criteria**:
- [ ] API parameter changes documented with performance metrics
- [ ] Graceful fallback implemented if bilingual mode unavailable
- [ ] Test results compared with baseline measurements
- [ ] Performance data logged for future reference

