import sys
import typing

def apply_patch():
    """
    Monkey patch typing.ForwardRef._evaluate for Python 3.12.4+ compatibility.
    Fixes 'missing 1 required keyword-only argument: recursive_guard' error 
    seen in libraries like pydantic v1, thinc, spacy, etc.
    """
    if sys.version_info < (3, 12, 4):
        # Even if version is older, we still want the subprocess patch
        apply_subprocess_patch()
        return

    try:
        # Check if already patched
        if hasattr(typing.ForwardRef, "_cortex_patched"):
            return

        print(f"Applying Python {sys.version} compatibility patch for ForwardRef._evaluate...")
        
        _original_evaluate = typing.ForwardRef._evaluate
        
        # Use *args and **kwargs to be safe against different call signatures
        def _patched_evaluate(self, globalns, localns, *args, **kwargs):
            # Python 3.12.4+ requires recursive_guard as keyword-only argument
            # If it's missing (legacy call), add it.
            if 'recursive_guard' not in kwargs:
                kwargs['recursive_guard'] = frozenset()
                
            return _original_evaluate(self, globalns, localns, *args, **kwargs)
        
        typing.ForwardRef._evaluate = _patched_evaluate
        typing.ForwardRef._cortex_patched = True
        print("Patch applied successfully.")

        
        # Also apply subprocess patch
        apply_subprocess_patch()
        
    except Exception as e:
        print(f"Failed to apply patch: {e}")

def apply_subprocess_patch():
    """
    Monkey patch subprocess.Popen to hide console windows on Windows.
    This prevents flashing terminal windows when running external commands like Tesseract.
    """
    if sys.platform != 'win32':
        return

    import subprocess
    
    # Check if already patched to avoid recursion/duplication
    if getattr(subprocess.Popen, '_cortex_patched', False):
        return

    print("Applying subprocess.Popen patch for hidden console windows...")
    
    _original_Popen = subprocess.Popen

    class PatchedPopen(_original_Popen):
        def __init__(self, *args, **kwargs):
            # Force CREATE_NO_WINDOW
            # 0x08000000 is CREATE_NO_WINDOW
            CREATE_NO_WINDOW = 0x08000000
            
            # Update creationflags
            current_flags = kwargs.get('creationflags', 0)
            kwargs['creationflags'] = current_flags | CREATE_NO_WINDOW
            
            # Also set STARTUPINFO as a backup method
            if 'startupinfo' not in kwargs:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                kwargs['startupinfo'] = startupinfo
            
            super().__init__(*args, **kwargs)

    subprocess.Popen = PatchedPopen
    subprocess.Popen._cortex_patched = True
    print("Subprocess patch applied (with CREATE_NO_WINDOW).")

if __name__ == "__main__":
    apply_patch()
    apply_subprocess_patch()
