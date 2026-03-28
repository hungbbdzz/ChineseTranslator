# -*- coding: utf-8 -*-
import compat_patch
compat_patch.apply_patch()

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='zhconv')
warnings.filterwarnings("ignore", category=DeprecationWarning) 

"""
Chinese to Vietnamese Translator (Hybrid: Offline + Online)
Main GUI Application with hotkey Alt+X for screen capture OCR

Features:
- Manual input Chinese text
- Alt+X hotkey to capture screen and OCR
- Hybrid mode: Show offline result first (fast), then update with online (accurate)
- Display 5 rows: Hán tự, Hán Việt, Pinyin, English, Tiếng Việt
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import ctypes

# Local modules
from translator import translate_all, get_pinyin, get_hanviet, preload_resources, detect_input_language, translate_to_chinese
from ocr_capture import capture_and_ocr, capture_frozen_and_ocr
from handwriting import HandwritingWindow
from i18n import t, set_language, get_language

# Pre-load heavy resources in background immediately
preload_resources()

# DPI Awareness for crisp text
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass




class ChineseTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(t('app_title'))
        self.root.geometry("650x700")
        self.root.minsize(650, 600)
        self.root.configure(bg='#1e1e2e')
        
        # Config
        self.config_file = "config.json"
        self.config = {
            "topmost": True,
            "show_chinese": True,
            "show_hanviet": True,
            "show_pinyin": True,
            "show_english": True,
            "show_vietnamese": True,
            "clipboard_monitor": False,
            "quick_translate": True,
            "translation_mode": "offline",  # "offline" (HF) or "online" (Google)
            "app_language": "vi"             # UI language: "vi" | "en"
        }
        self.load_config()
        
        # Apply language from config immediately
        set_language(self.config.get('app_language', 'vi'))
        
        # Translation History
        self.history = []           # List of translation records
        self.history_index = -1     # Current position in history (-1 = new/unsaved)
        self.history_file = "translation_history.json"
        self.max_history = 1000     # Maximum items to keep
        self._is_navigating = False # Flag to prevent saving during navigation
        self.load_history()
        
        # Modern dark theme colors
        self.colors = {
            'bg': '#1e1e2e',
            'fg': '#cdd6f4',
            'accent': '#89b4fa',
            'accent2': '#f5c2e7',
            'surface': '#313244',
            'surface2': '#45475a',
            'green': '#a6e3a1',
            'yellow': '#f9e2af',
            'red': '#f38ba8',
        }
        
        # Topmost state (bound to config)
        self.always_on_top = tk.BooleanVar(value=self.config['topmost'])
        self._apply_topmost_state()
        
        # Clipboard Monitor Variables (must be before _build_ui)
        self.clipboard_monitor_var = tk.BooleanVar(value=self.config.get('clipboard_monitor', False))
        self.quick_translate_var = tk.BooleanVar(value=self.config.get('quick_translate', True))
        self.translation_mode_var = tk.StringVar(value=self.config.get('translation_mode', 'offline'))
        self._last_clipboard = ""
        
        self._setup_styles()
        self._build_ui()
        self._setup_hotkey()
        self._setup_tray()
        
        # Override close button to minimize to tray
        self.root.protocol("WM_DELETE_WINDOW", self._hide_window)
        
        # Bind focus events for Smart Pin (Auto Lower when not pinned)
        self.root.bind('<FocusIn>', self._on_focus_in)
        self.root.bind('<FocusOut>', self._on_focus_out)
        
        # Start clipboard monitor
        self._start_clipboard_monitor()
    
    def _start_clipboard_monitor(self):
        """Start clipboard monitoring loop"""
        def check_clipboard():
            try:
                if self.clipboard_monitor_var.get():
                    current = self.root.clipboard_get()
                    if current != self._last_clipboard and current.strip():
                        # Check if contains Asian text
                        if self._contains_asian_text(current):
                            self._last_clipboard = current
                            self.input_text.delete('1.0', 'end')
                            self.input_text.insert('1.0', current)
                            self._check_empty_state()
                            self._on_translate()
                            self._show_window()
            except:
                pass
            self.root.after(500, check_clipboard)
        self.root.after(1000, check_clipboard)
    
    def _contains_asian_text(self, text):
        """Check if text contains Chinese/Korean/Japanese characters"""
        for char in text:
            if ('\u4e00' <= char <= '\u9fff' or  # Chinese
                '\uac00' <= char <= '\ud7af' or  # Korean
                '\u3040' <= char <= '\u30ff'):   # Japanese
                return True
        return False
    
    def _toggle_clipboard_monitor(self):
        """Toggle clipboard monitor"""
        self.config['clipboard_monitor'] = self.clipboard_monitor_var.get()
        self.save_config()
        status = "\u2705" if self.clipboard_monitor_var.get() else "\u274c"
        self._set_status(t('clipboard_status').format(status), 'accent')
    
    def _toggle_quick_translate(self):
        """Toggle quick translate hotkey"""
        self.config['quick_translate'] = self.quick_translate_var.get()
        self.save_config()
        status = "\u2705" if self.quick_translate_var.get() else "\u274c"
        self._set_status(t('quick_translate_status').format(status), 'accent')

    def _update_mode_button_text(self):
        """Update mode button text based on current mode"""
        if hasattr(self, 'mode_btn'):
            mode = self.translation_mode_var.get()
            self.mode_btn.config(text=t('mode_offline') if mode == 'offline' else t('mode_online'))

    def _toggle_translation_mode(self):
        """Toggle between offline (HF) and online (Google) translation"""
        current = self.translation_mode_var.get()
        new_mode = 'online' if current == 'offline' else 'offline'
        self.translation_mode_var.set(new_mode)
        self.config['translation_mode'] = new_mode
        self.save_config()
        self._update_mode_button_text()
        
        mode_label = t('mode_offline') if new_mode == 'offline' else t('mode_online')
        self._set_status(f"📡 {mode_label}", 'accent')
        self._show_toast_notification(t('toast_mode_switched').format(new_mode.upper()), 'green')
        
        # Re-translate current input with the new mode
        text = self.input_text.get('1.0', 'end').strip() if hasattr(self, 'input_text') else ''
        if text:
            self.root.after(200, self._on_translate)

    def load_config(self):
        import json
        import os
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_config(self):
        import json
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load_history(self):
        """Load translation history from JSON file"""
        import json
        import os
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                    # Limit to max_history items
                    if len(self.history) > self.max_history:
                        self.history = self.history[-self.max_history:]
                print(f"Loaded {len(self.history)} history items")
            except Exception as e:
                print(f"Error loading history: {e}")
                self.history = []
        self.history_index = len(self.history)  # Point past the end (new entry position)

    def save_history(self):
        """Save translation history to JSON file"""
        import json
        try:
            # Keep only last max_history items
            to_save = self.history[-self.max_history:] if len(self.history) > self.max_history else self.history
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_to_history(self, entry: dict):
        """Add a new translation entry to history"""
        # Don't add empty entries or during navigation
        if not entry.get('input') or self._is_navigating:
            return
        
        # Check if same as last entry to avoid duplicates
        if self.history and self.history[-1].get('input') == entry.get('input'):
            # Update existing entry with new results
            self.history[-1] = entry
            self.save_history()
            return
        
        # Add new entry
        self.history.append(entry)
        self.history_index = len(self.history)  # Point past end
        self.save_history()
        self._update_nav_buttons()

    def navigate_history(self, direction: int):
        """Navigate through translation history
        direction: -1 for back, +1 for forward
        """
        if not self.history:
            return
        
        new_index = self.history_index + direction
        
        # Clamp to valid range
        if new_index < 0:
            new_index = 0
        elif new_index >= len(self.history):
            new_index = len(self.history) - 1
        
        if new_index == self.history_index:
            return  # No change
        
        self.history_index = new_index
        entry = self.history[self.history_index]
        
        # Set flag to prevent re-saving this entry
        self._is_navigating = True
        
        # Restore input text
        self.input_text.delete('1.0', 'end')
        self.input_text.insert('1.0', entry.get('input', ''))
        self._check_empty_state()
        
        # Restore results
        results = {
            'chinese': entry.get('chinese', ''),
            'hanviet': entry.get('hanviet', ''),
            'pinyin': entry.get('pinyin', ''),
            'english': entry.get('english', ''),
            'vietnamese': entry.get('vietnamese', ''),
        }
        self._show_results(results, is_online=False)
        
        # Update status and buttons
        self._set_status(t('history_status', cur=self.history_index + 1, total=len(self.history)), 'accent')
        self._update_nav_buttons()
        
        # Reset flag after a short delay
        self.root.after(500, self._reset_nav_flag)

    def _reset_nav_flag(self):
        """Reset navigation flag"""
        self._is_navigating = False

    def _update_nav_buttons(self):
        """Update navigation button states"""
        if not hasattr(self, 'back_btn'):
            return
        
        # Back button: disabled if at start or no history
        if not self.history or self.history_index <= 0:
            self.back_btn.config(state='disabled')
        else:
            self.back_btn.config(state='normal')
        
        # Forward button: disabled if at end or no history
        if not self.history or self.history_index >= len(self.history) - 1:
            self.forward_btn.config(state='disabled')
        else:
            self.forward_btn.config(state='normal')

    def _open_history_list(self):
        """Open popup showing all translation history with dates"""
        if hasattr(self, 'history_dialog') and self.history_dialog and self.history_dialog.winfo_exists():
            self.history_dialog.lift()
            self.history_dialog.focus_force()
            return
        
        self.history_dialog = tk.Toplevel(self.root)
        dialog = self.history_dialog
        dialog.title(t('history_title'))
        dialog.geometry("600x600")
        dialog.configure(bg=self.colors['bg'])
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)
        
        # Center dialog
        x = self.root.winfo_x() + 30
        y = self.root.winfo_y() + 30
        dialog.geometry(f"+{x}+{y}")
        
        # Variables
        check_vars = {}
        item_widgets = {}  # Store widgets for filtering
        search_var = tk.StringVar()
        show_favorites_only = tk.BooleanVar(value=False)
        
        # === Header ===
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        header = ttk.Label(header_frame, text=t('history_header', count=len(self.history)),
                          font=('Segoe UI', 12, 'bold'))
        header.pack(side='left')
        
        # === Search Box ===
        search_frame = ttk.Frame(dialog)
        search_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(search_frame, text="🔍").pack(side='left')
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        # Favorites filter toggle
        fav_check = ttk.Checkbutton(search_frame, text=t('history_fav_filter'), variable=show_favorites_only)
        fav_check.pack(side='left', padx=5)
        
        # === Action Buttons ===
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        def toggle_favorite(idx):
            """Toggle favorite status for an entry"""
            if 0 <= idx < len(self.history):
                current = self.history[idx].get('favorite', False)
                self.history[idx]['favorite'] = not current
                self.save_history()
                # Update button text
                if idx in item_widgets:
                    new_text = "★" if self.history[idx]['favorite'] else "☆"
                    item_widgets[idx]['fav_btn'].config(text=new_text)
        
        def delete_selected():
            """Delete all selected entries"""
            to_delete = [idx for idx, var in check_vars.items() if var.get()]
            if not to_delete:
                return
            if not messagebox.askyesno(t('confirm_title'), t('confirm_delete_n', n=len(to_delete))):
                return
            for idx in sorted(to_delete, reverse=True):
                if 0 <= idx < len(self.history):
                    del self.history[idx]
            self.history_index = len(self.history)
            self.save_history()
            self._update_nav_buttons()
            dialog.destroy()
            self._open_history_list()
        
        def delete_all():
            """Delete all history"""
            if not self.history:
                return
            if not messagebox.askyesno(t('confirm_title'), t('confirm_delete_all', n=len(self.history))):
                return
            self.history = []
            self.history_index = 0
            self.save_history()
            self._update_nav_buttons()
            dialog.destroy()
            self._set_status(t('delete_all_done'), 'green')
        
        def select_all():
            """Toggle select all visible items"""
            visible_vars = [v for idx, v in check_vars.items() 
                           if idx in item_widgets and item_widgets[idx]['frame'].winfo_viewable()]
            if visible_vars:
                all_selected = all(v.get() for v in visible_vars)
                for v in visible_vars:
                    v.set(not all_selected)
        
        def export_history():
            """Export history to JSON file"""
            from tkinter import filedialog
            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
                title="Xuất lịch sử"
            )
            if path:
                import json
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.history, f, ensure_ascii=False, indent=2)
                self._set_status(t('export_done', n=len(self.history)), 'green')
        
        def import_history():
            """Import history from JSON file"""
            from tkinter import filedialog
            path = filedialog.askopenfilename(
                filetypes=[("JSON", "*.json")],
                title="Nhập lịch sử"
            )
            if path:
                import json
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        imported = json.load(f)
                    if isinstance(imported, list):
                        # Merge with existing (avoid duplicates by input)
                        existing_inputs = {e.get('input') for e in self.history}
                        new_count = 0
                        for entry in imported:
                            if entry.get('input') not in existing_inputs:
                                self.history.append(entry)
                                new_count += 1
                        self.save_history()
                        self._set_status(t('import_done', n=new_count), 'green')
                        dialog.destroy()
                        self._open_history_list()
                except Exception as e:
                    messagebox.showerror(t('confirm_title'), t('confirm_import_err', e=e))
        
        # Buttons row 1
        ttk.Button(btn_frame, text=t('history_select_all'), command=select_all).pack(side='left', padx=2)
        ttk.Button(btn_frame, text=t('history_delete_sel'), command=delete_selected).pack(side='left', padx=2)
        ttk.Button(btn_frame, text=t('history_delete_all'), command=delete_all).pack(side='left', padx=2)
        ttk.Separator(btn_frame, orient='vertical').pack(side='left', fill='y', padx=5)
        ttk.Button(btn_frame, text=t('history_export'), command=export_history).pack(side='left', padx=2)
        ttk.Button(btn_frame, text=t('history_import'), command=import_history).pack(side='left', padx=2)
        
        # === Scrollable List ===
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(list_frame, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scrollable, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        
        def on_canvas_resize(event):
            canvas.itemconfig(canvas.find_withtag('all')[0], width=event.width)
        canvas.bind('<Configure>', on_canvas_resize)
        
        def on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            except:
                pass
        dialog.bind('<MouseWheel>', on_mousewheel)
        canvas.bind('<MouseWheel>', on_mousewheel)
        
        def filter_list(*args):
            """Filter history list based on search and favorites"""
            query = search_var.get().lower()
            fav_only = show_favorites_only.get()
            
            for idx, widgets in item_widgets.items():
                entry = self.history[idx]
                input_text = entry.get('input', '').lower()
                is_fav = entry.get('favorite', False)
                
                # Check visibility
                matches_search = not query or query in input_text
                matches_fav = not fav_only or is_fav
                
                if matches_search and matches_fav:
                    widgets['frame'].pack(fill='x', pady=2, padx=5)
                else:
                    widgets['frame'].pack_forget()
        
        search_var.trace('w', filter_list)
        show_favorites_only.trace('w', filter_list)
        
        def select_entry(idx):
            """Load a specific history entry"""
            self.history_index = idx
            entry = self.history[idx]
            
            self._is_navigating = True
            self.input_text.delete('1.0', 'end')
            self.input_text.insert('1.0', entry.get('input', ''))
            self._check_empty_state()
            
            results = {
                'chinese': entry.get('chinese', ''),
                'hanviet': entry.get('hanviet', ''),
                'pinyin': entry.get('pinyin', ''),
                'english': entry.get('english', ''),
                'vietnamese': entry.get('vietnamese', ''),
            }
            self._show_results(results, is_online=False)
            self._set_status(t('history_status', cur=idx + 1, total=len(self.history)), 'accent')
            self._update_nav_buttons()
            self.root.after(500, self._reset_nav_flag)
            dialog.destroy()
        
        # === Populate List ===
        from datetime import datetime
        for i, entry in enumerate(reversed(self.history)):
            real_idx = len(self.history) - 1 - i
            
            item_frame = ttk.Frame(scrollable)
            item_frame.pack(fill='x', pady=2, padx=5)
            
            # Checkbox
            var = tk.BooleanVar(value=False)
            check_vars[real_idx] = var
            cb = ttk.Checkbutton(item_frame, variable=var)
            cb.pack(side='left')
            
            # Favorite button
            is_fav = entry.get('favorite', False)
            fav_btn = tk.Button(item_frame, text="★" if is_fav else "☆",
                               font=('Segoe UI', 12),
                               fg=self.colors['yellow'] if is_fav else self.colors['fg'],
                               bg=self.colors['surface'],
                               relief='flat', cursor='hand2',
                               command=lambda idx=real_idx: toggle_favorite(idx))
            fav_btn.pack(side='left', padx=2)
            
            # Parse timestamp
            ts = entry.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(ts)
                date_str = dt.strftime('%d/%m %H:%M')
            except:
                date_str = 'N/A'
            
            # Preview text
            input_text = entry.get('input', '')[:30]
            if len(entry.get('input', '')) > 30:
                input_text += '...'
            
            # Clickable row
            btn = tk.Button(item_frame, 
                           text=f"📅 {date_str}  |  {input_text}",
                           font=('Segoe UI', 10),
                           bg=self.colors['surface'],
                           fg=self.colors['fg'],
                           activebackground=self.colors['surface2'],
                           activeforeground=self.colors['accent'],
                           relief='flat', anchor='w', cursor='hand2',
                           command=lambda idx=real_idx: select_entry(idx))
            btn.pack(side='left', fill='x', expand=True)
            
            # Store widgets for filtering
            item_widgets[real_idx] = {
                'frame': item_frame,
                'fav_btn': fav_btn,
            }
        
        # No history message
        if not self.history:
            ttk.Label(scrollable, text=t('history_empty'),
                     font=('Segoe UI', 11)).pack(pady=20)
        
        # Close button
        ttk.Button(dialog, text=t('history_close'), command=dialog.destroy,
                  style='Accent.TButton').pack(pady=10)

    def _apply_topmost_state(self):
        """Apply topmost state based on variable"""
        is_pinned = self.always_on_top.get()
        self.root.attributes('-topmost', is_pinned)
        self.config['topmost'] = is_pinned
        self.save_config()

    def _show_mini_dict(self, event):
        """Show enhanced mini dictionary popup for Chinese character"""
        widget = event.widget
        try:
            # Get selected text or character at cursor
            try:
                selected = widget.get('sel.first', 'sel.last')
            except:
                # Get character at click position
                index = widget.index(f"@{event.x},{event.y}")
                selected = widget.get(index, f"{index}+1c")
            
            if not selected or not selected.strip():
                return
            
            # Only process single character for detailed view
            char = selected.strip()[0] if selected.strip() else ''
            if not char or not self._contains_asian_text(char):
                return
            
            # Get translations
            from translator import get_pinyin, get_hanviet
            
            pinyin = get_pinyin(char)
            hanviet = get_hanviet(char)
            
            # Get data from dictionary database
            from dict_data import get_stroke_count, get_radical_info, get_common_words, get_example_sentences
            
            stroke_count = get_stroke_count(char)
            radical_data = get_radical_info(char)
            radical_info = f"{radical_data[0]} ({radical_data[1]}) - {radical_data[2]}" if radical_data else None
            common_words = get_common_words(char)
            example_sentences = get_example_sentences(char)
            
            # Create popup
            popup = tk.Toplevel(self.root)
            popup.title(t('dict_title', char=char))
            popup.geometry("450x550")
            popup.configure(bg=self.colors['bg'])
            popup.attributes('-topmost', True)
            popup.resizable(True, True)
            
            # Position near cursor but ensure visible
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = min(self.root.winfo_pointerx() + 20, screen_w - 470)
            y = min(self.root.winfo_pointery() + 20, screen_h - 570)
            popup.geometry(f"+{x}+{y}")
            
            # Scrollable content
            canvas = tk.Canvas(popup, bg=self.colors['bg'], highlightthickness=0)
            scrollbar = ttk.Scrollbar(popup, orient='vertical', command=canvas.yview)
            content = ttk.Frame(canvas)
            
            content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.create_window((0, 0), window=content, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side='right', fill='y')
            canvas.pack(side='left', fill='both', expand=True)
            
            def on_mousewheel(e):
                canvas.yview_scroll(int(-1 * (e.delta / 120)), 'units')
                return 'break'  # Stop event propagation to main window
            
            # Bind to popup and all its children
            popup.bind('<MouseWheel>', on_mousewheel)
            canvas.bind('<MouseWheel>', on_mousewheel)
            content.bind('<MouseWheel>', on_mousewheel)
            
            # Bind to all future children
            def bind_mousewheel(widget):
                widget.bind('<MouseWheel>', on_mousewheel)
                for child in widget.winfo_children():
                    bind_mousewheel(child)
            
            popup.after(100, lambda: bind_mousewheel(content))
            
            # === Character Header ===
            header_frame = ttk.Frame(content)
            header_frame.pack(fill='x', pady=10, padx=15)
            
            ttk.Label(header_frame, text=char, 
                     font=('Microsoft YaHei', 48, 'bold'),
                     foreground=self.colors['accent2']).pack(side='left')
            
            info_frame = ttk.Frame(header_frame)
            info_frame.pack(side='left', padx=20)
            
            ttk.Label(info_frame, text=t('dict_pinyin', pinyin=pinyin),
                     font=('Segoe UI', 12, 'bold')).pack(anchor='w')
            ttk.Label(info_frame, text=t('dict_hanviet', hanviet=hanviet),
                     font=('Segoe UI', 12, 'bold'),
                     foreground=self.colors['green']).pack(anchor='w')
            
            # === Radical Info (if available) ===
            if radical_info:
                ttk.Separator(content, orient='horizontal').pack(fill='x', padx=15, pady=5)
                ttk.Label(content, text=t('dict_radical', radical=radical_info),
                         font=('Segoe UI', 11)).pack(anchor='w', padx=15)
            
            # === Common Words (CLICKABLE) ===
            if common_words:
                ttk.Separator(content, orient='horizontal').pack(fill='x', padx=15, pady=5)
                
                ttk.Label(content, text=t('dict_words'),
                         font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=15, pady=(5, 3))
                
                words_frame = ttk.Frame(content)
                words_frame.pack(fill='x', padx=15)
                
                def copy_and_translate(word_text):
                    """Copy word to input and translate"""
                    popup.destroy()
                    self.input_text.delete('1.0', 'end')
                    self.input_text.insert('1.0', word_text)
                    self._check_empty_state()
                    self._on_translate()
                
                for word, word_pinyin, word_meaning in common_words[:8]:
                    word_btn = tk.Button(words_frame, 
                                        text=f"• {word}",
                                        font=('Microsoft YaHei', 11),
                                        fg=self.colors['accent'],
                                        bg=self.colors['surface'],
                                        relief='flat',
                                        cursor='hand2',
                                        command=lambda w=word: copy_and_translate(w))
                    word_btn.pack(anchor='w', pady=1)
                    
                    # Hover effect
                    word_btn.bind('<Enter>', lambda e, b=word_btn: b.configure(bg=self.colors['surface2']))
                    word_btn.bind('<Leave>', lambda e, b=word_btn: b.configure(bg=self.colors['surface']))
            
            # === Example Sentences ===
            if example_sentences:
                ttk.Separator(content, orient='horizontal').pack(fill='x', padx=15, pady=5)
                
                ttk.Label(content, text=t('dict_examples'),
                         font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=15, pady=(5, 3))
                
                for cn, vn in example_sentences[:3]:
                    sent_frame = ttk.Frame(content)
                    sent_frame.pack(fill='x', padx=15, pady=3)
                    
                    # Clickable sentence
                    sent_btn = tk.Button(sent_frame, 
                                        text=f"🀄 {cn}",
                                        font=('Microsoft YaHei', 10),
                                        fg=self.colors['accent2'],
                                        bg=self.colors['surface'],
                                        relief='flat',
                                        cursor='hand2',
                                        anchor='w',
                                        command=lambda s=cn: copy_and_translate(s))
                    sent_btn.pack(anchor='w', fill='x')
                    sent_btn.bind('<Enter>', lambda e, b=sent_btn: b.configure(bg=self.colors['surface2']))
                    sent_btn.bind('<Leave>', lambda e, b=sent_btn: b.configure(bg=self.colors['surface']))
                    
                    ttk.Label(sent_frame, text=f"📝 {vn}",
                             font=('Segoe UI', 10),
                             foreground=self.colors['fg']).pack(anchor='w')
            
            # === Close Button ===
            ttk.Button(content, text=t('dict_close'), command=popup.destroy,
                      style='Accent.TButton').pack(pady=15)
            
            # === Event Handling ===
            # Close on Escape
            popup.bind('<Escape>', lambda e: popup.destroy())
            
            # Make transient (will close with parent interactions)
            popup.transient(self.root)
            popup.focus_set()
            
            # Close when clicking anywhere outside popup
            def check_click_outside(e):
                # Get popup geometry
                try:
                    px, py = popup.winfo_rootx(), popup.winfo_rooty()
                    pw, ph = popup.winfo_width(), popup.winfo_height()
                    
                    # Check if click is outside popup bounds
                    if not (px <= e.x_root <= px + pw and py <= e.y_root <= py + ph):
                        popup.destroy()
                except:
                    pass
            
            # Bind to root window for outside clicks
            self.root.bind('<Button-1>', check_click_outside, add='+')
            
            # Remove binding when popup destroyed
            def on_destroy(e):
                try:
                    self.root.unbind('<Button-1>')
                except:
                    pass
            popup.bind('<Destroy>', on_destroy)
            
        except Exception as e:
            print(f"Mini dict error: {e}")
            import traceback
            traceback.print_exc()
    
    # Dictionary methods now in dict_data.py

    def _on_focus_in(self, event):
        # If NOT pinned, raise to top on focus (Smart Mode)
        if not self.always_on_top.get():
            self.root.attributes('-topmost', True)

    def _on_focus_out(self, event):
        # If NOT pinned, lower on blur (Smart Mode)
        if not self.always_on_top.get():
            self.root.attributes('-topmost', False)
            
    def _open_settings(self):
        """Open settings dialog"""
        if hasattr(self, 'settings_dialog') and self.settings_dialog and self.settings_dialog.winfo_exists():
            self.settings_dialog.lift()
            self.settings_dialog.focus_force()
            return

        self.settings_dialog = tk.Toplevel(self.root)
        dialog = self.settings_dialog
        dialog.title(t('settings_title'))
        dialog.geometry("350x550")
        dialog.configure(bg=self.colors['bg'])
        dialog.attributes('-topmost', True)
        dialog.transient(self.root)

        x = self.root.winfo_x() + 50
        y = self.root.winfo_y() + 50
        dialog.geometry(f"+{x}+{y}")
        
        # === Language Selection ===
        ttk.Label(dialog, text=t('settings_lang_label'),
                  font=('Segoe UI', 11, 'bold')).pack(pady=(15, 5))
        
        lang_var = tk.StringVar(value=self.config.get('app_language', 'vi'))
        
        lang_frame = ttk.Frame(dialog)
        lang_frame.pack(anchor='w', padx=40, pady=2)
        
        def on_lang_change():
            new_lang = lang_var.get()
            self.config['app_language'] = new_lang
            self.save_config()
            set_language(new_lang)
            self._apply_language()
            self._show_toast_notification(t('toast_lang_changed'), 'green')
            # Đóng và mở lại dialog để toàn bộ nhãn được refresh theo ngôn ngữ mới
            dialog.destroy()
            self.root.after(50, self._open_settings)
        
        ttk.Radiobutton(lang_frame, text='Tiếng Việt', variable=lang_var,
                        value='vi', command=on_lang_change).pack(side='left', padx=(0, 15))
        ttk.Radiobutton(lang_frame, text='English', variable=lang_var,
                        value='en', command=on_lang_change).pack(side='left')

        ttk.Separator(dialog, orient='horizontal').pack(fill='x', padx=20, pady=10)

        # === Script Selection ===
        ttk.Label(dialog, text=t('settings_script_label'),
                  font=('Segoe UI', 11, 'bold')).pack(pady=(5, 5))
        
        script_var = tk.StringVar(value=self.config.get('chinese_script', 'simplified'))
        
        def on_script_change():
            self.config['chinese_script'] = script_var.get()
            self.save_config()
            
        ttk.Radiobutton(dialog, text=t('settings_simplified'), variable=script_var,
                        value='simplified', command=on_script_change).pack(anchor='w', padx=40, pady=2)
        ttk.Radiobutton(dialog, text=t('settings_traditional'), variable=script_var,
                        value='traditional', command=on_script_change).pack(anchor='w', padx=40, pady=2)

        ttk.Separator(dialog, orient='horizontal').pack(fill='x', padx=20, pady=10)

        # === Visibility Selection ===
        ttk.Label(dialog, text=t('settings_rows_label'),
                  font=('Segoe UI', 11, 'bold')).pack(pady=5)
        
        settings_map = [
            (t('vis_chinese'),    'show_chinese'),
            (t('vis_hanviet'),    'show_hanviet'),
            (t('vis_pinyin'),     'show_pinyin'),
            (t('vis_english'),    'show_english'),
            (t('vis_vietnamese'), 'show_vietnamese'),
        ]
        
        vars_map = {}
        for label, key in settings_map:
            var = tk.BooleanVar(value=self.config.get(key, True))
            vars_map[key] = var
            ttk.Checkbutton(dialog, text=label, variable=var).pack(anchor='w', padx=40, pady=5)
            
        def save_and_close():
            changed = False
            for key, var in vars_map.items():
                if self.config.get(key) != var.get():
                    self.config[key] = var.get()
                    changed = True
            if changed:
                self.save_config()
                self._update_result_layout()
                text = self.input_text.get('1.0', 'end').strip()
                if text:
                    self.root.after(100, self._on_translate)
            dialog.destroy()
            
        ttk.Button(dialog, text=t('btn_close'), command=save_and_close,
                   style='Accent.TButton').pack(pady=15)

    def _update_result_layout(self):
        """Rebuild result widgets based on config and current language"""
        for widget in self.scrollable_content.winfo_children():
            widget.destroy()
        
        self.result_widgets = {}
        
        full_configs = [
            ('chinese',    t('row_chinese'),    self.colors['accent2'], 16),
            ('hanviet',    t('row_hanviet'),    self.colors['green'],   13),
            ('pinyin',     t('row_pinyin'),     self.colors['yellow'],  13),
            ('english',    t('row_english'),    self.colors['accent'],  13),
            ('vietnamese', t('row_vietnamese'), self.colors['fg'],      13),
        ]
        
        for key, label, color, font_size in full_configs:
            config_key = f"show_{key}"
            if not self.config.get(config_key, True):
                continue
            
            row_frame = ttk.Frame(self.scrollable_content)
            row_frame.pack(fill='x', pady=5, padx=5)
            
            btn_container = ttk.Frame(row_frame)
            btn_container.pack(side='right', padx=(5, 0), fill='y')
            
            copy_btn = ttk.Button(btn_container, text="📋", width=3,
                                 command=lambda k=key: self._copy_result(k))
            copy_btn.pack(side='top', pady=0)
            
            lbl = ttk.Label(row_frame, text=label, width=12, font=('Segoe UI', 10))
            lbl.pack(side='left', anchor='n', pady=5)
            
            result_box = tk.Text(row_frame, height=1, font=('Segoe UI', font_size),
                                bg=self.colors['surface'], fg=color,
                                relief='flat', padx=8, pady=5, wrap='word')
            result_box.pack(side='left', fill='both', expand=True)
            result_box.config(state='disabled')
            
            if key in ['chinese', 'hanviet']:
                result_box.bind('<Double-Button-1>', self._show_mini_dict)
            
            self.result_widgets[key] = result_box

    def _on_translate(self, event=None):
        text = self.input_text.get('1.0', 'end').strip()
        if not text:
            if hasattr(self, 'status_label'):
                self.status_label.config(text=t('status_empty'), foreground=self.colors['yellow'])
            return 'break'

        if hasattr(self, 'status_label'):
            self.status_label.config(text=t('status_translating'), foreground=self.colors['accent'])
        self.root.update()

        # Run translation in thread based on selected mode
        def do_translate():
            try:
                mode = self.translation_mode_var.get()
                lang = detect_input_language(text)

                # ── CHẾ ĐỘ DỊCH NGƯỢC: input không phải tiếng Trung → dịch sang Hán Tự ──
                if lang != 'chinese':
                    self.root.after(0, lambda: self._set_status(t('status_reverse_start'), 'accent'))
                    reverse = translate_to_chinese(text)
                    chinese_out = reverse.get('chinese', '')
                    english_out = reverse.get('english', '')

                    if not chinese_out:
                        self.root.after(0, lambda: self._set_status(t('status_no_internet'), 'yellow'))
                        if english_out:
                            partial = {'chinese': '', 'hanviet': '', 'pinyin': '', 'english': english_out, 'vietnamese': ''}
                            self.root.after(0, lambda p=partial: self._show_results(p, is_online=False))
                        return

                    # Lấy Pinyin + Hán Việt từ Hán tự kết quả
                    pinyin_out  = get_pinyin(chinese_out)
                    hanviet_out = get_hanviet(chinese_out)

                    # Hiển thị partial ngay (Hán Tự, Hán Việt, Pinyin, English)
                    partial_results = {
                        'chinese':    chinese_out,
                        'hanviet':    hanviet_out,
                        'pinyin':     pinyin_out,
                        'english':    english_out,
                        'vietnamese': t('status_translating'),
                    }
                    self.root.after(0, lambda r=partial_results: self._show_results(r, is_online=False))

                    # Dịch Hán Tự → Tiếng Việt (dùng engine tương ứng với mode)
                    from translator import translate_online, get_translations, convert_script
                    target_script = self.config.get('chinese_script', 'simplified')
                    chinese_display = convert_script(chinese_out, target_script)

                    if mode == 'online':
                        vi_result = translate_online(chinese_out)
                        vietnamese_out = vi_result.get('vietnamese', '')
                    else:
                        vi_offline = get_translations(chinese_out)
                        vietnamese_out = vi_offline.get('vietnamese', '')

                    results = {
                        'chinese':    chinese_display,
                        'hanviet':    hanviet_out,
                        'pinyin':     pinyin_out,
                        'english':    english_out,
                        'vietnamese': vietnamese_out,
                    }

                    self.root.after(0, lambda r=results: self._show_results(r, is_online=False))
                    self.root.after(0, lambda: self._set_status(t('status_done_reverse'), 'green'))

                    from datetime import datetime
                    entry = {
                        "input":      text,
                        "chinese":    chinese_display,
                        "hanviet":    hanviet_out,
                        "pinyin":     pinyin_out,
                        "english":    english_out,
                        "vietnamese": vietnamese_out,
                        "timestamp":  datetime.now().isoformat()
                    }
                    self.root.after(0, lambda e=entry: self.add_to_history(e))
                    return

                # ── CHế ĐỘ THƯỜNG: input tiếng Trung ──
                if mode == 'offline':
                    # OFFLINE MODE: Use Hugging Face (direct zh→vi)
                    results = translate_all(text)
                    
                    # Input original text first
                    raw_original = results.pop('original')
                    
                    # Convert script
                    from translator import convert_script
                    target_script = self.config.get('chinese_script', 'simplified')
                    final_original = convert_script(raw_original, target_script)
                    
                    results['chinese'] = final_original
                    
                    self.root.after(0, lambda: self._show_results(results, is_online=False))
                    self.root.after(0, lambda: self._set_status(t('status_done_offline'), 'green'))
                    
                    # Save to history
                    from datetime import datetime
                    entry = {
                        "input": text,
                        "chinese": results.get('chinese', ''),
                        "hanviet": results.get('hanviet', ''),
                        "pinyin": results.get('pinyin', ''),
                        "english": results.get('english', ''),
                        "vietnamese": results.get('vietnamese', ''),
                        "timestamp": datetime.now().isoformat()
                    }
                    self.root.after(0, lambda e=entry: self.add_to_history(e))
                    
                else:
                    # ONLINE MODE: Use Google Translate directly
                    from translator import translate_online
                    online_results = translate_online(text)
                    
                    # Get basic info (pinyin, hanviet) from offline
                    hanviet = get_hanviet(text)
                    pinyin = get_pinyin(text)
                    
                    # Convert script
                    from translator import convert_script
                    target_script = self.config.get('chinese_script', 'simplified')
                    chinese_text = convert_script(text, target_script)
                    
                    results = {
                        'chinese': chinese_text,
                        'hanviet': hanviet,
                        'pinyin': pinyin,
                        'english': online_results.get('english', ''),
                        'vietnamese': online_results.get('vietnamese', '')
                    }
                    
                    # Truyền is_online=False để hiển thị ĐẦY ĐỦ tất cả dòng kết quả
                    self.root.after(0, lambda: self._show_results(results, is_online=False))
                    self.root.after(0, lambda: self._set_status(t('status_done_online'), 'green'))
                    
                    # Save to history
                    from datetime import datetime
                    entry = {
                        "input": text,
                        "chinese": results.get('chinese', ''),
                        "hanviet": results.get('hanviet', ''),
                        "pinyin": results.get('pinyin', ''),
                        "english": results.get('english', ''),
                        "vietnamese": results.get('vietnamese', ''),
                        "timestamp": datetime.now().isoformat()
                    }
                    self.root.after(0, lambda e=entry: self.add_to_history(e))

            except Exception as e:
                self.root.after(0, lambda: self._set_status(f"❌ Lỗi: {e}", 'red'))

        threading.Thread(target=do_translate, daemon=True).start()
        return 'break'
            


    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('.', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TButton', background=self.colors['surface'], foreground=self.colors['fg'],
                       padding=5, font=('Segoe UI', 9))  # Reduced padding
        style.map('TButton', background=[('active', self.colors['surface2'])])
        
        style.configure('Accent.TButton', background=self.colors['accent'], 
                       foreground='#1e1e2e', font=('Segoe UI', 9, 'bold'))
        style.map('Accent.TButton', background=[('active', '#7ba3e8')])
        
        style.configure('TLabelframe', background=self.colors['bg'], foreground=self.colors['accent'])
        style.configure('TLabelframe.Label', background=self.colors['bg'], 
                       foreground=self.colors['accent'], font=('Segoe UI', 11, 'bold'))
        
        # Checkbutton dark theme fix
        style.configure('TCheckbutton', background=self.colors['bg'], foreground=self.colors['fg'])
        style.map('TCheckbutton', 
                  background=[('active', self.colors['surface']), ('selected', self.colors['bg'])],
                  indicatorcolor=[('selected', self.colors['accent']), ('pressed', self.colors['accent'])])

        # Subtle Button for Paste
        style.configure('Subtle.TButton', background=self.colors['surface'], 
                       foreground='#9399b2', font=('Segoe UI', 10, 'italic'), borderwidth=0)
        style.map('Subtle.TButton', background=[('active', self.colors['surface'])], # No background change on hover
                                    foreground=[('active', '#cdd6f4')]) # Brighten text on hover

    def _force_paste_and_translate(self, event=None):
        try:
            # Only paste if input is effectively empty
            if self.input_text.get('1.0', 'end').strip():
                return
                
            content = self.root.clipboard_get()
            if content:
                self.input_text.delete('1.0', 'end')
                self.input_text.insert('1.0', content)
                self._check_empty_state() 
                self._on_translate()
        except:
            pass
        return 'break'

    def _on_key_release(self, event):
        # Ẩn/hiện nút dán ngay lập tức khi có thay đổi text
        self._check_empty_state()
        # Ignore modifier keys and navigation for auto-translate
        if getattr(event, 'keysym', '') in ['Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Up', 'Down', 'Left', 'Right', 'Return']:
            return
        self._schedule_auto_translate()

    def _schedule_auto_translate(self):
        if hasattr(self, '_auto_translate_id') and self._auto_translate_id is not None:
            self.root.after_cancel(self._auto_translate_id)
        self._auto_translate_id = self.root.after(2000, self._trigger_auto_translate)

    def _trigger_auto_translate(self):
        self._auto_translate_id = None
        text = self.input_text.get('1.0', 'end').strip()
        
        if text:
            try:
                from smart_suggestions import get_contextual_suggestions
                suggestions = get_contextual_suggestions(text)
                self._update_suggestions(suggestions)
            except Exception:
                self._update_suggestions([])
                
            if self.history and self.history[-1].get('input') == text:
                return
            self._on_translate()
        else:
            self._update_suggestions([])

    def _update_suggestions(self, suggestions):
        if not suggestions:
            if self.suggestions_frame.winfo_manager():
                self.suggestions_frame.pack_forget()
            return
            
        if not self.suggestions_frame.winfo_manager():
            self.suggestions_frame.pack(fill='x', pady=(0, 10), before=self.action_frame)
            
        for i, btn in enumerate(self.sugg_buttons):
            if i < len(suggestions):
                display_text, append_text = suggestions[i]
                btn.config(text=display_text, command=lambda a=append_text: self._insert_suggestion(a))
                if not btn.winfo_manager():
                    btn.pack(side='left', padx=3)
            else:
                if btn.winfo_manager():
                    btn.pack_forget()
                    
    def _insert_suggestion(self, append_text):
        self.input_text.insert('end', append_text)
        self._check_empty_state()
        self._schedule_auto_translate()

    def _check_empty_state(self):
        try:
            content = self.input_text.get('1.0', 'end').strip()
            if not content:
                self.paste_btn.place(relx=0.0, rely=0.0, anchor='nw', x=5, y=5)
                # Xóa toàn bộ kết quả khi input trống
                if hasattr(self, 'result_widgets'):
                    for widget in self.result_widgets.values():
                        widget.config(state='normal')
                        widget.delete('1.0', 'end')
                        widget.config(height=1, state='disabled')
                if hasattr(self, 'status_label'):
                    self.status_label.config(text=t('status_ready'), foreground=self.colors['fg'])
            else:
                self.paste_btn.place_forget()
        except:
            pass

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill='both', expand=True)
        
        # === HEADER SECTION ===
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill='x', pady=(0, 5))
        
        # Input Label
        self.input_label = ttk.Label(header_frame, text=t('input_label'), font=('Segoe UI', 11, 'bold'))
        self.input_label.pack(side='left', padx=(0, 10))
        
        # Controls (Right side)
        settings_btn = ttk.Button(header_frame, text="⚙️", width=3,
                                 command=self._open_settings)
        settings_btn.pack(side='right')
        
        self.topmost_check = ttk.Checkbutton(header_frame, text="📌",
                                            variable=self.always_on_top,
                                            command=self._toggle_topmost)
        self.topmost_check.pack(side='right', padx=5)
        
        # Clipboard Monitor Toggle
        self.clipboard_check = ttk.Checkbutton(header_frame, text="📋",
                                              variable=self.clipboard_monitor_var,
                                              command=self._toggle_clipboard_monitor)
        self.clipboard_check.pack(side='right', padx=5)
        
        # Quick Translate Toggle
        self.quick_check = ttk.Checkbutton(header_frame, text="🎯",
                                          variable=self.quick_translate_var,
                                          command=self._toggle_quick_translate)
        self.quick_check.pack(side='right', padx=5)

        # Translation Mode Toggle (Offline/Online)
        _init_mode_text = t('mode_online') if self.config.get('translation_mode') == 'online' else t('mode_offline')
        self.mode_btn = ttk.Button(header_frame, text=_init_mode_text, width=10,
                                   command=self._toggle_translation_mode)
        self.mode_btn.pack(side='right', padx=5)

        # === INPUT SECTION ===
        input_container = ttk.Frame(main_frame)
        input_container.pack(fill='x', pady=(0, 10))
        
        # Input text box
        self.input_text = tk.Text(input_container, height=3, font=('Microsoft YaHei', 14),
                                  bg=self.colors['surface'], fg=self.colors['fg'],
                                  insertbackground=self.colors['fg'],
                                  relief='flat', padx=10, pady=8)
        self.input_text.pack(fill='x')
        self.input_text.bind('<Return>', lambda e: self._on_translate())
        self.input_text.bind('<Double-Button-1>', self._force_paste_and_translate)
        
        # Clear Button (X)
        self.clear_input_btn = tk.Button(self.input_text, text="✖", font=('Segoe UI', 10),
                                         bg=self.colors['surface'], fg=self.colors['fg'],
                                         relief='flat', cursor='hand2', borderwidth=0,
                                         command=lambda: [self.input_text.delete('1.0', 'end'), self._check_empty_state(), self._update_suggestions([])])
        self.clear_input_btn.place(relx=1.0, rely=0.0, anchor='ne', x=-5, y=5)
        
        # Auto-translate feature
        self._auto_translate_id = None
        self.input_text.bind('<KeyRelease>', self._on_key_release)

        # Paste Button (Top-Left cố định) - cùng style với nút X
        self.paste_btn = tk.Button(self.input_text, text="📋",
                                   font=('Segoe UI', 15),
                                   bg=self.colors['surface'], fg='#9399b2',
                                   relief='flat', cursor='hand2', borderwidth=0,
                                   command=self._force_paste_and_translate)
        self.paste_btn.bind('<Enter>', lambda e: self.paste_btn.configure(fg=self.colors['fg']))
        self.paste_btn.bind('<Leave>', lambda e: self.paste_btn.configure(fg='#9399b2'))
        # Hiển thị ban đầu ở góc trên-trái cố định (giống nút X nhưng bên trái)
        self.paste_btn.place(relx=0.0, rely=0.0, anchor='nw', x=5, y=5)
        
        # Speaker button (Floating inside Input Text - Bottom Right)
        self.speak_btn = ttk.Button(input_container, text="🔊", width=3,
                                   command=self._speak_chinese)
        # Place relative to input_text
        self.speak_btn.place(in_=self.input_text, relx=1.0, rely=1.0, anchor='se', x=-2, y=-2)
        
        # Suggestions Frame (Gợi ý)
        self.suggestions_frame = ttk.Frame(main_frame)
        self.suggestions_label = ttk.Label(self.suggestions_frame, text=t('suggestions_label'), font=('Segoe UI', 9, 'bold'), foreground=self.colors['yellow'])
        self.suggestions_label.pack(side='left', padx=(0, 5))
        self.sugg_buttons = []
        for i in range(7):
            btn = tk.Button(self.suggestions_frame, text="", font=('Microsoft YaHei', 11),
                           bg=self.colors['surface'], fg=self.colors['accent2'],
                           relief='flat', cursor='hand2', borderwidth=0)
            btn.pack(side='left', padx=2)
            # Hover effect
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.colors['surface2']))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=self.colors['surface']))
            self.sugg_buttons.append(btn)
        
        # Actions Row
        self.action_frame = ttk.Frame(main_frame)
        self.action_frame.pack(fill='x', pady=(0, 15))
        
        # History Navigation Buttons
        self.back_btn = ttk.Button(self.action_frame, text="⬅️", width=3,
                                      command=lambda: self.navigate_history(-1))
        self.back_btn.pack(side='left', padx=(0, 5))
        
        self.forward_btn = ttk.Button(self.action_frame, text="➡️", width=3,
                                     command=lambda: self.navigate_history(1))
        self.forward_btn.pack(side='left', padx=(0, 5))
        
        # History List Button
        self.history_btn = ttk.Button(self.action_frame, text="📜", width=3,
                                     command=self._open_history_list)
        self.history_btn.pack(side='left', padx=(0, 10))
        
        # Initial button state
        self._update_nav_buttons()
        
        self.translate_btn = ttk.Button(self.action_frame, text=t('btn_translate'),
                                        command=self._on_translate, style='Accent.TButton')
        self.translate_btn.pack(side='left', padx=(0, 10))
        
        self.handwriting_btn = ttk.Button(self.action_frame, text=t('btn_handwriting'),
                                         command=self._open_handwriting)
        self.handwriting_btn.pack(side='left', padx=(0, 10))
        
        self.capture_btn = ttk.Button(self.action_frame, text=t('btn_capture'),
                                     command=self._on_capture)
        self.capture_btn.pack(side='left')
        
        # Determine RapidOCR status
        from ocr_capture import check_rapidocr_availability
        self.rapidocr_ready = check_rapidocr_availability()
        
        if not self.rapidocr_ready:
            self.install_btn = ttk.Button(action_frame, text="⬇️ Cài RapidOCR",
                                         command=self._install_rapidocr)
            self.install_btn.pack(side='left', padx=10)

        # === OUTPUT SECTION ===
        self.result_frame = ttk.LabelFrame(main_frame, text=t('result_title'), padding=2)
        output_frame = self.result_frame
        output_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Canvas and Scrollbar for scrolling
        canvas = tk.Canvas(output_frame, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(output_frame, orient="vertical", command=canvas.yview)
        
        self.scrollable_content = ttk.Frame(canvas)
        self.scrollable_content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_content, anchor="nw",
                             width=canvas.winfo_reqwidth())
                             
        # Auto resize canvas inner frame width
        def on_canvas_configure(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack layout
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Mousewheel scrolling (bind to canvas only, không dùng bind_all để tránh xung đột popup)
        def _on_mousewheel(event):
            try:
                bbox = canvas.bbox("all")
                if not bbox: return
                if bbox[3] - bbox[1] > canvas.winfo_height():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass
        
        canvas.bind("<MouseWheel>", _on_mousewheel)
        self.scrollable_content.bind("<MouseWheel>", _on_mousewheel)
        
        # Initialize result widgets based on config/layout
        self._update_result_layout()
        
        # === STATUS BAR ===
        self.status_label = ttk.Label(main_frame, text=t('status_ready'),
                                     font=('Segoe UI', 9))
        self.status_label.pack(fill='x', pady=(10, 0))
        
        # TTS Queue and Worker
        import queue
        self.tts_queue = queue.Queue()
        threading.Thread(target=self._tts_worker, daemon=True).start()
        
        if self.input_text.get('1.0', 'end').strip():
            self._schedule_auto_translate()
            
    def _insert_handwriting_char(self, char):
        try:
            sel_first = self.input_text.index("sel.first")
            sel_last = self.input_text.index("sel.last")
            self.input_text.delete(sel_first, sel_last)
        except tk.TclError:
            pass
            
        self.input_text.insert(tk.INSERT, char)
        self._check_empty_state()
        self._schedule_auto_translate()
        
    def _apply_language(self):
        """Update all static UI widgets to use the current language. Called when language changes."""
        # Window title
        self.root.title(t('app_title'))
        # Input section label
        if hasattr(self, 'input_label'):
            self.input_label.config(text=t('input_label'))
        # Translate button
        if hasattr(self, 'translate_btn'):
            self.translate_btn.config(text=t('btn_translate'))
        # Handwriting button
        if hasattr(self, 'handwriting_btn'):
            self.handwriting_btn.config(text=t('btn_handwriting'))
        # Capture button
        if hasattr(self, 'capture_btn'):
            self.capture_btn.config(text=t('btn_capture'))
        # Mode button
        self._update_mode_button_text()
        # Result panel label
        if hasattr(self, 'result_frame'):
            try:
                self.result_frame.config(text=t('result_title'))
            except Exception:
                pass
        # Suggestions label
        if hasattr(self, 'suggestions_label'):
            self.suggestions_label.config(text=t('suggestions_label'))
        # Rebuild result rows with new language labels
        self._update_result_layout()
        # Status bar
        if hasattr(self, 'status_label'):
            current = self.status_label.cget('text')
            # Only reset if showing "ready"-like text
            if not current.startswith(('✅', '❌', '⏳', '⚠️')):
                self.status_label.config(text=t('status_ready'))

    def _open_handwriting(self):
        """Mở cửa sổ Viết Tay — tối đa 2 cửa sổ, sang bên cạnh UI chính"""
        # Dọn danh sách: loại bỏ các cửa sổ đã đóng
        if not hasattr(self, '_hw_windows'):
            self._hw_windows = []
        self._hw_windows = [w for w in self._hw_windows if w.window.winfo_exists()]

        # Giới hạn tối đa 2 cửa sổ
        if len(self._hw_windows) >= 2:
            # Focus vào cửa sổ cuối cùng đang mở
            self._hw_windows[-1].window.lift()
            self._hw_windows[-1].window.focus_force()
            return

        # Mở cửa sổ mới với offset theo số cửa đang mở
        offset = len(self._hw_windows)
        hw = HandwritingWindow(self.root, self.colors, self._insert_handwriting_char,
                               position_offset=offset)
        self._hw_windows.append(hw)

    def _clear_input(self):
        """Clear input text"""
        self.input_text.delete('1.0', 'end')
        self._check_empty_state()
        if hasattr(self, 'status_label'):
            self.status_label.config(text=t('status_ready'))

    def _copy_text(self, text):
        """Helper to copy text to clipboard"""
        if text.strip():
            self.root.clipboard_clear()
            self.root.clipboard_append(text.strip())
            self._set_status("📋 Đã copy!", 'green')


    def _tts_worker(self):
        """Dedicated TTS worker thread - Uses edge-tts for high quality neural voices,
        with fallback to pyttsx3 if offline."""
        import pythoncom
        import pyttsx3
        import asyncio
        import os
        import tempfile
        import pygame
        
        # --- 1. Init Pygame Mixer for Audio Playback ---
        try:
            pygame.mixer.init()
            print("Pygame mixer initialized for TTS.")
        except Exception as e:
            print(f"Pygame init error: {e}")

        # --- 2. Pyttsx3 Fallback Initialization (Run once) ---
        try:
            pythoncom.CoInitialize()
            probe_engine = pyttsx3.init(driverName='sapi5')
            voices = probe_engine.getProperty('voices')
            
            chinese_voice_id = None
            english_voice_id = None
            
            for voice in voices:
                name_lower = voice.name.lower()
                if not chinese_voice_id and any(cn in name_lower for cn in ['chinese', 'huihui', 'yaoyao', 'kangkang', 'hanhan', 'zhiwei', 'lili']):
                    chinese_voice_id = voice.id
                if not english_voice_id and any(en in name_lower for en in ['english', 'zira', 'david', 'linda']):
                    english_voice_id = voice.id
            
            if not english_voice_id and voices:
                 english_voice_id = voices[0].id

            del probe_engine
            print(f"Fallback TTS Config - CN: {chinese_voice_id} | EN: {english_voice_id}")
            
        except Exception as e:
            print(f"TTS Probe Failed: {e}")
            chinese_voice_id = None
            english_voice_id = None

        def is_contains_chinese(text):
            for char in text:
                if u'\u4e00' <= char <= u'\u9fff':
                    return True
            return False

        print("TTS Worker Ready (Edge-TTS + Pyttsx3 Fallback)")

        # --- Async helper to generate edge-tts audio ---
        async def _generate_edge_audio(text, is_zh, output_file):
            import edge_tts
            voice = "zh-CN-XiaoxiaoNeural" if is_zh else "en-US-AriaNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)

        # --- 3. Loop Phase ---
        temp_audio_file = os.path.join(tempfile.gettempdir(), "translator_tts_temp.mp3")

        while True:
            try:
                # Get text (blocking)
                text = self.tts_queue.get()
                
                if text == "STOP":
                    pass # Just ignore or break
                elif text:
                    print(f"Speaking: {repr(text)}")
                    is_zh = is_contains_chinese(text)
                    success_edge = False

                    # Stop any currently playing audio
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    
                    # Unload file so it can be overwritten
                    pygame.mixer.music.unload()

                    # Try Edge-TTS (requires internet)
                    try:
                        import edge_tts
                        # Run async function in sync context
                        asyncio.run(_generate_edge_audio(text, is_zh, temp_audio_file))
                        
                        if os.path.exists(temp_audio_file):
                            pygame.mixer.music.load(temp_audio_file)
                            pygame.mixer.music.play()
                            
                            # Wait for playback to finish (while allowing UI to unfreeze, since this is a separate thread)
                            while pygame.mixer.music.get_busy():
                                pygame.time.Clock().tick(10)
                            
                            success_edge = True
                    except Exception as edge_err:
                        print(f"Edge-TTS failed (offline?): {edge_err}")
                        success_edge = False

                    # Fallback to Pyttsx3 (offline)
                    if not success_edge:
                        try:
                            print("Falling back to local pyttsx3...")
                            # Re-init engine EVERY TIME to prevent COM loop lockups
                            engine = pyttsx3.init(driverName='sapi5')
                            engine.setProperty('rate', 140)
                            engine.setProperty('volume', 1.0)
                            
                            if is_zh and chinese_voice_id:
                                engine.setProperty('voice', chinese_voice_id)
                            elif not is_zh and english_voice_id:
                                engine.setProperty('voice', english_voice_id)
                            
                            engine.say(text)
                            engine.runAndWait()
                            del engine
                            
                        except Exception as e:
                            print(f"Fallback TTS Speak Error: {e}")

                self.tts_queue.task_done()
                
            except Exception as e:
                print(f"TTS Loop Error: {e}")



    def _speak_chinese(self):
        """Queue text for TTS worker"""
        text = self.input_text.get('1.0', 'end').strip()
        
        if not text:
            # Fallback to result if input empty
            widget = self.result_widgets.get('chinese')
            if widget:
                text = widget.get('1.0', 'end').strip()
        
        if text:
            # Remove online indicator if present
            if text.startswith("🌐"):
                text = text.replace("🌐", "").strip()
            
            self._set_status(t('tts_speaking', text=text[:10]), 'accent')
            
            # Clear queue to prioritize new speech
            with self.tts_queue.mutex:
                self.tts_queue.queue.clear()
            self.tts_queue.put(text)
        else:
            self._set_status(t('tts_no_content'), 'yellow')

    def _setup_hotkey(self):
        """Setup global hotkeys using 'keyboard' lib — works inside fullscreen games.
        Alt+X  → frozen screen capture + OCR
        Ctrl+Shift+V → quick paste & translate
        """
        import keyboard as kb

        def on_capture_hotkey():
            self.root.after(0, self._on_capture)

        def on_quick_translate_hotkey():
            if self.quick_translate_var.get():
                self.root.after(0, self._quick_paste_and_translate)

        try:
            kb.add_hotkey('alt+x', on_capture_hotkey, suppress=False)
            kb.add_hotkey('ctrl+shift+v', on_quick_translate_hotkey, suppress=False)
            print("Global hotkeys registered: Alt+X (capture), Ctrl+Shift+V (quick translate)")
        except Exception as e:
            print(f"Hotkey registration failed: {e}")
    
    def _quick_paste_and_translate(self):
        """Quick paste from clipboard and translate - shows window"""
        try:
            content = self.root.clipboard_get()
            if content and content.strip():
                self._show_window()
                self.input_text.delete('1.0', 'end')
                self.input_text.insert('1.0', content)
                self._check_empty_state()
                self._on_translate()
        except:
            pass

    def _setup_tray(self):
        """Setup System Tray Icon"""
        import pystray
        from PIL import Image, ImageDraw

        # Create a simple icon
        image = Image.new('RGB', (64, 64), color=(30, 30, 46))
        d = ImageDraw.Draw(image)
        d.text((10, 10), "译", fill=(137, 180, 250), font_size=40)
        
        def quit_app(icon, item):
            icon.stop()
            self.root.quit()

        def show_app(icon, item):
            self._show_window()

        menu = pystray.Menu(
            pystray.MenuItem(t('tray_open'), show_app, default=True),
            pystray.MenuItem(t('tray_quit'), quit_app)
        )

        self.tray_icon = pystray.Icon("ChineseTranslator", image, t('app_title'), menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _show_window(self):
        """Restore window from tray"""
        self.root.deiconify()
        self.root.state('normal')
        self.root.lift()
        self.root.focus_force()

    def _hide_window(self):
        """Minimize to tray, or exit completely if Shift is held"""
        import ctypes
        # VK_SHIFT is 0x10
        if ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000:
            # Shift is held, close the app instantly
            self.root.withdraw()
            self.root.update()
            
            if hasattr(self, 'tray_icon'):
                try:
                    self.tray_icon.visible = False
                    self.tray_icon.stop()
                except Exception:
                    pass
            
            try:
                self.root.destroy()
            except:
                pass
                
            import os
            os._exit(0)
        else:
            self.root.withdraw()



    def _show_toast_notification(self, message: str, color_key: str = 'green'):
        """Show a temporary toast notification popup"""
        # Check if there's already a toast visible
        if hasattr(self, 'toast_label') and self.toast_label and self.toast_label.winfo_exists():
            self.toast_label.destroy()

        # Create toast label
        self.toast_label = tk.Label(
            self.root,
            text=message,
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors.get(color_key, self.colors['green']),
            fg='#1e1e2e',
            padx=15,
            pady=8,
            relief='raised',
            borderwidth=2
        )
        
        # Position at bottom-right of the window
        self.toast_label.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)
        
        # Auto-hide after 3 seconds
        def hide_toast():
            if hasattr(self, 'toast_label') and self.toast_label:
                try:
                    self.toast_label.destroy()
                except:
                    pass
                self.toast_label = None
        
        self.root.after(3000, hide_toast)
    
    def _on_capture(self):
        """Game-compatible screen capture: hides app first, freezes screen instantly,
        then shows overlay on frozen image for region selection.
        """
        self._set_status(t('ocr_preparing'), 'accent')

        # Hide the app window so it doesn't appear in the screenshot
        self.root.withdraw()

        def on_ocr_result(text, error):
            # Always restore the window when done (success, cancel, or error)
            # But skip restoring on tiny-selection so user can try again
            if error and 'Vùng chọn quá nhỏ' in str(error):
                self.root.after(0, self._show_window)
                self.root.after(0, lambda: self._set_status(f"⚠️ {error}", 'yellow'))
                return
            if error and ('Đã hủy' in str(error) or 'cancelled' in str(error).lower()):
                self.root.after(0, self._show_window)
                self.root.after(0, lambda: self._set_status(t('ocr_cancelled'), 'fg'))
                return

            # Show window with results
            self.root.after(0, self._show_window)

            if error:
                def show_err():
                    self._set_status(t('ocr_error', error), 'yellow')
                    messagebox.showwarning(t('ocr_error_title'), str(error))
                self.root.after(0, show_err)
                return

            if text:
                def on_success():
                    self.input_text.delete('1.0', 'end')
                    self.input_text.insert('1.0', text)
                    self._check_empty_state()
                    self._on_translate()
                self.root.after(0, on_success)
            else:
                self.root.after(0, lambda: self._set_status(t('ocr_no_text'), 'yellow'))

        # Wait a short moment for the window to fully disappear before grabbing the screen
        def start_capture():
            capture_frozen_and_ocr(on_ocr_result, lang='chinese', tk_root=self.root)

        self.root.after(150, start_capture)

    
    def _show_results(self, results: dict, is_online: bool = False):
        """Display translation results with auto-height"""
        for key, text in results.items():
            widget = self.result_widgets.get(key)
            if widget:
                # If online update, only update english/vietnamese and add indicator
                if is_online:
                    if key not in ['english', 'vietnamese']:
                        continue
                    if not text:
                        continue

                display_text = text
                # Add online indicator for better visibility
                if is_online and text:
                    display_text = f"🌐 {text}"

                widget.config(state='normal')
                widget.config(height=1) # Reset to calculate correctly
                widget.delete('1.0', 'end')
                widget.insert('1.0', display_text)
                
                # Auto-expand height based on content
                # We need to update idletasks to get correct line count
                widget.update_idletasks()
                
                # Count display lines (handled wrapped lines)
                num_lines = widget.count("1.0", "end", "displaylines")
                if num_lines:
                    # Limit max height to avoid layout breaking (e.g. 10 lines)
                    new_height = min(int(num_lines[0]), 10)
                    widget.config(height=new_height)
                
                widget.config(state='disabled')
    
    def _copy_result(self, key: str):
        """Copy result to clipboard"""
        widget = self.result_widgets.get(key)
        if widget:
            text = widget.get('1.0', 'end').strip()
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self._set_status(t('status_copied'), 'green')
    
    def _set_status(self, text: str, color_key: str = 'fg'):
        """Update status bar"""
        color = self.colors.get(color_key, self.colors['fg'])
        self.status_label.config(text=text, foreground=color)
    
    def _install_rapidocr(self):
        """Install RapidOCR via pip"""
        if not messagebox.askyesno(t('install_rapidocr_title'), t('install_rapidocr_msg')):
            return
            
        self._set_status(t('install_status_busy'), 'accent')
        self.root.update()
        
        def run_install():
            import subprocess
            import sys
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "rapidocr-onnxruntime"])
                self.root.after(0, lambda: messagebox.showinfo(t('install_rapidocr_title'), t('install_rapidocr_done')))
                self.root.after(0, lambda: self.install_btn.pack_forget())
                self.root.after(0, lambda: self._set_status(t('install_status_ok'), 'green'))
            except Exception as e:
                self.root.after(0, lambda e=e: messagebox.showerror(t('confirm_title'), t('install_rapidocr_fail').format(e)))
                self.root.after(0, lambda: self._set_status(t('install_status_fail'), 'red'))
                
        threading.Thread(target=run_install, daemon=True).start()

    def _toggle_topmost(self):
        """Toggle always on top manually"""
        # Just apply the new state
        self._apply_topmost_state()

def main():
    import sys
    
    # Check if starting hidden (for autostart)
    start_hidden = '--hidden' in sys.argv
    
    root = tk.Tk()
    
    # CRITICAL: Withdraw window BEFORE building UI to prevent flash
    if start_hidden:
        root.withdraw()
    
    app = ChineseTranslatorApp(root)
    
    # If NOT hidden, make sure window is visible
    if not start_hidden:
        root.deiconify()
    
    root.mainloop()


if __name__ == "__main__":
    main()
