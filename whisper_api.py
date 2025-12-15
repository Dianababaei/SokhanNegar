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
    
    try:
        # Convert audio_data to WAV format
        wav_buffer = _audio_data_to_wav(audio_data)
        
        # Call Whisper API with timeout
        # Set timeout via openai client configuration
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buffer,
            language="fa",
            timeout=timeout
        )
        
        # Extract and return transcribed text
        transcribed_text = response.text if hasattr(response, 'text') else str(response)
        
        # Track successful transcription
        stats = tracker.track_audio_duration(audio_duration_seconds, success=True)
        logger.info(
            f"Usage tracked - Total: {stats['total_minutes']:.2f} min, "
            f"Cost: {stats['estimated_cost']}, "
            f"Daily: {stats['daily_minutes']:.2f} min"
        )
        
        return transcribed_text.strip()
    
    except openai.AuthenticationError as e:
        # Track failed attempt
        tracker.track_audio_duration(audio_duration_seconds, success=False)
        raise openai.AuthenticationError(
            f"OpenAI authentication failed. Check your API key in .env file. "
            f"Details: {str(e)}"
        )
    
    except openai.RateLimitError as e:
        # Track failed attempt
        tracker.track_audio_duration(audio_duration_seconds, success=False)
        raise openai.RateLimitError(
            f"OpenAI API quota exceeded. Please try again later. "
            f"Details: {str(e)}"
        )
    
    except openai.APIError as e:
        # Track failed attempt
        tracker.track_audio_duration(audio_duration_seconds, success=False)
        raise openai.APIError(
            f"OpenAI API error occurred. Details: {str(e)}"
        )
    
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
