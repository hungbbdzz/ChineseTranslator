# -*- coding: utf-8 -*-


import os
import csv
import ast
import sys
import typing
import atexit
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import threading
import compat_patch
from logger_utils import get_logger

# Set up logging
logger = get_logger(__name__)

# Apply compatibility patch immediately
compat_patch.apply_patch()

# Thread pool for concurrent operations (reuse across calls)
_executor = ThreadPoolExecutor(max_workers=4)

# Register cleanup function
def _cleanup_executor():
    """Shutdown executor on program exit"""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=False)
        logger.info("ThreadPoolExecutor shutdown complete")

atexit.register(_cleanup_executor)

# Lazy loading for heavy modules
_pypinyin = None
_argos_translator = None
_init_lock = threading.Lock()

def _get_pypinyin():
    global _pypinyin
    if _pypinyin is None:
        import pypinyin
        _pypinyin = pypinyin
    return _pypinyin

def _ensure_package(from_code, to_code):
    """Ensure specific Argos Translate package is installed"""
    import argostranslate.package

    # Check installed
    installed = argostranslate.package.get_installed_packages()
    if any(p.from_code == from_code and p.to_code == to_code for p in installed):
        return True

    logger.info(f"Package {from_code}->{to_code} not found. Installing...")

    # Allow update index only if strictly necessary to avoid lag
    try:
        # Check available packages in current index first without updating?
        # No, safest to update index if we are missing a package we intend to install
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()

        target_pkg = next((p for p in available if p.from_code == from_code and p.to_code == to_code), None)

        if target_pkg:
            logger.info(f"Downloading {target_pkg.from_name} -> {target_pkg.to_name}...")
            path = target_pkg.download()
            argostranslate.package.install_from_path(path)
            logger.info(f"Installed {from_code}->{to_code}")
            return True
        else:
            logger.error(f"Error: Model {from_code}->{to_code} not found in repository.")
            return False
    except Exception as e:
        logger.error(f"Error installing package {from_code}->{to_code}: {e}")
        return False

def _get_argos_translator(source_lang='zh'):
    """Initialize Argos Translate with required models (thread-safe)"""
    global _argos_translator

    with _init_lock:
        try:
            import argostranslate.package
            import argostranslate.translate

            # Always ensure 'en' -> 'vi' as fallback chain
            _ensure_package('en', 'vi')

            # Determine source language code
            if source_lang == 'chinese': code = 'zh'
            elif source_lang == 'japanese': code = 'ja'
            elif source_lang == 'korean': code = 'ko'
            else: code = 'zh'

            # Ensure source -> en (fallback chain)
            if code != 'en':
                _ensure_package(code, 'en')

            # Improvement #4: also try to get a direct source -> vi package
            if code not in ('en', 'vi'):
                _ensure_package(code, 'vi')  # silent if not available in repo

            _argos_translator = argostranslate.translate
            return _argos_translator

        except Exception as e:
            logger.exception(f"Argos Translate init error: {e}")
            return None

