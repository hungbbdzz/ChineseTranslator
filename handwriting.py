import tkinter as tk
from tkinter import ttk
import threading
import requests
import time
from logger_utils import get_logger

# Set up logging
logger = get_logger(__name__)

class HandwritingWindow:
    def __init__(self, parent, colors, on_char_selected):
        self.parent = parent
        self.colors = colors
        self.on_char_selected = on_char_selected
        
        self.window = tk.Toplevel(parent)
        self.window.title("✍️ Viết Tay")
        self.window.geometry("500x650")
        self.window.configure(bg=colors['bg'])
        self.window.attributes('-topmost', True)
        self.window.transient(parent)
        self.window.minsize(450, 600)
        
        # Center the window relative to parent
        try:
            x = parent.winfo_x() + 50
            y = parent.winfo_y() + 50
            self.window.geometry(f"+{x}+{y}")
        except:
            pass
            
        self.strokes = []
        self.current_stroke = None
        
        # We need to keep a list of canvas item IDs for each stroke to support undo
        self.stroke_items = []
        self.current_stroke_items = []
        
        self._build_ui()
        self._bind_events()
        
        # Debounce timer for recognition
        self._recognize_timer = None
        
    def _build_ui(self):
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(header_frame, text="Viết chữ Hán vào ô bên dưới:", 
                  font=('Segoe UI', 11, 'bold')).pack(side='left')
        
        # Canvas
        self.canvas_frame = ttk.Frame(main_frame)
        self.canvas_frame.pack(fill='both', expand=True, pady=5)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg=self.colors['surface'], 
                               highlightthickness=1,
                               highlightbackground=self.colors['surface2'],
                               cursor="pencil")
        self.canvas.pack(fill='both', expand=True)
        
        # Draw a grid on canvas to help with writing
        self.canvas.bind('<Configure>', self._draw_grid)
        
        # Clear/Undo buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="↩️ Hoàn tác", command=self.undo).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="🗑️ Xóa hết", command=self.clear).pack(side='left', padx=5)
        
        # Predictions container
        ttk.Label(main_frame, text="Dự đoán (Cuộn chuột xem thêm - Click để chọn):", 
                  font=('Segoe UI', 10)).pack(anchor='w', pady=(5, 5))
                  
        self.pred_canvas = tk.Canvas(main_frame, height=50, bg=self.colors['bg'], highlightthickness=0)
        self.pred_canvas.pack(fill='x', pady=(0, 10))
        
        self.pred_inner = ttk.Frame(self.pred_canvas)
        self.pred_canvas.create_window((0, 0), window=self.pred_inner, anchor='nw')
        
        self.pred_inner.bind("<Configure>", lambda e: self.pred_canvas.configure(scrollregion=self.pred_canvas.bbox("all")))
        
        self.pred_buttons = []
            
        def _on_mousewheel(event):
            try:
                bbox = self.pred_canvas.bbox("all")
                if not bbox: return "break"
                if bbox[2] - bbox[0] > self.pred_canvas.winfo_width():
                    self.pred_canvas.xview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass
            return "break" # Prevent propagation to global root bindings
            
        # Bind MouseWheel to window to capture all scroll events here
        self.window.bind("<MouseWheel>", _on_mousewheel)
        self.pred_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.pred_inner.bind("<MouseWheel>", _on_mousewheel)
        for btn in self.pred_buttons:
            btn.bind("<MouseWheel>", _on_mousewheel)
            
        # Status
        self.status_var = tk.StringVar(value="Sẵn sàng")
        ttk.Label(main_frame, textvariable=self.status_var, 
                  font=('Segoe UI', 9), foreground=self.colors['fg']).pack(anchor='w')

    def _draw_grid(self, event=None):
        self.canvas.delete("grid")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 1 and h > 1:
            # Draw cross
            self.canvas.create_line(w/2, 0, w/2, h, fill=self.colors['surface2'], dash=(4, 4), tags="grid")
            self.canvas.create_line(0, h/2, w, h/2, fill=self.colors['surface2'], dash=(4, 4), tags="grid")

    def _on_enter(self, btn):
        if btn['state'] != 'disabled':
            btn.configure(bg=self.colors['surface2'])
    
    def _on_leave(self, btn):
        if btn['state'] != 'disabled':
            btn.configure(bg=self.colors['surface'])

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self._start_stroke)
        self.canvas.bind("<B1-Motion>", self._draw_stroke)
        self.canvas.bind("<ButtonRelease-1>", self._end_stroke)
        
    def _start_stroke(self, event):
        self.current_stroke = [[], [], []] # x, y, time
        self.current_stroke_items = []
        self._add_point(event.x, event.y)
        
        # Cancel any pending recognition to save requests while drawing continuously
        if self._recognize_timer is not None:
            self.window.after_cancel(self._recognize_timer)
            self._recognize_timer = None
        
    def _draw_stroke(self, event):
        if self.current_stroke:
            x, y = event.x, event.y
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            
            # Clamp to canvas
            x = max(0, min(w, x))
            y = max(0, min(h, y))
            
            # Draw line on canvas
            if len(self.current_stroke[0]) > 0:
                last_x = self.current_stroke[0][-1]
                last_y = self.current_stroke[1][-1]
                item_id = self.canvas.create_line(last_x, last_y, x, y, 
                                                width=5, fill=self.colors['fg'], 
                                                capstyle=tk.ROUND, joinstyle=tk.ROUND)
                self.current_stroke_items.append(item_id)
            self._add_point(x, y)
            
    def _end_stroke(self, event):
        if self.current_stroke and len(self.current_stroke[0]) > 1:
            self.strokes.append(self.current_stroke)
            self.stroke_items.append(self.current_stroke_items)
        elif self.current_stroke_items:
            # Clean up single point clicks without movement
            for item in self.current_stroke_items:
                self.canvas.delete(item)
                
        self.current_stroke = None
        self.current_stroke_items = []
        
        # Debounce recognition
        if self._recognize_timer is not None:
            self.window.after_cancel(self._recognize_timer)
        self._recognize_timer = self.window.after(500, self._recognize)
        
    def _add_point(self, x, y):
        self.current_stroke[0].append(x)
        self.current_stroke[1].append(y)
        timestamp = int(time.time() * 1000)
        self.current_stroke[2].append(timestamp)
        
    def clear(self):
        self.canvas.delete("all")
        self._draw_grid()
        self.strokes = []
        self.stroke_items = []
        self._update_predictions([])
        self.status_var.set("Đã xóa")
        
        if self._recognize_timer is not None:
            self.window.after_cancel(self._recognize_timer)
            self._recognize_timer = None
        
    def undo(self):
        if self.strokes and self.stroke_items:
            # Delete canvas items for the last stroke
            items_to_delete = self.stroke_items.pop()
            for item in items_to_delete:
                self.canvas.delete(item)
                
            self.strokes.pop()
            
            if self._recognize_timer is not None:
                self.window.after_cancel(self._recognize_timer)
            self._recognize_timer = self.window.after(300, self._recognize)
            
    def _recognize(self):
        self._recognize_timer = None
        
        if not self.strokes:
            self._update_predictions([])
            return
            
        self.status_var.set("Đang nhận dạng...")
        
        # Capture current strokes and canvas size for the thread
        strokes_data = list(self.strokes)
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        def worker():
            try:
                url = "https://inputtools.google.com/request?ime=handwriting&app=mobilesearch&cs=1&oe=UTF-8"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "options": "enable_pre_space",
                    "requests": [{
                        "writing_guide": {"width": cw if cw > 0 else 400, "height": ch if ch > 0 else 400},
                        "ink": strokes_data,
                        "language": "zh-CN"
                    }]
                }

                resp = requests.post(url, headers=headers, json=payload, timeout=5)
                resp.raise_for_status()  # Raise exception for HTTP errors
                data = resp.json()

                if data[0] == "SUCCESS":
                    predictions = data[1][0][1]
                    # Update UI in main thread
                    if self.window.winfo_exists():
                        self.window.after(0, self._update_predictions, predictions)
                        self.window.after(0, self.status_var.set, "Đã nhận dạng")
                else:
                    logger.warning(f"Handwriting recognition failed: {data}")
                    if self.window.winfo_exists():
                        self.window.after(0, self.status_var.set, "Lỗi từ API")
            except requests.exceptions.Timeout:
                logger.warning("Handwriting recognition timeout")
                if self.window.winfo_exists():
                    self.window.after(0, self.status_var.set, "Timeout")
            except requests.exceptions.RequestException as e:
                logger.error(f"Handwriting recognition error: {e}")
                if self.window.winfo_exists():
                    self.window.after(0, self.status_var.set, "Lỗi kết nối")
            except Exception as e:
                logger.exception(f"Unexpected error in handwriting recognition: {e}")
                if self.window.winfo_exists():
                    self.window.after(0, self.status_var.set, "Lỗi")
                
        threading.Thread(target=worker, daemon=True).start()
        
    def _update_predictions(self, predictions):
        if not self.window.winfo_exists():
            return
            
        self.current_predictions = predictions
        
        # Create buttons dynamically if needed
        while len(self.pred_buttons) < len(predictions):
            idx = len(self.pred_buttons)
            btn = tk.Button(self.pred_inner, font=('Microsoft YaHei', 16),
                           width=3, height=1, bg=self.colors['surface'], fg=self.colors['accent'],
                           relief='flat', cursor='hand2')
            btn.config(command=lambda i=idx: self._select_prediction(i))
            btn.bind('<Enter>', lambda e, b=btn: self._on_enter(b))
            btn.bind('<Leave>', lambda e, b=btn: self._on_leave(b))
            self.pred_buttons.append(btn)
            
        # Update text and visibility
        for i, btn in enumerate(self.pred_buttons):
            if i < len(predictions):
                btn.config(text=predictions[i], state='normal', 
                          bg=self.colors['surface'], fg=self.colors['accent'])
                from tkinter import Pack
                if not btn.winfo_manager():
                    btn.pack(side='left', padx=3)
            else:
                if btn.winfo_manager():
                    btn.pack_forget()
                    
        # Update scroll region
        self.pred_canvas.update_idletasks()
        self.pred_canvas.configure(scrollregion=self.pred_canvas.bbox("all"))
                
    def _select_prediction(self, idx):
        if hasattr(self, 'current_predictions') and idx < len(self.current_predictions):
            char = self.current_predictions[idx]
            if self.on_char_selected:
                self.on_char_selected(char)
            # Flash clear
            self.clear()
            self.status_var.set(f"Đã thêm '{char}'")
