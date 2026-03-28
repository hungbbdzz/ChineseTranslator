# -*- coding: utf-8 -*-
"""
i18n.py — Simple internationalization module for ChineseTranslator
Supported languages: 'vi' (Vietnamese), 'en' (English)
"""

STRINGS = {
    'vi': {
        # Window / titles
        'app_title':             '📖 Dịch Tiếng Trung',
        'input_label':           '📝 Nhập Văn Bản',
        'result_title':          '📖 Kết Quả',
        'settings_title':        'Cài đặt hiển thị',

        # Buttons
        'btn_translate':         '🔄 Dịch Ngay',
        'btn_handwriting':       '✍️ Viết Tay',
        'btn_capture':           '📸 Alt+X: Chụp & Dịch',
        'btn_close':             'Đóng',
        'btn_save':              'Lưu',

        # Mode toggle
        'mode_offline':          '📡 Offline',
        'mode_online':           '🌐 Online',

        # Result row labels
        'row_chinese':           '🀄 Hán Tự:',
        'row_hanviet':           '🇻🇳 Hán Việt:',
        'row_pinyin':            '🔤 Pinyin:',
        'row_english':           '🇬🇧 English:',
        'row_vietnamese':        '📝 Tiếng Việt:',

        # Status messages
        'status_ready':          'Sẵn sàng',
        'status_translating':    '⏳ Đang dịch...',
        'status_done_offline':   '✅ Dịch Offline (HF) xong!',
        'status_done_online':    '✅ Dịch Online (Google) xong! 🌐',
        'status_done_reverse':   '✅ Đã dịch xong!',
        'status_reverse_start':  '⏳ Đang dịch ngược → Hán Tự...',
        'status_empty':          '⚠️ Vui lòng nhập nội dung',
        'status_no_internet':    '⚠️ Không dịch được sang Hán Tự (cần internet)',
        'status_error':          '❌ Lỗi: {}',
        'status_copied':         '📋 Đã copy!',
        'status_cleared':        'Sẵn sàng',

        # Settings dialog
        'settings_script_label': 'Kiểu chữ Hán:',
        'settings_simplified':   'Giản thể (Mặc định)',
        'settings_traditional':  'Phồn thể (Truyền thống)',
        'settings_rows_label':   'Chọn dòng kết quả:',
        'settings_lang_label':   'Ngôn ngữ giao diện:',

        # Row visibility names
        'vis_chinese':           'Hán Tự',
        'vis_hanviet':           'Hán Việt',
        'vis_pinyin':            'Pinyin',
        'vis_english':           'English',
        'vis_vietnamese':        'Tiếng Việt',

        # History dialog
        'history_title':         '📜 Lịch sử dịch',
        'history_header':        '📜 Lịch sử ({count} bản dịch)',
        'history_empty':         'Chưa có lịch sử dịch',
        'history_search_hint':   '🔍',
        'history_fav_filter':    '⭐ Chỉ yêu thích',
        'history_select_all':    '☑️ Chọn',
        'history_delete_sel':    '🗑️ Xóa chọn',
        'history_delete_all':    '⚠️ Xóa hết',
        'history_export':        '📤 Xuất',
        'history_import':        '📥 Nhập',
        'history_close':         'Đóng',
        'history_status':        '📜 Lịch sử: {cur}/{total}',

        # Confirm dialogs
        'confirm_title':         'Xác nhận',
        'confirm_delete_n':      'Xóa {n} mục đã chọn?',
        'confirm_delete_all':    'Xóa TOÀN BỘ {n} lịch sử?',
        'confirm_import_err':    'Không thể nhập: {e}',
        'import_done':           '📥 Đã nhập {n} mục mới',
        'export_done':           '📤 Đã xuất {n} mục',
        'delete_all_done':       '🗑️ Đã xóa toàn bộ lịch sử',

        # Notifications / toasts
        'toast_mode_switched':   '✅ Chuyển sang chế độ {}',
        'toast_lang_changed':    '✅ Ngôn ngữ đã cập nhật!',

        # Tray
        'tray_open':             'Mở giao diện',
        'tray_quit':             'Thoát',

        # OCR
        'ocr_error_title':       'Lỗi OCR',

        # Clipboard / quick translate
        'clipboard_status':      '📋 Clipboard Monitor: {}',
        'quick_translate_status':'🎯 Quick Translate (Ctrl+Shift+V): {}',

        # OCR / capture
        'ocr_preparing':         '📸 Đang chuẩn bị chụp màn hình...',
        'ocr_cancelled':         'Đã hủy chụp',
        'ocr_no_text':           '⚠️ Không tìm thấy văn bản',
        'ocr_error':             '⚠️ {}',

        # TTS
        'tts_speaking':          '🔊 Đang đọc: {text}...',
        'tts_no_content':        '⚠️ Không có nội dung để đọc',

        # Handwriting
        'hw_title':              '✍️ Viết Tay',
        'hw_guide':              'Viết chữ Hán vào ô bên dưới:',
        'hw_predictions':        'Dự đoán (Cuộn chuột xem thêm - Click để chọn):',
        'hw_ready':              'Sẵn sàng',
        'hw_recognizing':        'Đang nhận dạng...',
        'hw_recognized':         'Đã nhận dạng',
        'hw_added':              "Đã thêm '{char}'",
        'hw_cleared':            'Đã xóa',
        'hw_api_error':          'Lỗi từ API',
        'hw_timeout':            'Timeout',
        'hw_conn_error':         'Lỗi kết nối',
        'hw_error':              'Lỗi',
        'hw_undo':               '⬅ Lui',
        'hw_redo':               'Tiến ➡',
        'hw_clear':              '🗑️ Xóa hết',

        # Mini dict
        'dict_title':            '📖 Từ điển: {char}',
        'dict_pinyin':           '🔤 Pinyin: {pinyin}',
        'dict_hanviet':          '🇻🇳 Hán Việt: {hanviet}',
        'dict_radical':          '📐 Bộ thủ: {radical}',
        'dict_words':            '📚 Từ ghép & Ví dụ (Click để dịch):',
        'dict_examples':         '💬 Câu ví dụ:',
        'dict_close':            'Đóng',

        # Install
        'install_rapidocr_title':'Cài đặt RapidOCR',
        'install_rapidocr_msg':  'Bạn có muốn tải và cài đặt thư viện RapidOCR (khoảng 40MB) không?',
        'install_rapidocr_done': 'Đã cài đặt RapidOCR! Vui lòng khởi động lại App.',
        'install_rapidocr_fail': 'Không thể cài đặt:\n{}',
        'install_status_ok':     '✅ Cài đặt xong! Hãy khởi động lại.',
        'install_status_fail':   '❌ Cài đặt thất bại',
        'install_status_busy':   '⏳ Đang cài đặt RapidOCR...',

        # Suggestions
        'suggestions_label':     '💡 Gợi ý:',
    },

    'en': {
        # Window / titles
        'app_title':             '📖 Chinese Translator',
        'input_label':           '📝 Input Text',
        'result_title':          '📖 Results',
        'settings_title':        'Display Settings',

        # Buttons
        'btn_translate':         '🔄 Translate',
        'btn_handwriting':       '✍️ Handwriting',
        'btn_capture':           '📸 Alt+X: Capture & Translate',
        'btn_close':             'Close',
        'btn_save':              'Save',

        # Mode toggle
        'mode_offline':          '📡 Offline',
        'mode_online':           '🌐 Online',

        # Result row labels
        'row_chinese':           '🀄 Chinese:',
        'row_hanviet':           '🇻🇳 Sino-Vietnamese:',
        'row_pinyin':            '🔤 Pinyin:',
        'row_english':           '🇬🇧 English:',
        'row_vietnamese':        '📝 Vietnamese:',

        # Status messages
        'status_ready':          'Ready',
        'status_translating':    '⏳ Translating...',
        'status_done_offline':   '✅ Offline (HF) translation done!',
        'status_done_online':    '✅ Online (Google) translation done! 🌐',
        'status_done_reverse':   '✅ Translation done!',
        'status_reverse_start':  '⏳ Translating to Chinese...',
        'status_empty':          '⚠️ Please enter some text',
        'status_no_internet':    '⚠️ Cannot translate to Chinese (internet required)',
        'status_error':          '❌ Error: {}',
        'status_copied':         '📋 Copied!',
        'status_cleared':        'Ready',

        # Settings dialog
        'settings_script_label': 'Chinese Script:',
        'settings_simplified':   'Simplified (Default)',
        'settings_traditional':  'Traditional',
        'settings_rows_label':   'Select result rows:',
        'settings_lang_label':   'Interface language:',

        # Row visibility names
        'vis_chinese':           'Chinese',
        'vis_hanviet':           'Sino-Vietnamese',
        'vis_pinyin':            'Pinyin',
        'vis_english':           'English',
        'vis_vietnamese':        'Vietnamese',

        # History dialog
        'history_title':         '📜 Translation History',
        'history_header':        '📜 History ({count} entries)',
        'history_empty':         'No translation history yet',
        'history_search_hint':   '🔍',
        'history_fav_filter':    '⭐ Favorites only',
        'history_select_all':    '☑️ Select',
        'history_delete_sel':    '🗑️ Delete selected',
        'history_delete_all':    '⚠️ Delete all',
        'history_export':        '📤 Export',
        'history_import':        '📥 Import',
        'history_close':         'Close',
        'history_status':        '📜 History: {cur}/{total}',

        # Confirm dialogs
        'confirm_title':         'Confirm',
        'confirm_delete_n':      'Delete {n} selected items?',
        'confirm_delete_all':    'Delete ALL {n} history entries?',
        'confirm_import_err':    'Cannot import: {e}',
        'import_done':           '📥 Imported {n} new entries',
        'export_done':           '📤 Exported {n} entries',
        'delete_all_done':       '🗑️ All history deleted',

        # Notifications / toasts
        'toast_mode_switched':   '✅ Switched to {} mode',
        'toast_lang_changed':    '✅ Language updated!',

        # Tray
        'tray_open':             'Open App',
        'tray_quit':             'Quit',

        # OCR
        'ocr_error_title':       'OCR Error',

        # Clipboard / quick translate
        'clipboard_status':      '📋 Clipboard Monitor: {}',
        'quick_translate_status':'🎯 Quick Translate (Ctrl+Shift+V): {}',

        # OCR / capture
        'ocr_preparing':         '📸 Preparing screen capture...',
        'ocr_cancelled':         'Capture cancelled',
        'ocr_no_text':           '⚠️ No text found',
        'ocr_error':             '⚠️ {}',

        # TTS
        'tts_speaking':          '🔊 Speaking: {text}...',
        'tts_no_content':        '⚠️ No text to speak',

        # Handwriting
        'hw_title':              '✍️ Handwriting',
        'hw_guide':              'Write Chinese characters below:',
        'hw_predictions':        'Predictions (scroll for more — click to select):',
        'hw_ready':              'Ready',
        'hw_recognizing':        'Recognizing...',
        'hw_recognized':         'Recognized',
        'hw_added':              "Added '{char}'",
        'hw_cleared':            'Cleared',
        'hw_api_error':          'API error',
        'hw_timeout':            'Timeout',
        'hw_conn_error':         'Connection error',
        'hw_error':              'Error',
        'hw_undo':               '⬅ Undo',
        'hw_redo':               'Redo ➡',
        'hw_clear':              '🗑️ Clear All',

        # Mini dict
        'dict_title':            '📖 Dictionary: {char}',
        'dict_pinyin':           '🔤 Pinyin: {pinyin}',
        'dict_hanviet':          '🇻🇳 Sino-Viet: {hanviet}',
        'dict_radical':          '📐 Radical: {radical}',
        'dict_words':            '📚 Compound words & Examples (click to translate):',
        'dict_examples':         '💬 Example sentences:',
        'dict_close':            'Close',

        # Install
        'install_rapidocr_title':'Install RapidOCR',
        'install_rapidocr_msg':  'Do you want to download and install RapidOCR (~40MB)?',
        'install_rapidocr_done': 'RapidOCR installed! Please restart the app.',
        'install_rapidocr_fail': 'Cannot install:\n{}',
        'install_status_ok':     '✅ Installed! Please restart.',
        'install_status_fail':   '❌ Installation failed',
        'install_status_busy':   '⏳ Installing RapidOCR...',

        # Suggestions
        'suggestions_label':     '💡 Suggestions:',
    }
}

# --- Module-level active language ---
_current_lang = 'vi'


def set_language(lang: str) -> None:
    """Set the active UI language. lang: 'vi' | 'en'"""
    global _current_lang
    if lang in STRINGS:
        _current_lang = lang


def get_language() -> str:
    """Return the currently active language code."""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """
    Look up a translated string by key.
    Falls back to Vietnamese, then to the key itself.
    Supports named format args: t('history_header', count=5)
    """
    lang_dict = STRINGS.get(_current_lang, STRINGS['vi'])
    text = lang_dict.get(key, STRINGS['vi'].get(key, key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text
