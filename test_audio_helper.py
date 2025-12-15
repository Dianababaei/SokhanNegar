"""
Test audio sample generation helper for integration testing.

This module provides utilities to generate test audio samples and
documentation for quality comparison testing of Whisper vs Google API.
"""

import os
import wave
import struct
import logging
from pathlib import Path
import math

logger = logging.getLogger(__name__)


def create_test_samples_directory():
    """Create test_samples directory if it doesn't exist."""
    samples_dir = Path("test_samples")
    samples_dir.mkdir(exist_ok=True)
    logger.info(f"Test samples directory ready: {samples_dir.absolute()}")
    return samples_dir


def generate_sine_wave(frequency, duration, sample_rate=16000):
    """
    Generate a sine wave for testing.
    
    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate in Hz (default: 16000)
    
    Returns:
        bytes: Audio data as PCM 16-bit samples
    """
    num_samples = int(duration * sample_rate)
    amplitude = 32767  # Max amplitude for 16-bit signed
    
    audio_data = []
    for i in range(num_samples):
        # Generate sine wave
        sample = amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
        # Convert to 16-bit signed integer
        sample_int = int(sample)
        audio_data.append(struct.pack('<h', sample_int))
    
    return b''.join(audio_data)


def generate_silence(duration, sample_rate=16000):
    """
    Generate silent audio (zero samples).
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
    
    Returns:
        bytes: Silent audio data
    """
    num_samples = int(duration * sample_rate)
    return b'\x00\x00' * num_samples


def generate_noise(duration, sample_rate=16000):
    """
    Generate white noise for testing.
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
    
    Returns:
        bytes: Noise audio data
    """
    import random
    num_samples = int(duration * sample_rate)
    amplitude = 32767
    
    audio_data = []
    for _ in range(num_samples):
        # Generate random noise
        sample = random.randint(-amplitude, amplitude)
        audio_data.append(struct.pack('<h', sample))
    
    return b''.join(audio_data)


def create_wav_file(filename, audio_data, sample_rate=16000, channels=1):
    """
    Create a WAV file from audio data.
    
    Args:
        filename: Output filename
        audio_data: Audio data in bytes
        sample_rate: Sample rate in Hz
        channels: Number of channels (1=mono, 2=stereo)
    """
    sample_width = 2  # 16-bit samples
    
    with wave.open(str(filename), 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)
    
    logger.info(f"Created WAV file: {filename} ({len(audio_data)} bytes)")


def create_test_audio_samples():
    """
    Create all test audio samples needed for testing.
    
    This creates dummy/synthetic samples. For actual testing,
    replace with real Persian speech samples.
    """
    samples_dir = create_test_samples_directory()
    
    logger.info("Generating test audio samples...")
    logger.info("NOTE: These are synthetic samples for structure validation.")
    logger.info("For quality comparison tests, use actual Persian speech samples.")
    
    # Create directory structure documentation
    create_samples_readme(samples_dir)
    
    # 1. Short duration sample (5 seconds)
    logger.info("Generating short_clear.wav (5s)...")
    short_audio = generate_sine_wave(440, 5)  # 440 Hz tone
    create_wav_file(samples_dir / "short_clear.wav", short_audio)
    
    # 2. Medium duration sample (30 seconds)
    logger.info("Generating medium_dialogue.wav (30s)...")
    # Mix of tones to simulate dialogue
    medium_audio = (
        generate_sine_wave(440, 15) +  # First speaker
        generate_sine_wave(880, 15)    # Second speaker
    )
    create_wav_file(samples_dir / "medium_dialogue.wav", medium_audio)
    
    # 3. Long duration sample (5 minutes)
    logger.info("Generating long_narration.wav (5 min)...")
    # Extended tone for long duration
    long_audio = generate_sine_wave(440, 300)  # 5 minutes = 300 seconds
    create_wav_file(samples_dir / "long_narration.wav", long_audio)
    
    # 4. Noise sample (5 seconds)
    logger.info("Generating noisy_speech.wav (5s with noise)...")
    noisy = generate_noise(5)
    create_wav_file(samples_dir / "noisy_speech.wav", noisy)
    
    # 5. Multiple speakers (simulated)
    logger.info("Generating multiple_speakers.wav (30s)...")
    multi_speaker = (
        generate_sine_wave(300, 10) +  # Speaker 1 (lower pitch)
        generate_sine_wave(600, 10) +  # Speaker 2 (higher pitch)
        generate_sine_wave(450, 10)    # Speaker 3 (medium pitch)
    )
    create_wav_file(samples_dir / "multiple_speakers.wav", multi_speaker)
    
    # 6. Fast speech (simulated with higher frequency)
    logger.info("Generating fast_speech.wav (5s)...")
    fast_audio = generate_sine_wave(880, 5)  # Higher frequency = faster perception
    create_wav_file(samples_dir / "fast_speech.wav", fast_audio)
    
    logger.info("✓ Test audio samples created successfully")
    logger.info(f"Location: {samples_dir.absolute()}")


