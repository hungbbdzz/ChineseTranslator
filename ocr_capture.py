# -*- coding: utf-8 -*-
"""
OCR Screen Capture Module
Capture screen region and extract Chinese text using Tesseract
"""

import tkinter as tk
from PIL import Image, ImageGrab, ImageTk, ImageEnhance
import threading
import os
import shutil
import atexit
from logger_utils import get_logger

# Set up logging
logger = get_logger(__name__)

# Lazy load pytesseract
_pytesseract = None

def _get_pytesseract():
    global _pytesseract
    if _pytesseract is None:
        try:
            import pytesseract
            # Try to find Tesseract in common locations
            # Try to find Tesseract in common locations
            import shutil
            import os
            
            # 1. Check PATH
            tesseract_path = shutil.which("tesseract")
            
            # 2. Check common Windows paths
            if not tesseract_path:
                common_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
                    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        tesseract_path = path
                        break
            
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                print(f"Tesseract found: {tesseract_path}")
            else:
                print("Warning: Tesseract executable not found.")
                
            _pytesseract = pytesseract
        except ImportError:
            print("pytesseract not installed. Run: pip install pytesseract")
            _pytesseract = None
    return _pytesseract


def check_tesseract_availability():
    """Check if Tesseract is installed and configured."""
    _get_pytesseract()
    if _pytesseract and hasattr(_pytesseract, 'pytesseract'):
        return shutil.which(_pytesseract.pytesseract.tesseract_cmd) is not None or \
               os.path.exists(_pytesseract.pytesseract.tesseract_cmd)
    return False

