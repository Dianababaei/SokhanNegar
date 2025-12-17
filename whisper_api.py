"""
Whisper API integration for Persian speech-to-text transcription.

This module provides the whisper_recognize() function to transcribe Persian audio
using OpenAI's cloud-based Whisper API with usage tracking.
"""

import io
import wave
import socket
import speech_recognition as sr
import openai
import logging
from config import OPENAI_API_KEY
from usage_tracker import get_tracker

# Configure logging
logger = logging.getLogger(__name__)

# Configure OpenAI API key
openai.api_key = OPENAI_API_KEY


def _audio_data_to_wav(audio_data: sr.AudioData) -> io.BytesIO:
    """
    Convert speech_recognition.AudioData to in-memory WAV file.
    
    Args:
        audio_data: sr.AudioData object with audio frame data
        
    Returns:
        io.BytesIO: WAV file in memory, ready for API consumption
        
    Raises:
        ValueError: If audio_data format is invalid
    """
    if not isinstance(audio_data, sr.AudioData):
        raise ValueError("Input must be a speech_recognition.AudioData object")
    
    # Create in-memory WAV file
    wav_buffer = io.BytesIO()
    
    try:
        with wave.open(wav_buffer, 'wb') as wav_file:
            # Set audio parameters
            # Channels: 1 (mono)
            # Sample width: audio_data.sample_width (typically 2 for int16)
            # Frame rate: audio_data.sample_rate (typically 16000)
            wav_file.setnchannels(1)
            wav_file.setsampwidth(audio_data.sample_width)
            wav_file.setframerate(audio_data.sample_rate)
            
            # Write audio frame data
            wav_file.writeframes(audio_data.frame_data)
    except Exception as e:
        raise ValueError(f"Failed to create WAV from audio data: {str(e)}")
    
    # Reset buffer position to beginning for reading
    wav_buffer.seek(0)
    return wav_buffer


