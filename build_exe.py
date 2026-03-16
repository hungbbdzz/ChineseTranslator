import PyInstaller.__main__
import os
import shutil

# 1. Clean previous build
if os.path.exists('dist'): shutil.rmtree('dist')
if os.path.exists('build'): shutil.rmtree('build')

# 2. Define data to include
# Format: 'source;dest' (Windows)
datas = [
    ('data/hanviet_pinyin.csv', 'data'),
    ('compat_patch.py', '.'),
    # Note: Argos models are stored in user config, so we let app download them naturally
    # or we could bundle them if paths were local.
]

# Convert datas to list of string arguments
add_data_args = []
for src, dst in datas:
    add_data_args.append(f'--add-data={src};{dst}')

# 3. Hidden imports required for argostranslate/pyinstaller logic
hidden_imports = [
    'argostranslate',
    'argostranslate.translate',
    'argostranslate.package',
    'argostranslate.argospm',
    'zhconv',
    'pyttsx3.drivers',
    'pyttsx3.drivers.sapi5',
]

hidden_import_args = []
for imp in hidden_imports:
    hidden_import_args.append(f'--hidden-import={imp}')

# 4. Run PyInstaller
args = [
    'ChineseTranslator.py',
    '--name=ChineseTranslator',
    '--onefile',
    '--windowed',  # No console window
    '--clean',
    *add_data_args,
    *hidden_import_args,
]

print("Building EXE with args:", args)
PyInstaller.__main__.run(args)

print("\n✅ Build completed! Check 'dist/ChineseTranslator.exe'")
