<div align="center">

# 📖 Chinese Translator

**A powerful, hybrid Chinese translation desktop app for Windows**
*Translate Chinese to Vietnamese & English — offline-first, with smart OCR, handwriting input, and neural TTS.*

[![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green?logo=opensourceinitiative)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?logo=windows)](https://www.microsoft.com/windows)
[![Stars](https://img.shields.io/github/stars/hungbbdzz/ChineseTranslator?style=social)](https://github.com/hungbbdzz/ChineseTranslator/stargazers)
[![Issues](https://img.shields.io/github/issues/hungbbdzz/ChineseTranslator)](https://github.com/hungbbdzz/ChineseTranslator/issues)

<img width="635" height="615" alt="ChineseTranslator Screenshot" src="https://github.com/user-attachments/assets/5972dbaa-ed54-48da-b9f2-df82efebfa1f" />

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🀄 **5-Row Deep Translation** | Displays **Chinese · Sino-Vietnamese · Pinyin · English · Vietnamese** simultaneously |
| 📸 **Screen Capture OCR** | Press `Alt+X` anywhere (including fullscreen games) to freeze & crop any text |
| 🌐 **Hybrid Translation** | Instant offline result via HuggingFace NLLB, then seamlessly updated by Google Translate |
| ✍️ **Handwriting Pad** | Draw Chinese strokes with mouse — powered by Google Handwriting API |
| 💡 **Smart Suggestions** | Context-aware word predictions based on 10 real-life scenarios (shopping, travel, greetings…) |
| ⏱️ **Auto-Translate** | Automatically translates 2 seconds after you stop typing |
| 🔊 **Neural TTS** | Microsoft Edge TTS for natural-sounding voices; falls back to Windows SAPI5 offline |
| 📖 **Mini Dictionary** | Double-click any Chinese character to see radical, stroke count, compounds & example sentences |
| 📋 **Clipboard Monitor** | Auto-detects copied Chinese/Japanese/Korean text and pops up a translation instantly |
| 📜 **Translation History** | Stores up to 1,000 recent translations with search, favorites, export/import (JSON) |
| 🌍 **Bilingual UI** | Full **English / Vietnamese** interface — switchable live in Settings |
| 🔁 **Reverse Translation** | Type Vietnamese or English → converts back to Chinese characters |

---

## 🚀 Installation

### Requirements
- **Windows 10/11** (64-bit)
- **Python 3.10 – 3.12**

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/hungbbdzz/ChineseTranslator.git
cd ChineseTranslator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the app
python ChineseTranslator.py
```

> [!NOTE]
> **First launch:** The app will download the offline HuggingFace NLLB translation model (~2.4 GB). This only happens once — subsequent launches are instant.

> [!TIP]
> For the best OCR experience, optionally install **RapidOCR** via the in-app install button (⬇️) in the toolbar. The app works without it using a fallback engine.

---

## ⌨️ Hotkeys

| Shortcut | Action |
|---|---|
| `Alt + X` | Freeze screen → drag to select Chinese text → OCR & translate |
| `Ctrl + Shift + V` | Translate the current clipboard content immediately |
| `Double-click` on a character | Open Mini Dictionary popup |
| `Shift + Click ✖` | Force-quit the app (bypasses minimize-to-tray) |

---

## 🏗️ Architecture

The app is designed around a **low-latency, accuracy-fallback pipeline**:

```
User Input / Alt+X Hotkey
        │
        ▼
 ┌─────────────┐     ┌──────────────────────┐
 │  OCR Engine │────▶│  Image Preprocessing │
 │  RapidOCR   │     │  (upscale, contrast, │
 │  (ONNX)     │     │   sharpen for subtext)│
 └─────────────┘     └──────────────────────┘
        │
        ▼
 ┌──────────────────────────────────────────┐
 │         Translation Pipeline             │
 │                                          │
 │  Thread 1 (Instant):                     │
 │  • dict_data → Pinyin + Sino-Viet        │
 │  • HuggingFace NLLB → Vietnamese (fast)  │
 │                                          │
 │  Thread 2 (Background):                  │
 │  • Google Translate API → high-accuracy  │
 │    Vietnamese & English (updates UI 🌐)  │
 └──────────────────────────────────────────┘
        │
        ▼
 ┌─────────────────┐
 │  Neural TTS     │
 │  Edge TTS ───── fallback ──▶ pyttsx3     │
 └─────────────────┘
```

---

## 📁 Project Structure

```
ChineseTranslator/
│
├── ChineseTranslator.py    # Main GUI — Tkinter UI, events, tray icon, hotkeys
├── translator.py           # Core translation engine (offline NLLB + online Google)
├── ocr_capture.py          # Screen capture, image preprocessing & RapidOCR
├── handwriting.py          # Handwriting pad window & Google Handwriting API
├── smart_suggestions.py    # Context-aware suggestion engine (10 scenario groups)
├── dict_data.py            # Mini dictionary DB (radicals, compounds, examples)
├── i18n.py                 # Internationalization — English / Vietnamese strings
├── compat_patch.py         # PyInstaller compatibility patches
├── logger_utils.py         # Logging utilities
│
├── data/
│   ├── hanviet_pinyin.csv  # Sino-Vietnamese & Pinyin lookup table
│   └── sinov_readings.csv  # Supplementary Sino-Vietnamese readings
│
├── build_exe.py            # PyInstaller build script
├── installer_script.iss    # Inno Setup installer script
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Pytest & coverage configuration
├── RunTranslator.bat       # Windows startup batch launcher
└── config.json             # User preferences (auto-generated on first run)
```

---

## ⚙️ Configuration

The app auto-generates `config.json` on first run. You can edit it manually or use the in-app **Settings (⚙️)** dialog.

| Key | Type | Default | Description |
|---|---|---|---|
| `topmost` | bool | `true` | Keep window always on top |
| `show_chinese` | bool | `true` | Show Chinese row in results |
| `show_hanviet` | bool | `true` | Show Sino-Vietnamese row |
| `show_pinyin` | bool | `true` | Show Pinyin row |
| `show_english` | bool | `true` | Show English row |
| `show_vietnamese` | bool | `true` | Show Vietnamese row |
| `clipboard_monitor` | bool | `false` | Auto-translate copied Asian text |
| `quick_translate` | bool | `true` | Enable `Ctrl+Shift+V` hotkey |
| `translation_mode` | string | `"offline"` | `"offline"` (NLLB) or `"online"` (Google) |
| `app_language` | string | `"vi"` | UI language: `"vi"` or `"en"` |
| `chinese_script` | string | `"simplified"` | `"simplified"` or `"traditional"` |

---

## 🔨 Build (Standalone `.exe`)

Package the entire app into a single portable `.exe` with no Python required:

```bash
# Install PyInstaller
pip install pyinstaller

# Run the automated build script
python build_exe.py
```

> Output: `dist/ChineseTranslator.exe`

To create a Windows installer (`.exe` setup wizard), compile `installer_script.iss` with [Inno Setup](https://jrsoftware.org/isinfo.php):

```
Output: Output/ChineseTranslator_Setup.exe
```

---

## 🐛 Troubleshooting

**TTS not working / no sound:**
- Ensure you have an internet connection for Microsoft Edge TTS (Neural voices).
- Without internet, the app falls back to Windows SAPI5 voices automatically.
- Install the Windows Chinese Language Pack: *Settings → Time & Language → Language → Add Chinese (Simplified)*.

**Online translation returns empty or "Error":**
- Google Translate has rate limits. Wait a few seconds and retry, or switch to Offline mode.

**`pip install` fails:**
- Use Python **64-bit** version 3.10–3.12. Avoid 3.13+ (some ML deps not yet compatible).
- Try: `pip install --upgrade pip` first.

**OCR misses text in games:**
- Some anti-cheat systems block screen capture. Use the clipboard (`Ctrl+Shift+V`) method instead.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by [hungbbdzz](https://github.com/hungbbdzz)

*If this project helped you, please consider giving it a ⭐ on GitHub!*

</div>