def whisper_recognize(audio_data: sr.AudioData, timeout: int = 30) -> str:
    """
    Transcribe Persian audio using OpenAI's Whisper API with usage tracking.

    Args:
        audio_data: sr.AudioData object containing mono audio at 16kHz, int16
        timeout: API call timeout in seconds (default: 30)

    Returns:
        str: Transcribed Persian text

    Raises:
        openai.AuthenticationError: If API key is invalid
        openai.RateLimitError: If API quota is exceeded
        openai.APIError: For general OpenAI API errors
        socket.timeout: If API call times out
        ConnectionError: For network connectivity issues
        ValueError: If audio format is invalid
    """
    import numpy as np

    tracker = get_tracker()

    # Calculate audio duration before API call (in seconds)
    # AudioData.frame_data is in bytes, sample_rate is in Hz, sample_width is in bytes
    # duration = (num_frames) / sample_rate
    # num_frames = len(frame_data) / sample_width
    try:
        num_frames = len(audio_data.frame_data) / audio_data.sample_width
        audio_duration_seconds = num_frames / audio_data.sample_rate
    except (AttributeError, ZeroDivisionError):
        # Default to 5 seconds (standard chunk size) if calculation fails
        audio_duration_seconds = 5.0
        logger.warning(f"Could not calculate audio duration, using default 5 seconds")

    # Check if audio has sufficient energy (not just silence/noise)
    try:
        # Convert bytes to numpy array for energy calculation
        audio_array = np.frombuffer(audio_data.frame_data, dtype=np.int16)

        # Calculate RMS (root mean square) energy
        rms_energy = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))

        # Calculate zero crossing rate (helps detect noise vs speech)
        zero_crossings = np.sum(np.abs(np.diff(np.sign(audio_array)))) / (2 * len(audio_array))

        # If energy is too low, it's likely silence
        if rms_energy < 300:
            logger.info(f"Audio energy too low ({rms_energy:.0f}), skipping transcription")
            raise ValueError("Audio contains mostly silence")

        # For medical interviews, prioritize accuracy over cost
        # Use Whisper for moderate to high energy audio (better accuracy)
        # Adjusted threshold to match microphone sensitivity
        if rms_energy < 500:
            logger.info(f"Audio energy ({rms_energy:.0f}) - Using Google API (low energy)")
            raise ValueError("Audio quality better suited for Google Speech Recognition")

        # If zero crossing rate is too high, it's likely just noise
        if zero_crossings > 0.3:  # High zero crossing rate indicates noise
            logger.info(f"High zero crossing rate ({zero_crossings:.3f}), likely noise - skipping")
            raise ValueError("Audio contains mostly noise")

        logger.info(f"Audio quality check passed - Energy: {rms_energy:.0f}, ZCR: {zero_crossings:.3f}")

    except Exception as e:
        if "mostly silence" in str(e) or "mostly noise" in str(e) or "better suited for Google" in str(e):
            raise
        logger.warning(f"Could not check audio energy: {e}")
    
    try:
        # Convert audio_data to WAV format
        wav_buffer = _audio_data_to_wav(audio_data)

        # Give the buffer a filename so OpenAI can recognize the format
        wav_buffer.name = "audio.wav"

        # Call Whisper API with timeout
        # Set timeout via openai client configuration
        # Note: Whisper automatically handles mixed languages when language is not specified
        # But we specify "fa" to prioritize Persian while still detecting English words
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buffer,
            language="fa",  # Primary language, but Whisper still detects English
            temperature=0.0,  # Use deterministic output for consistency
            timeout=timeout
        )
        
        # Extract and return transcribed text
        transcribed_text = response.text if hasattr(response, 'text') else str(response)
        transcribed_text = transcribed_text.strip()

        # Validate transcription quality - filter out gibberish
        if transcribed_text:
            # Check if text is too short (likely noise)
            if len(transcribed_text) < 2:
                logger.info(f"Transcription too short ('{transcribed_text}'), likely noise")
                raise ValueError("Transcription result too short")

            # Check for gibberish patterns (random letters/characters)
            # Persian text should have mostly Persian characters
            persian_chars = sum(1 for c in transcribed_text if '\u0600' <= c <= '\u06FF')
            total_alpha = sum(1 for c in transcribed_text if c.isalpha())

            if total_alpha > 0:
                persian_ratio = persian_chars / total_alpha

                # If less than 50% Persian characters in alphabetic text, it's likely gibberish
                if persian_ratio < 0.5:
                    logger.info(f"Low Persian ratio ({persian_ratio:.2f}), text: '{transcribed_text}'")
                    raise ValueError("Transcription appears to be gibberish")

            # Check for repeated single characters (common in noise transcription)
            if len(transcribed_text) <= 10:
                unique_chars = len(set(transcribed_text.replace(' ', '')))
                if unique_chars <= 3:  # Too few unique characters
                    logger.info(f"Too few unique characters in '{transcribed_text}'")
                    raise ValueError("Transcription appears to be noise")

        # Track successful transcription
        stats = tracker.track_audio_duration(audio_duration_seconds, success=True)
        logger.info(
            f"✓ Valid transcription: '{transcribed_text[:50]}...' | "
            f"Total: {stats['total_minutes']:.2f} min, "
            f"Cost: {stats['estimated_cost']}"
        )

        return transcribed_text
    
    except openai.AuthenticationError as e:
        # Track failed attempt
        tracker.track_audio_duration(audio_duration_seconds, success=False)
        logger.error(f"OpenAI authentication failed. Check your API key in .env file. Details: {str(e)}")
        raise

    except openai.RateLimitError as e:
        # Track failed attempt
        tracker.track_audio_duration(audio_duration_seconds, success=False)
        logger.error(f"OpenAI API quota exceeded. Please try again later. Details: {str(e)}")
        raise

    except openai.APIError as e:
        # Track failed attempt
        tracker.track_audio_duration(audio_duration_seconds, success=False)
        logger.error(f"OpenAI API error occurred. Details: {str(e)}")
        raise
    
    except socket.timeout as e:
        # Track failed attempt
        tracker.track_audio_duration(audio_duration_seconds, success=False)
        raise socket.timeout(
            f"API call timed out after {timeout} seconds. Details: {str(e)}"
        )
    
    except (ConnectionError, socket.gaierror, socket.error) as e:
        # Track failed attempt
        tracker.track_audio_duration(audio_duration_seconds, success=False)
        raise ConnectionError(
            f"Network error during API call. Details: {str(e)}"
        )
    
    except ValueError as e:
        # Track failed attempt
        tracker.track_audio_duration(audio_duration_seconds, success=False)
        # Re-raise ValueError from audio format conversion
        raise ValueError(f"Audio format error: {str(e)}")
    
    except Exception as e:
        # Track failed attempt
        tracker.track_audio_duration(audio_duration_seconds, success=False)
        # Catch any unexpected errors and provide context
        raise Exception(
            f"Unexpected error during Whisper transcription: {str(e)}"
        )