def create_samples_readme(samples_dir):
    """Create README documentation for test samples."""
    readme_path = samples_dir / "README.md"
    
    readme_content = """# Test Audio Samples

This directory contains test audio samples for Whisper API integration testing.

## Samples Overview

### 1. short_clear.wav (5 seconds)
- **Purpose**: Quick API tests, valid audio format validation
- **Content**: 440 Hz sine wave (synthetic)
- **For Real Testing**: Replace with clear Persian speech sample
- **Example Text**: "سلام، چطور می‌تونم کمکتون کنم؟"

### 2. medium_dialogue.wav (30 seconds)
- **Purpose**: Conversational quality testing
- **Content**: Multi-speaker simulation (synthetic)
- **For Real Testing**: Replace with natural Persian dialogue
- **Test Metrics**: Word accuracy, punctuation, dialogue continuity

### 3. long_narration.wav (5+ minutes)
- **Purpose**: Extended operation testing, memory stability
- **Content**: 5-minute continuous audio (synthetic)
- **For Real Testing**: Replace with long Persian narration
- **Test Metrics**: Memory usage stability, continuous processing

### 4. noisy_speech.wav (5 seconds)
- **Purpose**: Robustness testing with background noise
- **Content**: White noise (synthetic)
- **For Real Testing**: Record Persian speech with background noise
- **Noise Types to Test**:
  - Background conversation
  - Traffic noise
  - Music/TV in background
  - Office environment

### 5. multiple_speakers.wav (30 seconds)
- **Purpose**: Multi-speaker handling and differentiation
- **Content**: Three different frequencies (synthetic)
- **For Real Testing**: Record conversation between 2-3 Persian speakers
- **Test Metrics**: Speaker identification, speech boundaries

### 6. fast_speech.wav (5 seconds)
- **Purpose**: Rapid speech handling
- **Content**: Higher frequency tone (synthetic)
- **For Real Testing**: Record native Persian speaker at normal/fast speech rate
- **Test Metrics**: Speech rate adaptation, word preservation

## Important Notes

### Synthetic vs Real Samples
- **Current samples are synthetic** (sine waves, noise)
- Used for testing **file structure and API integration**
- **Cannot assess transcription quality** without real speech

### For Quality Testing
1. Obtain actual Persian speech samples
2. Record clear Persian speaker (male/female)
3. Collect challenging scenarios:
   - Multiple speakers
   - Background noise
   - Fast/slow speech
   - Different accents/dialects

### Sample Format Requirements
- **Format**: WAV (PCM)
- **Sample Rate**: 16 kHz (16000 Hz)
- **Channels**: Mono (1)
- **Bit Depth**: 16-bit signed PCM
- **File Size**: Varies by duration

## Quality Comparison Test Procedure

1. **Prepare Real Samples**
   ```
   test_samples/
   ├── short_clear.wav      → Real Persian speech (5s)
   ├── medium_dialogue.wav  → Real dialogue (30s)
   ├── noisy_speech.wav     → Real noisy speech (5s)
   └── ... (other samples)
   ```

2. **Test Both APIs**
   - Transcribe each sample with Whisper API
   - Transcribe each sample with Google API
   - Save transcripts in test_samples/results/

3. **Compare Results**
   - Character-level comparison
   - Word accuracy
   - Punctuation handling
   - Semantic accuracy

4. **Document Findings**
   - Update test_report.md with results
   - Record improvement metrics
   - Note API differences

## Creating Test Audio Files

### Option 1: Record Your Own
```bash
# On Linux/macOS with ffmpeg:
ffmpeg -f pulse -i default -t 30 medium_dialogue.wav

# On Windows with audio recording software
# Use Audacity or similar to record and export as WAV
```

### Option 2: Use Existing Samples
- YouTube: Persian speech samples (download using yt-dlp)
- Podcasts: Extract segments from Persian podcasts
- Archives: Persian text-to-speech archives
- Commercial: Licensed Persian speech corpora

### Option 3: Generate with TTS
```bash
# Using espeak or similar for Persian
espeak -v fa "سلام، این یک نمونه آزمایشی است" -w test.wav
```

## Testing Guidelines

1. **Always test with real Persian speech** for quality assessment
2. **Use synthetic samples only** for format/integration validation
3. **Document source of speech samples** for reproducibility
4. **Keep original and transcription pairs** for analysis
5. **Test diverse speakers and conditions** for robustness

---

**Note**: Current synthetic samples are placeholders. Replace with actual Persian 
speech samples before running quality comparison tests in test_report.md.
"""
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    logger.info(f"Created samples documentation: {readme_path}")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Creating test audio samples...")
    create_test_audio_samples()
    logger.info("✓ Test audio setup complete")
