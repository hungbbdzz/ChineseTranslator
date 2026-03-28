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
_hf_translator = None
_init_lock = threading.Lock()

def _get_pypinyin():
    global _pypinyin
    if _pypinyin is None:
        import pypinyin
        _pypinyin = pypinyin
    return _pypinyin

def _get_hf_translator():
    """Initialize Hugging Face Transformers model for Chinese -> Vietnamese translation (thread-safe)
    
    Uses Meta's NLLB (No Language Left Behind) - high-quality multilingual model.
    Model: facebook/nllb-200-distilled-600M (~2.4GB, best quality for zh->vi)
    """
    global _hf_translator
    
    with _init_lock:
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            
            if _hf_translator is None:
                logger.info("Loading NLLB model: facebook/nllb-200-distilled-600M...")
                
                model_name = "facebook/nllb-200-distilled-600M"
                tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang="zho_Hans")
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                
                _hf_translator = {
                    'tokenizer': tokenizer,
                    'model': model,
                    'src_lang': 'zho_Hans',  # Chinese Simplified
                    'tgt_lang': 'vie_Latn'   # Vietnamese
                }
                logger.info("NLLB model loaded successfully!")
            
            return _hf_translator
            
        except Exception as e:
            logger.exception(f"Hugging Face translator init error: {e}")
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

    Uses NLLB for direct Chinese -> Vietnamese translation (highest quality).
    English translation is handled separately by translate_online() using Google Translate.
    """
    import torch

    results = {'english': '', 'vietnamese': ''}

    if not text:
        return results

    try:
        # Use NLLB for direct Chinese -> Vietnamese translation
        hf_data = _get_hf_translator()
        if hf_data:
            tokenizer = hf_data['tokenizer']
            model = hf_data['model']
            src_lang = hf_data['src_lang']
            tgt_lang = hf_data['tgt_lang']

            # Tokenize with source language and target language hint
            tokenizer.src_lang = src_lang
            inputs = tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            input_length = inputs['input_ids'].shape[1]
            
            # Find the target language token in special tokens
            vie_token = f"__{tgt_lang}__"
            special_tokens = tokenizer.additional_special_tokens
            if vie_token in special_tokens:
                tgt_token_id = tokenizer.convert_tokens_to_ids(vie_token)
            else:
                # Fallback: search for token containing 'vie'
                vie_token = next((t for t in special_tokens if 'vie' in t), None)
                if vie_token:
                    tgt_token_id = tokenizer.convert_tokens_to_ids(vie_token)
                else:
                    tgt_token_id = None

            # Generate translation
            with torch.no_grad():
                if tgt_token_id:
                    outputs = model.generate(
                        **inputs,
                        forced_bos_token_id=tgt_token_id,
                        max_length=min(input_length * 3, 512),
                        num_beams=5,
                        length_penalty=2.0,
                        early_stopping=False,
                    )
                else:
                    # No target token found, generate without language forcing
                    outputs = model.generate(
                        **inputs,
                        max_length=min(input_length * 3, 512),
                        num_beams=5,
                        length_penalty=2.0,
                    )

            # Decode result
            vietnamese = tokenizer.decode(outputs[0], skip_special_tokens=True)
            results['vietnamese'] = vietnamese
            logger.info(f"[Translate] NLLB Direct zh->vi used (input_tokens={input_length})")

        # Note: English translation is handled separately by translate_online()
        # which uses Google Translate API.

    except Exception as e:
        logger.exception(f"NLLB Translation error: {e}")
        results['vietnamese'] = f'(Error: {e})'

    return results


def translate_online(text: str) -> dict:
    """
    Translate text using Google Translate API (Online).
    Returns dict: {'english': str, 'vietnamese': str}
    """
    results = {'english': '', 'vietnamese': ''}

    if not text:
        return results

    def _google_translate_v2(query, dest):
        try:
            from googletrans import Translator
            translator = Translator()
            result = translator.translate(query, dest=dest, src='zh-cn')
            return result.text
        except ImportError:
            return None
        except Exception as e:
            logger.debug(f"googletrans error: {e}")
            return None
    
    def _translate_fallback(query, dest):
        try:
            from translate import Translator
            translator = Translator(to_lang=dest, from_lang='zh')
            return translator.translate(query)
        except ImportError:
            return None
        except Exception as e:
            logger.debug(f"Translate library error ({dest}): {e}")
            return None

    def _deep_translator_fallback(query, dest):
        try:
            from deep_translator import GoogleTranslator
            return GoogleTranslator(source='zh', target=dest).translate(query)
        except Exception as e:
            logger.debug(f"deep_translator error ({dest}): {e}")
            return None

    def _post_process_vietnamese(text):
        if not text: return text
        replacements = {'Tôi là': 'Tôi là', 'rất tốt': 'rất tốt'}
        processed = text
        for old, new in replacements.items():
            processed = processed.replace(old, new)
        return ' '.join(processed.split())

    def translate_task(lang):
        result = _google_translate_v2(text, lang)
        if not result:
            result = _translate_fallback(text, lang)
        if not result:
            result = _deep_translator_fallback(text, lang)
            
        if lang == 'vi' and result:
            result = _post_process_vietnamese(result)
        return result
    
    try:
        # submit to global executor to avoid blocking on local threadpool shutdown 
        fut_en = _executor.submit(translate_task, 'en')
        fut_vi = _executor.submit(translate_task, 'vi')
        
        en = None
        vi = None
        
        try:
            en = fut_en.result(timeout=10)
        except Exception as e:
            logger.debug(f"Timeout or error getting EN translation: {e}")
            
        try:
            vi = fut_vi.result(timeout=10)
        except Exception as e:
            logger.debug(f"Timeout or error getting VI translation: {e}")

        if en: results['english'] = en
        if vi: results['vietnamese'] = vi

    except Exception as e:
        logger.error(f"All translation methods failed: {e}")

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


def detect_input_language(text: str) -> str:
    """
    Detect if input text is Chinese or other language.
    Returns: 'chinese' | 'other'
    """
    if not text:
        return 'other'
    
    chinese_count = sum(
        1 for char in text
        if '\u4e00' <= char <= '\u9fff'
        or '\u3400' <= char <= '\u4dbf'  # CJK Extension A
        or '\uf900' <= char <= '\ufaff'  # CJK Compatibility
    )
    
    # Nếu > 30% ký tự là chữ Hán → coi là Chinese input
    non_space = len([c for c in text if not c.isspace()])
    if non_space == 0:
        return 'other'
    ratio = chinese_count / non_space
    return 'chinese' if ratio >= 0.3 else 'other'


def translate_to_chinese(text: str) -> dict:
    """
    Dịch văn bản (tiếng Việt/Anh/v.v.) sang tiếng Trung (Giản thể) và English.
    Returns: {'chinese': str, 'english': str}
    """
    result = {'chinese': '', 'english': ''}
    
    if not text:
        return result

    def _to_chinese(query):
        """Cố thử nhiều language code cho tiếng Trung giản thể"""
        # googletrans v4 codes
        for zh_code in ['zh-cn', 'zh-CN', 'zh']:
            try:
                from googletrans import Translator
                t = Translator()
                r = t.translate(query, dest=zh_code, src='auto')
                if r and r.text:
                    return r.text
            except Exception:
                pass
        # deep_translator fallback
        for zh_code in ['zh-CN', 'chinese (simplified)', 'zh']:
            try:
                from deep_translator import GoogleTranslator
                r = GoogleTranslator(source='auto', target=zh_code).translate(query)
                if r:
                    return r
            except Exception:
                pass
        return None

    def _to_english(query):
        try:
            from googletrans import Translator
            r = Translator().translate(query, dest='en', src='auto')
            if r and r.text:
                return r.text
        except Exception:
            pass
        try:
            from deep_translator import GoogleTranslator
            return GoogleTranslator(source='auto', target='en').translate(query)
        except Exception:
            pass
        return None

    try:
        fut_zh = _executor.submit(_to_chinese, text)
        fut_en = _executor.submit(_to_english, text)

        chinese = None
        english = None
        try:
            chinese = fut_zh.result(timeout=12)
        except Exception as e:
            logger.debug(f"translate_to_chinese zh error: {e}")
        try:
            english = fut_en.result(timeout=10)
        except Exception as e:
            logger.debug(f"translate_to_chinese en error: {e}")

        if chinese:
            result['chinese'] = chinese
        if english:
            result['english'] = english
    except Exception as e:
        logger.error(f"translate_to_chinese error: {e}")

    return result


def preload_resources():

    """Pre-load all heavy resources at startup (blocking, ensures model is ready)."""
    try:
        print("[Preload] Loading pypinyin...")
        _get_pypinyin()
        print("[Preload] Loading Han-Viet dictionary...")
        _get_hanviet_dict()
        print("[Preload] Loading NLLB translation model (this may take 1-2 minutes)...")
        _get_hf_translator()
        print("[Preload] ✅ All resources loaded successfully!")
    except Exception as e:
        print(f"[Preload] ❌ Error: {e}")


# Quick test
if __name__ == "__main__":
    test_text = "你好世界"
    print(f"Input: {test_text}")
    print(f"All: {translate_all(test_text)}")

