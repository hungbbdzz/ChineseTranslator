"""
build_exe.py — PyInstaller build script for ChineseTranslator
=============================================================
Usage:
    pip install pyinstaller
    python build_exe.py

Output: dist/ChineseTranslator.exe
"""

import os
import shutil
import sys
import PyInstaller.__main__

# ── Configuration ──────────────────────────────────────────────────────────────
APP_NAME   = "ChineseTranslator"
ENTRY      = "ChineseTranslator.py"
ICON       = None  # Set to "assets/icon.ico" if you have one

# Data files to bundle (source → destination inside the exe)
DATAS = [
    ("data/hanviet_pinyin.csv",  "data"),
    ("data/sinov_readings.csv",  "data"),
    ("compat_patch.py",          "."),
    ("i18n.py",                  "."),
]

# Modules that PyInstaller cannot auto-detect
HIDDEN_IMPORTS = [
    # Transformers / HuggingFace
    "transformers",
    "transformers.models.nllb",
    "sentencepiece",
    # Chinese tools
    "zhconv",
    "pypinyin",
    # TTS
    "pyttsx3.drivers",
    "pyttsx3.drivers.sapi5",
    # OCR
    "rapidocr_onnxruntime",
    # Tray
    "pystray",
    "PIL._tkinter_finder",
]

# ── Clean previous build ───────────────────────────────────────────────────────
print("🧹 Cleaning previous build artifacts...")
for folder in ("dist", "build", f"{APP_NAME}.spec"):
    if os.path.exists(folder):
        if os.path.isdir(folder):
            shutil.rmtree(folder)
        else:
            os.remove(folder)

# ── Assemble PyInstaller arguments ────────────────────────────────────────────
args = [
    ENTRY,
    f"--name={APP_NAME}",
    "--onefile",           # Single portable .exe
    "--windowed",          # No console window
    "--clean",             # Clean PyInstaller cache
    "--noconfirm",         # Overwrite without prompting
]

# Icon (optional)
if ICON and os.path.exists(ICON):
    args.append(f"--icon={ICON}")

# Data files
for src, dst in DATAS:
    if os.path.exists(src):
        args.append(f"--add-data={src};{dst}")
    else:
        print(f"  ⚠️  Skipping missing data: {src}")

# Hidden imports
for imp in HIDDEN_IMPORTS:
    args.append(f"--hidden-import={imp}")

# ── Run PyInstaller ────────────────────────────────────────────────────────────
print(f"\n🔨 Building {APP_NAME}.exe...")
print(f"   Entry: {ENTRY}")
print(f"   Mode:  One-file, windowed (no console)\n")

try:
    PyInstaller.__main__.run(args)
    exe_path = os.path.join("dist", f"{APP_NAME}.exe")
    size_mb  = os.path.getsize(exe_path) / (1024 * 1024) if os.path.exists(exe_path) else 0
    print(f"\n✅ Build complete!")
    print(f"   Output : dist/{APP_NAME}.exe")
    print(f"   Size   : {size_mb:.1f} MB")
    print(f"\n💡 Tip: To create a Windows installer, compile installer_script.iss with Inno Setup.")
except Exception as e:
    print(f"\n❌ Build failed: {e}", file=sys.stderr)
    sys.exit(1)