class HanVietDict:
    """Han-Viet dictionary for character-by-character conversion"""
    
    def __init__(self):
        self.char_to_hanviet = {}
        self._load_data()
    
    def _load_data(self):
        """Load Han-Viet data from CSV files"""
        data_dir = Path(__file__).parent / "data"
        
        # Primary source: sinov_readings.csv (format: 汉字,漢越語,IPA)
        sinov_path = data_dir / "sinov_readings.csv"
        if sinov_path.exists():
            try:
                with open(sinov_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip header
                    for row in reader:
                        if len(row) >= 2:
                            char, hanviet = row[0], row[1]
                            if char and hanviet:
                                if char not in self.char_to_hanviet:
                                    self.char_to_hanviet[char] = []
                                if hanviet not in self.char_to_hanviet[char]:
                                    self.char_to_hanviet[char].append(hanviet)
            except Exception as e:
                print(f"Error loading sinov_readings.csv: {e}")
        
        # Secondary source: hanviet_pinyin.csv (format: char,hanviet,pinyin)
        hanviet_path = data_dir / "hanviet_pinyin.csv"
        if hanviet_path.exists():
            try:
                with open(hanviet_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip header
                    for row in reader:
                        if len(row) >= 2:
                            char = row[0]
                            # Parse hanviet list format: "['thượng']" or "['càn', 'kiền']"
                            try:
                                hanviet_list = ast.literal_eval(row[1])
                                if isinstance(hanviet_list, list):
                                    for hv in hanviet_list:
                                        if char not in self.char_to_hanviet:
                                            self.char_to_hanviet[char] = []
                                        # Capitalize first letter
                                        hv_cap = hv.capitalize()
                                        if hv_cap not in self.char_to_hanviet[char]:
                                            self.char_to_hanviet[char].append(hv_cap)
                            except:
                                pass
            except Exception as e:
                print(f"Error loading hanviet_pinyin.csv: {e}")
        
        print(f"Loaded {len(self.char_to_hanviet)} Han-Viet characters")
    
    def get(self, char):
        """Get Han-Viet reading(s) for a character"""
        # 1. Direct lookup
        if char in self.char_to_hanviet:
            return self.char_to_hanviet[char]
        
        # 2. Try converting Simplified -> Traditional
        try:
            from zhconv import convert
            trad_char = convert(char, 'zh-hant')
            if trad_char != char and trad_char in self.char_to_hanviet:
                return self.char_to_hanviet[trad_char]
        except ImportError:
            pass
            
        return None

# Global dictionary instance
_hanviet_dict = None

def _get_hanviet_dict():
    global _hanviet_dict
    if _hanviet_dict is None:
        _hanviet_dict = HanVietDict()
    return _hanviet_dict


def get_pinyin(text: str, style='tone') -> str:
    """
    Convert Chinese text to Pinyin.
    
    Args:
        text: Chinese text
        style: 'tone' (with tone marks) or 'number' (with tone numbers)
    
    Returns:
        Pinyin string
    """
    pypinyin = _get_pypinyin()
    if pypinyin is None:
        return ""
    
    if style == 'tone':
        result = pypinyin.lazy_pinyin(text, style=pypinyin.Style.TONE)
    else:
        result = pypinyin.lazy_pinyin(text, style=pypinyin.Style.TONE3)
    
    return ' '.join(result)


def convert_script(text: str, to_variant: str = 'simplified') -> str:
    """
    Convert Chinese text between Simplified and Traditional.
    Args:
        text: Input text
        to_variant: 'simplified' (zh-hans) or 'traditional' (zh-hant)
    """
    if not text:
        return ""
        
    try:
        from zhconv import convert
        if to_variant == 'traditional':
            return convert(text, 'zh-hant')
        else:
            return convert(text, 'zh-hans')
    except ImportError:
        return text



def get_hanviet(text: str) -> str:
    """
    Convert Chinese text to Han-Viet (Sino-Vietnamese).
    
    Args:
        text: Chinese text
    
    Returns:
        Han-Viet string
    """
    dict_obj = _get_hanviet_dict()
    result = []
    
    for char in text:
        readings = dict_obj.get(char)
        if readings:
            # Use first reading, capitalize
            result.append(readings[0])
        elif char.isspace():
            result.append(' ')
        elif ord(char) >= 0x4E00 and ord(char) <= 0x9FFF:
            # Unknown CJK character
            result.append(f'[{char}]')
        else:
            # Non-Chinese character, keep as-is
            result.append(char)
    
    return ' '.join(result)


@lru_cache(maxsize=256)
def get_translations(text: str, source_lang: str = 'chinese') -> dict:
    """
    Translate text to English and Vietnamese.
    Returns dict: {'english': str, 'vietnamese': str}

    Improvement #4: Tries a direct source->vi Argos package first (1 step).
    Falls back to the classic source->en->vi chain if not available.
    """
    results = {'english': '', 'vietnamese': ''}
    
    if not text:
        return results

    # Determine source code
    if source_lang == 'chinese': src_code = 'zh'
    elif source_lang == 'japanese': src_code = 'ja'
    elif source_lang == 'korean': src_code = 'ko'
    else: src_code = 'zh'

    try:
        at = _get_argos_translator(source_lang)
        if at:
            # Check if a direct src->vi package is installed
            import argostranslate.package
            installed = argostranslate.package.get_installed_packages()
            has_direct = any(
                p.from_code == src_code and p.to_code == 'vi'
                for p in installed
            )

            if has_direct:
                # One-step: source -> vi directly
                vi_text = at.translate(text, src_code, 'vi')
                # Also get English via the normal route
                en_text = at.translate(text, src_code, 'en')
                print(f"[Translate] Direct {src_code}->vi used")
            else:
                # Two-step fallback: source -> en -> vi
                en_text = at.translate(text, src_code, 'en')
                vi_text = at.translate(en_text, 'en', 'vi')

            results['english'] = en_text
            results['vietnamese'] = vi_text

    except Exception as e:
        results['english'] = f'(Error: {e})'
        results['vietnamese'] = f'(Error: {e})'
        
    return results


def translate_online(text: str) -> dict:
    """
    Translate text using Google Translate API (Online).
    Returns dict: {'english': str, 'vietnamese': str}
    
    Improved: Uses googletrans library for better quality translations
    with post-processing for more natural Vietnamese output.
    """
    results = {'english': '', 'vietnamese': ''}

    if not text:
        return results

    def _google_translate_v2(query, dest):
        """Use googletrans library (better quality)"""
        try:
            from googletrans import Translator
            translator = Translator()
            result = translator.translate(query, dest=dest, src='zh-cn')
            return result.text
        except ImportError:
            logger.warning("googletrans not installed, falling back to translate library")
            return None
        except Exception as e:
            logger.warning(f"googletrans error: {e}")
            return None
    
    def _translate_fallback(query, dest):
        """Fallback to translate library"""
        try:
            from translate import Translator
            translator = Translator(to_lang=dest, from_lang='zh')
            return translator.translate(query)
        except Exception as e:
            logger.warning(f"Translate library error ({dest}): {e}")
            return None

    def _post_process_vietnamese(text):
        """Post-process Vietnamese translation for better quality"""
        if not text:
            return text
        
        # Fix common translation issues
        replacements = {
            'Tôi là': 'Tôi là',
            'rất tốt': 'rất tốt',
            'cảm thấy': 'cảm thấy',
            'làm việc': 'làm việc',
            'học tập': 'học tập',
            'người Trung Quốc': 'người Trung Quốc',
            'tiếng Trung': 'tiếng Trung',
            'ngày mai': 'ngày mai',
            'hôm nay': 'hôm nay',
            'xin chào': 'xin chào',
            'tạm biệt': 'tạm biệt',
            'cảm ơn': 'cảm ơn',
            'đồng ý': 'đồng ý',
            'không biết': 'không biết',
            'có thể': 'có thể',
            'muốn': 'muốn',
            'thích': 'thích',
            'đang': 'đang',
            'đã': 'đã',
            'sẽ': 'sẽ',
        }
        
        # Apply replacements
        processed = text
        for old, new in replacements.items():
            processed = processed.replace(old, new)
        
        # Fix spacing issues
        processed = ' '.join(processed.split())
        
        return processed

    # Run EN and VI requests in parallel (cuts wait time in half)
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def translate_task(lang):
        if lang == 'en':
            result = _google_translate_v2(text, 'en')
            if not result:
                result = _translate_fallback(text, 'en')
            return result
        else:  # vi
            result = _google_translate_v2(text, 'vi')
            if not result:
                result = _translate_fallback(text, 'vi')
            if result:
                result = _post_process_vietnamese(result)
            return result
    
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_en = pool.submit(translate_task, 'en')
            fut_vi = pool.submit(translate_task, 'vi')
            en = fut_en.result(timeout=10)
            vi = fut_vi.result(timeout=10)

        if en: 
            results['english'] = en
        if vi: 
            results['vietnamese'] = vi

    except Exception as e:
        logger.warning(f"Online translation failed: {e}")
        # Try deep-translator as last resort
        try:
            from deep_translator import GoogleTranslator
            results['english'] = GoogleTranslator(source='zh', target='en').translate(text)
            results['vietnamese'] = GoogleTranslator(source='zh', target='vi').translate(text)
        except Exception as fallback_error:
            logger.error(f"All translation methods failed: {fallback_error}")

    return results


def translate_all(text: str) -> dict:
    """
    Translate Chinese text and return all outputs.
    Uses concurrent execution for maximum performance.
    
    Args:
        text: Chinese text
    
    Returns:
        dict with keys: original, hanviet, pinyin, english, vietnamese
    """
    if not text:
        return {
            'original': '',
            'hanviet': '',
            'pinyin': '',
            'english': '',
            'vietnamese': ''
        }
    
    # Run all translations concurrently
    result = {'original': text}
    
    # Submit all tasks to thread pool
    futures = {
        'hanviet': _executor.submit(get_hanviet, text),
        'pinyin': _executor.submit(get_pinyin, text),
        'translations': _executor.submit(get_translations, text),
    }
    
    # Collect results as they complete
    for key, future in futures.items():
        try:
            if key == 'translations':
                translations = future.result(timeout=30)
                result['english'] = translations['english']
                result['vietnamese'] = translations['vietnamese']
            else:
                result[key] = future.result(timeout=10)
        except Exception as e:
            if key == 'translations':
                result['english'] = f'(Lỗi: {e})'
                result['vietnamese'] = f'(Lỗi: {e})'
            else:
                result[key] = f'(Lỗi: {e})'
    
    return result


def preload_resources():
    """Pre-load all heavy resources in background for faster first translation."""
    def _preload():
        try:
            _get_pypinyin()
            _get_hanviet_dict()
            _get_argos_translator()
            print("All resources pre-loaded successfully!")
        except Exception as e:
            print(f"Preload error: {e}")
    
    threading.Thread(target=_preload, daemon=True).start()


# Quick test
if __name__ == "__main__":
    test_text = "你好世界"
    print(f"Input: {test_text}")
    print(f"All: {translate_all(test_text)}")

