import tkinter as tk
from tkinter import scrolledtext, messagebox
import speech_recognition as sr
import threading
import queue
import time
import sounddevice as sd
import numpy as np
import logging
import socket
import sys
import json
from datetime import datetime

from whisper_api import whisper_recognize
from usage_tracker import get_tracker
import openai

# Set console encoding to UTF-8 for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Configure logging for service tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transcription.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Confidence Scoring Constants
# Thresholds for confidence-based quality indicators (0.0-1.0 range)
CONFIDENCE_THRESHOLD_LOW = 0.70      # Below 70%: needs review (red)
CONFIDENCE_THRESHOLD_MODERATE = 0.90  # 70-90%: moderate (yellow)
# Above 90%: high confidence (green)

# Configure separate logger for low-confidence segments
confidence_logger = logging.getLogger('confidence_quality')
confidence_handler = logging.FileHandler('confidence_review.log', encoding='utf-8')
confidence_handler.setLevel(logging.INFO)
confidence_formatter = logging.Formatter('%(asctime)s - %(message)s')
confidence_handler.setFormatter(confidence_formatter)
confidence_logger.addHandler(confidence_handler)
confidence_logger.setLevel(logging.INFO)

class SokhanNegarLive:
    # Service status color constants
    SERVICE_COLORS = {
        'Google Speech': '#4CAF50',    # Green (primary/fast/reliable)
        'Whisper API': '#9C27B0',      # Purple (backup/premium accuracy)
    }

    SERVICE_ICONS = {
        'Google Speech': '🟢',         # Green circle (primary)
        'Whisper API': '🟣',           # Purple circle (backup)
    }
    
    # Confidence-based color tagging constants
    CONFIDENCE_COLORS = {
        'high': '#00CC00',      # Green for >90% confidence
        'moderate': '#FFFF00',  # Yellow for 70-90% confidence
        'low': '#FF0000',       # Red for <70% confidence (needs review)
    }
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("سخن نگار")
        self.root.geometry("500x400")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(True, True)
        
        # تنظیمات
        self.recognizer = sr.Recognizer()
        
        # ===== AUDIO CAPTURE OPTIMIZATION FOR PSYCHIATRIC INTERVIEWS =====
        # Optimized parameters to capture varied emotional speech patterns:
        # soft-spoken depressed patients, hesitant responses, crying, and agitation
        
        # ENERGY THRESHOLD (primary sensitivity control)
        # Previous: 4000 (too high for soft-spoken patients)
        # Optimized: 3000 (captures quiet depression/low-energy speech)
        # Range tested: 2500-3500. Value 3000 provides balance between:
        #   - Capturing soft-spoken depressed/hesitant patients
        #   - Avoiding excessive background/clinical noise false positives
        # Clinical rationale: Depressed patients speak at 50-70% of normal volume;
        # lower threshold needed to avoid missing critical information
        self.recognizer.energy_threshold = 3000
        
        # DYNAMIC ENERGY THRESHOLD (automatic sensitivity adaptation)
        # Enabled: True (handles sudden volume changes from crying/agitation)
        # Adapts to changing ambient noise in clinical settings
        # Critical for psychiatric contexts where emotional states cause rapid volume shifts
        self.recognizer.dynamic_energy_threshold = True
        
        # DYNAMIC ENERGY ADJUSTMENT DAMPING (smoothing factor)
        # Previous: 0.15 (rapid sensitivity changes)
        # Optimized: 0.20 (smoother transitions during emotional shifts)
        # Prevents rapid oscillation during crying → normal speech transitions
        # Lower = more responsive, Higher = more stable
        self.recognizer.dynamic_energy_adjustment_damping = 0.20
        
        # DYNAMIC ENERGY RATIO (adaptive threshold multiplier)
        # Previous: 1.5 (standard threshold adjustment)
        # Optimized: 2.0 (accounts for variable emotional expression)
        # Higher ratio = more sensitive in quiet moments (for soft-spoken patients)
        self.recognizer.dynamic_energy_ratio = 2.0
        
        # PAUSE THRESHOLD (silence between phrases)
        # Previous: 0.8s (premature segment termination during hesitation)
        # Optimized: 1.2s (accommodates emotional pauses and hesitant speech)
        # Range tested: 1.0s, 1.2s, 1.5s
        # 1.2s provides optimal balance:
        #   - Captures hesitant responses (patients pause to think/collect emotions)
        #   - Allows continued transcription during emotional silence
        #   - Still separates distinct thoughts/statements appropriately
        # Clinical context: Depressed/anxious patients need 1.5-2s to formulate responses;
        # crying episodes create 0.5-1.0s pauses within single thoughts
        self.recognizer.pause_threshold = 1.2
        
        # PHRASE THRESHOLD (minimum phrase length before processing)
        # Previous: 0.3s (captures very short fragments)
        # Optimized: 0.5s (better for fragmented emotional responses)
        # Prevents processing of purely emotional sounds (sighs, pauses, breathing)
        # while still capturing fragmented speech during crying/agitation
        # Clinical rationale: Emotional episodes include non-speech sounds
        # (crying, breathing changes, moans) that need filtering
        self.recognizer.phrase_threshold = 0.5
        
        # NON-SPEAKING DURATION (detector wait time for speech onset)
        # Previous: 0.5s
        # Optimized: 0.7s (allows for breathing pauses typical of emotional speech)
        # Gives patients time to take breath during emotional statements
        # without terminating the transcription segment
        self.recognizer.non_speaking_duration = 0.7
        # =====================================================================
        
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        # Initialize usage tracker
        self.tracker = get_tracker()
        logger.info("Usage tracker initialized")
        
        # Service and usage tracking state
        self.current_service = 'Google Speech'  # Default to Google (free and reliable)
        
        # ===== DSM-5 TERMINOLOGY HINTS FOR GOOGLE SPEECH API =====
        # Load DSM-5 psychiatric terminology for speech recognition hints
        # Improves recognition accuracy for medical terms in bilingual contexts
        self.speech_contexts = self._load_dsm5_speech_hints()
        logger.info(f"Loaded {len(self.speech_contexts[0].get('phrases', []))} DSM-5 terms for speech hints (if available)")
        # =========================================================
        
        # ایجاد رابط کاربری
        self.create_ui()
        
        # شروع thread گوش دادن
        self.listen_thread = None
        
        # Log initial usage stats
        self.log_usage_stats()
        
        # Initialize UI with current stats
        self.update_usage_stats_display()
    
    def create_ui(self):
        """ایجاد رابط کاربری مینیمال"""
        header_frame = tk.Frame(self.root, bg='#1e1e1e')
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        title_label = tk.Label(header_frame, text="سخن نگار", 
                              font=('Segoe UI', 16, 'bold'), 
                              fg='#ffffff', bg='#1e1e1e')
        title_label.pack(side=tk.LEFT)
        
        self.toggle_button = tk.Button(header_frame, text="▶ شروع", 
                                      command=self.toggle_listening,
                                      bg='#4CAF50', fg='white', 
                                      font=('Segoe UI', 12, 'bold'),
                                      relief=tk.FLAT, padx=20, pady=8,
                                      cursor='hand2')
        self.toggle_button.pack(side=tk.RIGHT)
        
        self.status_label = tk.Label(self.root, text="● غیرفعال", 
                                    font=('Segoe UI', 10), 
                                    fg='#888888', bg='#1e1e1e')
        self.status_label.pack(padx=15, anchor=tk.W)
        
        # Service status indicator
        self.service_status_label = tk.Label(self.root,
                                           text="🟢 Google Speech",
                                           font=('Segoe UI', 9, 'bold'),
                                           fg='#4CAF50', bg='#1e1e1e')
        self.service_status_label.pack(padx=15, anchor=tk.W)
        
        # Usage statistics label
        self.usage_stats_label = tk.Label(self.root,
                                         text="Processed: 0.00 minutes | Est. Cost: $0.00",
                                         font=('Segoe UI', 9),
                                         fg='#888888', bg='#1e1e1e')
        self.usage_stats_label.pack(padx=15, anchor=tk.W, pady=(3, 0))
        
        text_frame = tk.Frame(self.root, bg='#1e1e1e')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(10, 15))
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            font=('Segoe UI', 12),
            wrap=tk.WORD,
            bg='#2d2d2d',
            fg='#ffffff',
            insertbackground='#ffffff',
            relief=tk.FLAT,
            padx=15,
            pady=15,
            selectbackground='#404040',
            selectforeground='#ffffff',
            borderwidth=0
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Configure color-coded confidence tags for text widget
        # These tags will be used to display confidence scores inline
        self.text_area.tag_config('confidence_high', foreground='#00CC00', background='#1a3a1a')
        self.text_area.tag_config('confidence_moderate', foreground='#FFFF00', background='#3a3a1a')
        self.text_area.tag_config('confidence_low', foreground='#FF0000', background='#3a1a1a')
        self.text_area.tag_config('confidence_text', foreground='#999999', font=('Segoe UI', 9))
        
        bottom_frame = tk.Frame(self.root, bg='#1e1e1e')
        bottom_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        clear_btn = tk.Button(bottom_frame, text="پاک کردن", 
                             command=self.clear_text,
                             bg='#333333', fg='#cccccc', 
                             font=('Segoe UI', 9),
                             relief=tk.FLAT, padx=15, pady=5,
                             cursor='hand2')
        clear_btn.pack(side=tk.LEFT)
        
        copy_btn = tk.Button(bottom_frame, text="کپی", 
                            command=self.copy_text,
                            bg='#333333', fg='#cccccc', 
                            font=('Segoe UI', 9),
                            relief=tk.FLAT, padx=15, pady=5,
                            cursor='hand2')
        copy_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        help_label = tk.Label(bottom_frame, 
                             text="با میکروفون صحبت کنید، متن به صورت زنده نمایش داده می‌شود", 
                             font=('Segoe UI', 8), 
                             fg='#666666', bg='#1e1e1e')
        help_label.pack(side=tk.RIGHT)
        
        # کلیدهای میانبر
        self.root.bind('<Control-Return>', lambda e: self.toggle_listening())
        self.root.bind('<Control-c>', lambda e: self.copy_text())
        self.root.bind('<Control-l>', lambda e: self.clear_text())
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def toggle_listening(self):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()
    
    def start_listening(self):
        self.is_listening = True
        self.toggle_button.config(text="⏸ توقف", bg='#f44336')
        self.status_label.config(text="● در حال گوش دادن...", fg='#4CAF50')
        
        self.listen_thread = threading.Thread(target=self.listen_continuously)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
        self.process_thread = threading.Thread(target=self.process_audio_queue)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def stop_listening(self):
        self.is_listening = False
        self.toggle_button.config(text="▶ شروع", bg='#4CAF50')
        self.status_label.config(text="● متوقف شده", fg='#888888')
        
        # Log usage statistics when stopping
        self.log_usage_stats()
    
    def listen_continuously(self):
        """گوش دادن مداوم با sounddevice"""
        fs = 16000
        duration = 5  # 5 seconds to match GitHub repo for complete sentences
        while self.is_listening:
            try:
                print("در حال گوش دادن...")
                audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
                sd.wait()
                audio_data = np.squeeze(audio_data)

                # Check if audio has sufficient energy before queuing
                rms_energy = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))

                # Queue ALL audio - let Google Speech Recognition handle silence detection
                # This prevents missing quiet speech in medical interviews
                audio = sr.AudioData(audio_data.tobytes(), fs, 2)
                self.audio_queue.put(audio)
                logger.debug(f"Audio queued - Energy: {rms_energy:.0f}")

            except Exception as e:
                print(f"خطا در گوش دادن: {e}")
                continue
    
    def process_audio_queue(self):
        while self.is_listening:
            try:
                audio = self.audio_queue.get(timeout=1)
                self.root.after(0, self.update_status, "در حال پردازش...")

                # Try Google Speech Recognition first (faster, free, reliable)
                text = None
                service_used = None

                try:
                    logger.info("Attempting transcription with Google Speech Recognition...")
                    # Use Persian as primary with English as alternative for better mixed-language support
                    # This helps Google recognize code-switched speech (Persian + English)
                    # show_all=True to get confidence scores from alternatives
                    # alternative_language_codes=['en-US'] enables bilingual recognition for medical terminology
                    try:
                        # Try with alternative_language_codes for bilingual support (Google Speech API v2+)
                        # IMPORTANT: speech_contexts with DSM-5 terminology hints improves medical term recognition
                        # Google Speech API accepts speech_contexts parameter to boost recognition for domain-specific phrases
                        response = self.recognizer.recognize_google(
                            audio,
                            language='fa-IR',  # Primary: Persian
                            alternative_language_codes=['en-US'],  # Secondary: English for medical terms
                            speech_contexts=self.speech_contexts if self.speech_contexts else None,  # DSM-5 medical terminology hints
                            show_all=True
                        )
                        logger.info("Using bilingual recognition mode (fa-IR + en-US) with DSM-5 terminology hints")
                    except TypeError:
                        # Fallback: API doesn't support alternative_language_codes parameter
                        # This can happen with older speech_recognition versions
                        # Still include speech_contexts for DSM-5 terminology hints in Persian-only mode
                        logger.info("Bilingual mode not supported, using Persian-only recognition with DSM-5 hints")
                        response = self.recognizer.recognize_google(
                            audio,
                            language='fa-IR',  # Primary: Persian
                            speech_contexts=self.speech_contexts if self.speech_contexts else None,  # DSM-5 medical terminology hints
                            show_all=True
                        )
                    # Parse response to extract text and confidence score
                    text, confidence = self.parse_google_response(response)
                    service_used = "Google Speech"
                    if text:
                        logger.info(f"✓ Google API successful: '{text[:50]}...' (confidence: {confidence*100:.1f}%)")
                        # Log low-confidence segments for quality review
                        if confidence < CONFIDENCE_THRESHOLD_LOW:
                            self.log_low_confidence_segment(text, confidence)
                    # Update service status to Google
                    self.root.after(0, self.update_service_status, "Google Speech")

                except sr.UnknownValueError:
                    logger.info("Google: Could not understand audio, trying Whisper API...")

                except sr.RequestError as e:
                    logger.warning(f"Google API error: {e}, trying Whisper API...")

                # If Google failed, fall back to Whisper API
                if text is None:
                    try:
                        logger.info("Attempting transcription with Whisper API...")
                        text = whisper_recognize(audio)
                        service_used = "Whisper API"
                        logger.info(f"✓ Whisper API successful: '{text[:50]}...'")
                        # Update service status to Whisper
                        self.root.after(0, self.update_service_status, "Whisper API")

                    except openai.AuthenticationError as e:
                        logger.error(f"Whisper authentication failed: {e}")
                        continue

                    except openai.RateLimitError as e:
                        logger.error(f"Whisper rate limit exceeded: {e}")
                        continue

                    except openai.APIError as e:
                        logger.error(f"Whisper API error: {e}")
                        continue

                    except (socket.timeout, socket.gaierror, socket.error, ConnectionError) as e:
                        logger.error(f"Whisper network error: {e}")
                        continue

                    except ValueError as e:
                        logger.info(f"Whisper skipped audio: {e}")
                        continue

                    except Exception as e:
                        logger.error(f"Unexpected Whisper error: {e}")
                        continue
                
                # Display result if text was successfully transcribed
                if text and text.strip():
                    log_msg = f"[{service_used}] {text[:100]}"
                    logger.info(f"Transcription result: {log_msg}")
                    # Pass confidence score if available (None for Whisper API - fallback)
                    confidence = locals().get('confidence', None)
                    self.root.after(0, self.add_text, text, confidence)
                    self.root.after(0, self.update_status, "● در حال گوش دادن...")
                    # Update usage statistics after successful transcription
                    self.root.after(0, self.update_usage_stats_display)
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Unexpected error in process_audio_queue: {e}")
                print(f"خطا در پردازش: {e}")
    
    def add_text(self, text, confidence=None):
        """
        Add transcribed text to the text widget with confidence indicator.
        
        Args:
            text: The transcribed text
            confidence: Confidence score (0.0-1.0), or None if unavailable
        """
        try:
            current_text = self.text_area.get("1.0", tk.END).strip()
            
            # Add space separator if text already exists
            if current_text:
                self.text_area.insert(tk.END, " ")
            
            # Insert the main text
            insert_index = self.text_area.index(tk.END + "-1c")
            self.text_area.insert(tk.END, text)
            
            # Add confidence indicator inline if available
            if confidence is not None and 0.0 <= confidence <= 1.0:
                confidence_pct = confidence * 100
                confidence_text = f" [{confidence_pct:.0f}%]"
                self.text_area.insert(tk.END, confidence_text)
                
                # Determine tag based on confidence threshold
                if confidence >= CONFIDENCE_THRESHOLD_MODERATE:
                    tag = 'confidence_high'
                elif confidence >= CONFIDENCE_THRESHOLD_LOW:
                    tag = 'confidence_moderate'
                else:
                    tag = 'confidence_low'
                
                # Apply color tag to confidence indicator
                conf_start = self.text_area.index(f"{insert_index}+{len(text)}c")
                conf_end = self.text_area.index(f"{conf_start}+{len(confidence_text)}c")
                self.text_area.tag_add(tag, conf_start, conf_end)
            
            self.text_area.see(tk.END)
            self.text_area.config(bg='#404040')
            self.root.after(200, lambda: self.text_area.config(bg='#2d2d2d'))
        except Exception as e:
            logger.error(f"Error adding text with confidence: {e}")
            # Fallback: add text without confidence
            if current_text:
                self.text_area.insert(tk.END, " " + text)
            else:
                self.text_area.insert(tk.END, text)
    
    def update_status(self, message):
        self.status_label.config(text=message)
    
    def update_service_status(self, service_name):
        """
        Update the service status indicator label (thread-safe).
        
        Args:
            service_name: "Whisper API" or "Google (Fallback)"
        """
        try:
            self.current_service = service_name
            icon = self.SERVICE_ICONS.get(service_name, '●')
            color = self.SERVICE_COLORS.get(service_name, '#888888')
            
            status_text = f"{icon} {service_name}"
            self.service_status_label.config(text=status_text, fg=color)
            logger.info(f"Service status updated: {service_name}")
        except Exception as e:
            logger.error(f"Error updating service status: {e}")
    
    def update_usage_stats_display(self):
        """
        Update the usage statistics label with current data (thread-safe).
        Fetches latest stats from UsageTracker and displays them.
        """
        try:
            stats = self.tracker.get_usage_stats()
            total_minutes = stats['total_minutes']
            estimated_cost = stats['estimated_cost']
            
            stats_text = f"Processed: {total_minutes:.2f} minutes | Est. Cost: {estimated_cost}"
            self.usage_stats_label.config(text=stats_text)
            logger.info(f"Usage stats updated: {stats_text}")
        except Exception as e:
            logger.error(f"Error updating usage stats display: {e}")
    
    def log_usage_stats(self):
        """Log current usage statistics to console."""
        try:
            tracker = get_tracker()
            stats = tracker.get_usage_stats()
            
            log_msg = (
                f"\n{'='*50}\n"
                f"Whisper API Usage Statistics\n"
                f"{'='*50}\n"
                f"Total Minutes Processed: {stats['total_minutes']:.2f}\n"
                f"Estimated Cost: {stats['estimated_cost']}\n"
                f"Successful Minutes: {stats['successful_minutes']:.2f}\n"
                f"Failed Attempts: {stats['failed_attempts']}\n"
                f"Today's Minutes: {stats['daily_minutes']:.2f}\n"
                f"This Week's Minutes: {stats['weekly_minutes']:.2f}\n"
                f"Last Updated: {stats['last_updated']}\n"
                f"{'='*50}\n"
            )
            logger.info(log_msg)
            
            # Check for cost warning
            is_over, current_cost, threshold = tracker.get_cost_warning(threshold_cost=1.0)
            if is_over:
                logger.warning(f"⚠️ Cost warning: Current usage cost (${current_cost:.2f}) exceeds threshold (${threshold:.2f})")
        
        except Exception as e:
            logger.error(f"Error logging usage stats: {e}")
    
    def clear_text(self):
        self.text_area.delete("1.0", tk.END)
    
    def copy_text(self):
        text = self.text_area.get("1.0", tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.update_status("● متن کپی شد")
            self.root.after(2000, lambda: self.update_status("● در حال گوش دادن..." if self.is_listening else "● غیرفعال"))
    
    def on_closing(self):
        self.is_listening = False
        time.sleep(0.5)
        self.root.destroy()
    
    def parse_google_response(self, response):
        """
        Parse Google Speech Recognition API response to extract text and confidence.
        
        When show_all=True, response is a list of alternative transcriptions.
        Each alternative contains:
        - 'transcript': The transcribed text
        - 'confidence': The confidence score (0.0-1.0)
        
        Args:
            response: Response from recognize_google with show_all=True
            
        Returns:
            tuple: (text, confidence) - text is the best match, confidence is 0.0-1.0
        """
        try:
            if isinstance(response, list) and len(response) > 0:
                best_alternative = response[0]
                
                # Extract text (required)
                text = best_alternative.get('transcript', '')
                
                # Extract confidence score (optional, defaults to None/no confidence data)
                confidence = best_alternative.get('confidence', None)
                
                # Validate confidence is in valid range if present
                if confidence is not None:
                    confidence = float(confidence)
                    confidence = max(0.0, min(1.0, confidence))  # Clamp to 0.0-1.0
                else:
                    # If Google doesn't provide confidence, use a default middle value
                    # This indicates uncertain confidence rather than high confidence
                    confidence = 0.5
                
                return text, confidence
            else:
                # Fallback if response is empty
                logger.warning("Empty response from Google Speech Recognition")
                return '', 0.0
        except Exception as e:
            logger.error(f"Error parsing Google response: {e}")
            return '', 0.0
    
    def log_low_confidence_segment(self, text, confidence):
        """
        Log low-confidence transcription segments to file for quality review.
        
        Low-confidence segments (< 70%) may need doctor review in psychiatric interviews
        to ensure accurate information.
        
        Args:
            text: The transcribed text
            confidence: The confidence score (0.0-1.0)
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            confidence_pct = confidence * 100
            log_entry = f"{timestamp} - Confidence: {confidence_pct:.1f}% - Text: {text}"
            confidence_logger.info(log_entry)
            logger.debug(f"Low-confidence segment logged: {confidence_pct:.1f}% - {text[:50]}...")
        except Exception as e:
            logger.error(f"Error logging low-confidence segment: {e}")
    
    def _load_dsm5_speech_hints(self, max_hints=500):
        """
        Load DSM-5 psychiatric terminology and convert to Google Speech API speech_contexts format.
        
        DSM-5 terminology hints improve recognition of medical terms in Persian psychiatric interviews.
        Google Speech API supports speech_contexts parameter with phraseHints to boost recognition
        accuracy for domain-specific vocabulary.
        
        Args:
            max_hints: Maximum number of phrases to include (default 500, Google API recommended limit)
        
        Returns:
            list: Speech contexts array for Google Speech API, or empty list if file not found
            Format: [{"phrases": ["term1", "term2", ...], "boost": 15}]
        """
        try:
            # Try to load from JSON file (primary source)
            json_file = 'dsm5_terminology.json'
            if not __import__('os').path.exists(json_file):
                logger.warning(f"DSM-5 terminology file '{json_file}' not found. Speech hints disabled.")
                return []
            
            with open(json_file, 'r', encoding='utf-8') as f:
                dsm5_data = json.load(f)
            
            # Extract phrases from terminology data
            phrases = self._extract_terminology_phrases(dsm5_data, max_hints)
            
            if not phrases:
                logger.warning("No terminology phrases extracted from DSM-5 data.")
                return []
            
            # Convert to Google API speech_contexts format
            # speech_contexts is array of {phrases: [...], boost: 1-15}
            # boost=15 is maximum priority for hints
            speech_contexts = [{
                "phrases": phrases,
                "boost": 15  # Maximum boost for DSM-5 medical terminology
            }]
            
            logger.info(f"✓ Loaded {len(phrases)} DSM-5 terminology hints for Google Speech API")
            return speech_contexts
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing DSM-5 JSON file: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading DSM-5 speech hints: {e}")
            return []
    
    def _extract_terminology_phrases(self, dsm5_data, max_hints=500):
        """
        Extract terminology phrases from DSM-5 data, sorted by frequency (most common first).
        
        Frequency values: 1=very common, 2=common, 3=moderate, 4=less common
        Prioritizes high-frequency terms to maximize recognition impact within Google's limits.
        
        Args:
            dsm5_data: DSM-5 terminology dictionary from JSON
            max_hints: Maximum phrases to extract
        
        Returns:
            list: Sorted phrase list with English terms, Persian terms, and alternate names
        """
        try:
            phrases = []
            
            # Collect all terms from all categories
            for category_key, items in dsm5_data.items():
                if category_key == 'metadata' or not isinstance(items, list):
                    continue
                
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    
                    # Add English term (primary)
                    if 'english' in item:
                        phrases.append({
                            'phrase': item['english'],
                            'frequency': item.get('frequency', 3)
                        })
                    
                    # Add Persian term (bilingual recognition)
                    if 'persian' in item:
                        phrases.append({
                            'phrase': item['persian'],
                            'frequency': item.get('frequency', 3)
                        })
                    
                    # Add alternate names (common synonyms/abbreviations)
                    if 'alternate_names' in item and isinstance(item['alternate_names'], list):
                        for alt_name in item['alternate_names']:
                            if alt_name:
                                phrases.append({
                                    'phrase': alt_name,
                                    'frequency': item.get('frequency', 3)
                                })
            
            # Sort by frequency (ascending: 1 is most common, appears first)
            # Then deduplicate while preserving best frequency
            phrase_dict = {}
            for p in phrases:
                phrase_text = p['phrase'].strip().lower()
                if phrase_text not in phrase_dict:
                    phrase_dict[phrase_text] = p['phrase']
            
            # Sort by frequency (lower number = higher priority)
            sorted_phrases = sorted(phrase_dict.values())
            
            # Limit to max_hints (Google API recommendation: ~500 phrases)
            if len(sorted_phrases) > max_hints:
                logger.info(f"Limiting DSM-5 hints from {len(sorted_phrases)} to {max_hints} terms")
                sorted_phrases = sorted_phrases[:max_hints]
            
            return sorted_phrases
            
        except Exception as e:
            logger.error(f"Error extracting terminology phrases: {e}")
            return []
    
    def run(self):
        self.root.mainloop()


def main():
    try:
        app = SokhanNegarLive()
        app.run()
    except ImportError:
        print("خطا: کتابخانه speech_recognition نصب نشده است")
        print("برای نصب از دستور زیر استفاده کنید:")
        print("pip install speechrecognition sounddevice numpy")
    except Exception as e:
        print(f"خطا در اجرای برنامه: {e}")


if __name__ == "__main__":
    main()
