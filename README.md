# 📖 Chinese to Vietnamese Translator

A lightweight, hybrid (Offline + Online) Chinese to Vietnamese translation tool built with Python and Tkinter. This tool is optimized for reading Chinese materials, playing games (with a frozen-screen OCR feature), and quick lookups.

It runs locally with high-quality TTS and fallback mechanisms, ensuring a seamless experience even without an internet connection.

## 🌟 Tóm Tắt Tính Năng (Features)

- **Dịch 5 Dòng Chuyên Sâu:** Hiển thị đồng thời **Hán Tự**, **Hán Việt**, **Pinyin**, **English**, và **Tiếng Việt**.
- **Chụp Màn Hình & Tách Chữ (OCR) dùng Phím Tắt:** 
  - Nhấn `Alt + X` ở bất kỳ đâu (kể cả trong game Fullscreen).
  - Màn hình sẽ "đông cứng" ngay lập tức để bạn kéo chọn phân vùng chứa chữ tiếng Trung.
  - Sử dụng module **RapidOCR (ONNX)** siêu nhẹ và chính xác, không cần cài đặt Tesseract lằng nhằng.
- **Dịch Hybrid (Ngoại Tuyến + Trực Tuyến):** 
  - Dịch **Offline ngay lập tức** bằng thư viện `argostranslate` (đảm bảo phản hồi nhanh, không độ trễ).
  - Tự động lấy kết quả từ **Google Translate API** để bổ sung ngữ cảnh chính xác ở chế độ nền.
- **Đọc Phát Âm (Neural TTS):** Sử dụng **Microsoft Edge TTS** (`edge-tts`) cho giọng đọc tự nhiên (Hán & Việt). Nếu mất mạng, hệ thống tự động fallback về giọng đọc offline của Windows (`pyttsx3`).
- **Từ Điển Mini:** Nhấp đúp chuột vào một ký tự tiếng Trung bất kỳ để tra bộ thủ, số nét, ví dụ từ ghép và câu mẫu.
- **Smart Clipboard Monitor:** Tự động phát hiện khi bạn copy văn bản chứa tiếng Trung/Nhật/Hàn và hiển thị ngay bản dịch.
- **Lưu Lịch Sử:** Lưu lại 1000 bản dịch gần nhất để bạn có thể xem lại, tìm kiếm hoặc xuất file JSON.

## 🚀 Cài Đặt (Installation)

Yêu cầu: **Python 3.10+**

1. Clone repository về máy:
   ```bash
   git clone https://github.com/your-username/chinese-translator.git
   cd chinese-translator
   ```

2. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```

3. Chạy ứng dụng:
   ```bash
   python ChineseTranslator.py
   ```
   *(Hoặc chạy file `RunTranslator.bat` trên Windows)*

## ⌨️ Phím Tắt Tiện Ích (Hotkeys)

- `Alt + X` : Chụp màn hình (đông cứng màn hình hiện tại) và quét OCR để dịch.
- `Ctrl + Shift + V` : Dịch nhanh văn bản vừa Copy trong Clipboard.
- Hiển thị bảng từ điển khi **Nhấp Đúp (Double Click)** vào một chữ Hán (ở dòng input hoặc kết quả).

## 🛠️ Cấu Trúc Dự Án (Project Structure)

- `ChineseTranslator.py`: Giao diện chính (GUI) và xử lý sự kiện (Tkinter, Hotkeys, Tray Icon).
- `ocr_capture.py`: Mudule chụp màn hình và trích xuất văn bản (OCR) bằng `rapidocr-onnxruntime`. Hỗ trợ chế độ chụp frozen-screen.
- `translator.py`: Module dịch chính, liên kết Pinyin, Hán Việt Offline và dịch đa tầng (Offline Argos / Online Deep-Translator).
- `dict_data.py`: Cơ sở dữ liệu cho từ điển mini (bộ thủ, từ ghép, ví dụ).
- `compat_patch.py`: Chứa các bản vá tương thích (compatibility patches) chống lỗi khi compile bằng PyInstaller.
- `data/`: Thư mục chứa từ điển Hán Việt (`sinov_readings.csv`, `hanviet_pinyin.csv`).

## ⚙️ Đóng gói thành `.exe` (Build)

Bạn có thể đóng gói toàn bộ tool này thành 1 file `.exe` chạy độc lập bằng PyInstaller.

```bash
pip install pyinstaller
python build_exe.py
```
File thực thi cuối cùng sẽ được tạo ở thư mục `dist/`.

## 🤝 Giấy phép (License)
MIT License.