class ScreenCapture:
    """Allows user to select a region on screen and captures it"""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.canvas = None
        self.root = None
    
    def capture(self):
        """Start selection overlay"""
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.3)
        self.root.configure(bg='gray')
        
        self.canvas = tk.Canvas(self.root, cursor="cross", bg='gray', 
                                highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        self.canvas.bind('<Button-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.root.bind('<Escape>', lambda e: self._cancel())
        
        self.root.focus_force()
    
    def _on_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline='red', width=2
        )
    
    def _on_drag(self, event):
        if self.rect_id and self.start_x is not None:
            x1 = self.canvas.canvasx(self.start_x)
            y1 = self.canvas.canvasy(self.start_y)
            x2 = event.x
            y2 = event.y
            self.canvas.coords(self.rect_id, 
                             min(self.start_x, event.x_root),
                             min(self.start_y, event.y_root),
                             max(self.start_x, event.x_root),
                             max(self.start_y, event.y_root))
    
    def _on_release(self, event):
        end_x = event.x_root
        end_y = event.y_root
        
        # Calculate bounding box
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        # Close overlay immediately
        self.root.destroy()
        
        # Check if selection is too small
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            if self.callback:
                self.callback(None, "Vùng chọn quá nhỏ")
            return
        
        # Small delay to let overlay disappear
        self.root.after_idle(lambda: self._do_capture(x1, y1, x2, y2))
    
    def _do_capture(self, x1, y1, x2, y2):
        try:
            import time
            time.sleep(0.1)  # Let overlay fully disappear
            
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            if self.callback:
                self.callback(screenshot, None)
        except Exception as e:
            if self.callback:
                self.callback(None, str(e))
    
    def _cancel(self):
        self.root.destroy()
        if self.callback:
            self.callback(None, "Đã hủy")


# ─── Improvement #1: Engine Cache ────────────────────────────────────────────
_rapidocr_engine = None
_rapidocr_lock = threading.Lock()

def _get_rapidocr_engine():
    """Return a cached RapidOCR engine (initialized only once)."""
    global _rapidocr_engine
    if _rapidocr_engine is None:
        with _rapidocr_lock:
            if _rapidocr_engine is None:  # double-check inside lock
                from rapidocr_onnxruntime import RapidOCR
                print("[OCR] Initializing RapidOCR engine (first time)...")
                _rapidocr_engine = RapidOCR(use_angle_cls=True)
                print("[OCR] RapidOCR engine ready and cached.")
    return _rapidocr_engine
# ──────────────────────────────────────────────────────────────────────────────


def check_rapidocr_availability():
    """Check if RapidOCR is installed"""
    try:
        import rapidocr_onnxruntime
        return True
    except ImportError:
        return False


def _preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Improvement #2: Upscale small images and boost contrast/sharpness
    for better OCR accuracy on game text with small fonts."""
    # Upscale if too small (e.g. tiny game subtitles)
    w, h = image.size
    if w < 600 or h < 80:
        scale = max(600 / w, 80 / h, 2.0)  # at least 2x
        new_w = int(w * scale)
        new_h = int(h * scale)
        image = image.resize((new_w, new_h), Image.LANCZOS)

    # Boost contrast and sharpness
    image = ImageEnhance.Contrast(image).enhance(1.6)
    image = ImageEnhance.Sharpness(image).enhance(1.4)
    return image


def extract_text(image, lang='chinese'):
    """
    Extract text using RapidOCR (Offline, High Accuracy).
    Uses a cached engine (initialized once) and preprocesses the image.
    Args:
        image: PIL Image object
        lang: Ignored (kept for compatibility)
    Returns:
        text (str), error (str)
    """
    if not check_rapidocr_availability():
        return "", "Chưa cài đặt RapidOCR. Vui lòng cài đặt trong App."

    try:
        import numpy as np

        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Improvement #2: preprocess before OCR
        image = _preprocess_for_ocr(image)

        img_np = np.array(image)

        # Improvement #1: use cached engine
        engine = _get_rapidocr_engine()

        # Run OCR
        result, elapse = engine(img_np)

        if not result:
            return "", None

        # Result format: [[box, text, score], ...]
        text_lines = [line[1] for line in result]

        # Combine text (Chinese usually has no spaces)
        combined_text = "".join(text_lines)
        combined_text = combined_text.replace(" ", "")

        return combined_text, None

    except Exception as e:
        print(f"RapidOCR Error: {e}")
        return "", f"(Lỗi RapidOCR: {e})"


def capture_and_ocr(callback, lang='chinese'):
    """
    Convenience function: Capture screen region and OCR.
    """
    def on_capture(image, error):
        if error:
            callback(None, error)
            return
        
        if image:
            text, ocr_error = extract_text(image, lang=lang)
            callback(text, ocr_error)
        else:
            callback(None, "Không có ảnh")
    
    capturer = ScreenCapture(callback=on_capture)
    capturer.capture()


class FrozenScreenCapture:
    """
    Game-compatible capture: Takes a full screenshot instantly (like PrintScreen,
    without stealing game focus), then overlays it as a frozen image so the user
    can drag-select a region — all without disturbing the running game.

    Usage: always call via capture_frozen_and_ocr() which handles thread-safety.
    """

    def __init__(self, callback=None, tk_root=None):
        self.callback = callback
        self.tk_root = tk_root  # Main tkinter root for scheduling on main thread
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.screenshot = None  # PIL Image of full screen

    def grab_screen_then_overlay(self):
        """Run in background thread: grab screen, then schedule overlay on main thread."""
        import time
        time.sleep(0.05)  # tiny delay so any key-up animation settles
        self.screenshot = ImageGrab.grab()
        # Schedule overlay creation on the main (tkinter) thread
        if self.tk_root:
            self.tk_root.after(0, self._show_overlay)
        else:
            # Fallback: run directly (only safe if already on main thread)
            self._show_overlay()

    def _show_overlay(self):
        """Create fullscreen overlay with frozen screenshot as background (main thread)."""
        self.win = tk.Toplevel()
        self.win.attributes('-fullscreen', True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg='black')
        self.win.overrideredirect(True)

        # Convert PIL screenshot to Tk image (must keep reference!)
        self.tk_image = ImageTk.PhotoImage(self.screenshot)

        self.canvas = tk.Canvas(
            self.win,
            cursor='cross',
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill='both', expand=True)

        # Draw frozen screenshot as background
        self.canvas.create_image(0, 0, anchor='nw', image=self.tk_image)

        # Draw dim overlay via stipple (no real alpha needed)
        sw = self.screenshot.width
        sh = self.screenshot.height
        self.canvas.create_rectangle(
            0, 0, sw, sh,
            fill='black', stipple='gray25', outline=''
        )

        # Hint text
        self.canvas.create_text(
            sw // 2, 40,
            text='🖱️ Kéo để chọn vùng chữ  •  ESC để hủy',
            fill='white',
            font=('Segoe UI', 16, 'bold'),
        )

        self.canvas.bind('<Button-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.win.bind('<Escape>', lambda e: self._cancel())
        self.win.focus_force()

    def _on_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline='#ff5555', width=2, dash=(4, 2)
        )

    def _on_drag(self, event):
        if self.rect_id and self.start_x is not None:
            self.canvas.coords(
                self.rect_id,
                min(self.start_x, event.x_root),
                min(self.start_y, event.y_root),
                max(self.start_x, event.x_root),
                max(self.start_y, event.y_root),
            )

    def _on_release(self, event):
        end_x = event.x_root
        end_y = event.y_root

        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        self.win.destroy()

        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            if self.callback:
                self.callback(None, 'Vùng chọn quá nhỏ')
            return

        # Crop from already-captured screenshot — no second grab needed
        cropped = self.screenshot.crop((x1, y1, x2, y2))
        if self.callback:
            self.callback(cropped, None)

    def _cancel(self):
        self.win.destroy()
        if self.callback:
            self.callback(None, 'Đã hủy')


def capture_frozen_and_ocr(callback, lang='chinese', tk_root=None):
    """
    Game-compatible OCR: Instantly captures full screen (no focus switch),
    overlays frozen image for region selection, then runs OCR.

    Works even when a fullscreen game is running.

    Args:
        callback: fn(text, error) called with OCR result
        lang: language hint (default 'chinese')
        tk_root: the main tk.Tk() root window (required for thread-safety)
    """
    def on_capture(image, error):
        if error:
            callback(None, error)
            return
        if image:
            # Run OCR in a background thread to keep UI responsive
            def do_ocr():
                text, ocr_error = extract_text(image, lang=lang)
                callback(text, ocr_error)
            threading.Thread(target=do_ocr, daemon=True).start()
        else:
            callback(None, 'Không có ảnh')

    capturer = FrozenScreenCapture(callback=on_capture, tk_root=tk_root)
    # Screenshot happens in background thread (doesn't need focus)
    threading.Thread(target=capturer.grab_screen_then_overlay, daemon=True).start()



# Test
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    def on_result(text, error):
        if error:
            print(f"Error: {error}")
        else:
            print(f"OCR Result: {text}")
        root.quit()
    
    print("Click and drag to select region...")
    root.after(100, lambda: capture_and_ocr(on_result))
    root.mainloop()
