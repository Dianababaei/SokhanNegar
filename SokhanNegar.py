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
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("سخن نگار")
        self.root.geometry("500x400")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(True, True)
        
        # تنظیمات
        self.recognizer = sr.Recognizer()
        # Adjust recognizer settings optimized for your microphone
        self.recognizer.energy_threshold = 4000  # Matches GitHub repo settings
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.8  # Matches GitHub repo (0.8s between phrases)
        self.recognizer.phrase_threshold = 0.3  # Minimum phrase length
        self.recognizer.non_speaking_duration = 0.5  # Wait for pauses
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        # Initialize usage tracker
        self.tracker = get_tracker()
        logger.info("Usage tracker initialized")
        
        # Service and usage tracking state
        self.current_service = 'Google Speech'  # Default to Google (free and reliable)
        
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
                    text = self.recognizer.recognize_google(
                        audio,
                        language='fa-IR',  # Primary: Persian
                        show_all=False
                    )
                    service_used = "Google Speech"
                    logger.info(f"✓ Google API successful: '{text[:50]}...'")
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
                    self.root.after(0, self.add_text, text)
                    self.root.after(0, self.update_status, "● در حال گوش دادن...")
                    # Update usage statistics after successful transcription
                    self.root.after(0, self.update_usage_stats_display)
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Unexpected error in process_audio_queue: {e}")
                print(f"خطا در پردازش: {e}")
    
    def add_text(self, text):
        current_text = self.text_area.get("1.0", tk.END).strip()
        if current_text:
            self.text_area.insert(tk.END, " " + text)
        else:
            self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)
        self.text_area.config(bg='#404040')
        self.root.after(200, lambda: self.text_area.config(bg='#2d2d2d'))
    
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
