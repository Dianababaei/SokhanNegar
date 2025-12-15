import tkinter as tk
from tkinter import scrolledtext, messagebox
import speech_recognition as sr
import threading
import queue
import time
import sounddevice as sd
import numpy as np

class SokhanNegarLive:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("سخن نگار")
        self.root.geometry("500x400")
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(True, True)
        
        # تنظیمات
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.audio_queue = queue.Queue()
        
        # ایجاد رابط کاربری
        self.create_ui()
        
        # شروع thread گوش دادن
        self.listen_thread = None
    
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
    
    def listen_continuously(self):
        """گوش دادن مداوم با sounddevice"""
        fs = 16000
        duration = 5
        while self.is_listening:
            try:
                print("در حال گوش دادن...")
                audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
                sd.wait()
                audio_data = np.squeeze(audio_data)
                audio = sr.AudioData(audio_data.tobytes(), fs, 2)
                self.audio_queue.put(audio)
            except Exception as e:
                print(f"خطا در گوش دادن: {e}")
                continue
    
    def process_audio_queue(self):
        while self.is_listening:
            try:
                audio = self.audio_queue.get(timeout=1)
                self.root.after(0, self.update_status, "در حال پردازش...")
                text = self.recognizer.recognize_google(audio, language='fa-IR')
                if text.strip():
                    self.root.after(0, self.add_text, text)
                    self.root.after(0, self.update_status, "● در حال گوش دادن...")
            except queue.Empty:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                self.root.after(0, self.update_status, f"خطا در سرویس: {e}")
                time.sleep(2)
                self.root.after(0, self.update_status, "● در حال گوش دادن...")
            except Exception as e:
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
