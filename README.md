# 📖 Chinese to Vietnamese Translator

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/hungbbdzz/ChineseTranslator/blob/main/LICENSE)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey?logo=windows)
[![Stars](https://img.shields.io/github/stars/hungbbdzz/ChineseTranslator?style=social)](https://github.com/hungbbdzz/ChineseTranslator/stargazers)

<img width="635" height="615" alt="{1B6C6297-037D-4248-831F-EEEF3C63A497}" src="https://github.com/user-attachments/assets/5972dbaa-ed54-48da-b9f2-df82efebfa1f" />


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
- **Gợi Ý Thông Minh & Điền Tự Động (Context-Aware Suggestions):** 
  - Dự đoán từ vựng dựa trên lịch sử gõ và 10 nhóm ngữ cảnh thực tế (Mua sắm, Chào hỏi, Đi lại...).
  - Tự động hiển thị các mẫu câu tình huống ngay khi ô nhập liệu trống.
- **Bảng Viết Tay (Handwriting Pad):** Tích hợp bảng vẽ nhận diện nét chữ Hán trực tiếp, hỗ trợ cuộn và chọn dự đoán chữ cái chính xác.
- **Tự Động Dịch (Auto-Translate Delay):** Ứng dụng tự động dịch văn bản ngay sau khi bạn dừng gõ 2 giây, giúp trải nghiệm rảnh tay và liền mạch.
- **Đọc Phát Âm (Neural TTS):** Sử dụng **Microsoft Edge TTS** (`edge-tts`) cho giọng đọc tự nhiên (Hán & Việt). Nếu mất mạng, hệ thống tự động fallback về giọng đọc offline của Windows (`pyttsx3`).
- **Từ Điển Mini:** Nhấp đúp chuột vào một ký tự tiếng Trung bất kỳ để tra bộ thủ, số nét, ví dụ từ ghép và câu mẫu.
- **Smart Clipboard Monitor:** Tự động phát hiện khi bạn copy văn bản chứa tiếng Trung/Nhật/Hàn và hiển thị ngay bản dịch.
- **Lưu Lịch Sử:** Lưu lại 1000 bản dịch gần nhất để bạn có thể xem lại, tìm kiếm hoặc xuất file JSON.

## 🚀 Cài Đặt (Installation)

Yêu cầu: **Python 3.10+**

1. Clone repository về máy:
   ```bash
   git clone https://github.com/hungbbdzz/ChineseTranslator.git
   cd ChineseTranslator
   ```

2. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```

3. Chạy ứng dụng:
   ```bash
   python ChineseTranslator.py
> [!NOTE]
> **Lần chạy đầu tiên:** Ứng dụng sẽ mất khoảng 1-2 phút để tải các mô hình dịch thuật ngoại tuyến (Argos Models) từ internet. Các lần chạy sau sẽ khởi động ngay lập tức.

## 🔄 Luồng Kiến Trúc Hoạt Động (Core Workflow)

Dự án được thiết kế với tư duy tối ưu hóa tốc độ phản hồi (low-latency) kết hợp độ chính xác cao (accuracy fallback):

1. **Trigger & Màn hình chờ (Screen Capture):** Người dùng kích hoạt chương trình bằng phím tắt toàn cục `Alt + X` hoặc `Ctrl + Shift + V`. App sẽ chụp và "đông cứng" ngay khung hình hiện tại trên màn hình hệ thống (kể cả game Fullscreen).
2. **Tiền xử lý (Image Preprocessing):** Vùng chữ được cắt ra sẽ đi qua lớp xử lý của Pillow. App sẽ phân tích kích thước; nếu là vùng chữ chữ nhỏ (như sub game), ảnh được upscale lên 2x (Lanzcos), kích 1.6x độ tương phản và 1.4x độ nét.
3. **Nhận diện (OCR Processing):** Ảnh tiền xử lý được đẩy vào engine `RapidOCR (ONNX)` (đã được cache sẵn trong RAM từ lúc khởi động). Quá trình xuất ra tiếng Trung mất chưa tới 0.1 giây.
4. **Dịch thuật song song (Multi-threaded Translation Pipeline):**
   - *Luồng 1 (Sync & Local):* Truy xuất CSDL `dict_data` cục bộ để tìm Pinyin và Hán Việt. Tiếp tục gọi mô hình `argostranslate` để dịch thô 1 bước `zh->vi` (hoặc `zh->en->vi`). Kết quả này được in ra màn hình **gần như ngay lập tức**.
   - *Luồng 2 (Async & Online):* Tạo một thread chạy ngầm gửi request tới API `Google Translate` thông qua thư viện `deep-translator`. Khi API trả về kết quả mang ngữ cảnh tốt hơn, chữ trên màn hình giao diện tự động được update (có check icon báo hiệu 🌐).
5. **Text-to-Speech (Fallback Mechanism):** Khi người dùng nhấn nút 🔊, hệ thống đẩy text vào hàng đợi lấy dữ liệu qua `edge-tts` (Microfot Neural Voices) cho giọng đọc mượt mà. Trong trường hợp rớt mạng, luồng `Catch (Exception)` sẽ đổi hướng dữ liệu chạy thẳng qua `pyttsx3` (SAPI5 offline).

## ⌨️ Phím Tắt Tiện Ích (Hotkeys)

- `Alt + X` : Chụp màn hình (đông cứng màn hình hiện tại) và quét OCR để dịch.
- `Ctrl + Shift + V` : Dịch nhanh văn bản vừa Copy trong Clipboard.
- `Shift + Click ✖ (Nút Close)` : Buộc ứng dụng tắt hoàn toàn ngay lập tức (bỏ qua thu nhỏ xuống khay hệ thống).
- Hiển thị bảng từ điển khi **Nhấp Đúp (Double Click)** vào một chữ Hán (ở dòng input hoặc kết quả).

## 🛠️ Cấu Trúc Dự Án (Project Structure)

- `ChineseTranslator.py`: Giao diện chính (GUI) và xử lý sự kiện (Tkinter, Hotkeys, Tray Icon).
- `ocr_capture.py`: Mudule chụp màn hình và trích xuất văn bản (OCR) bằng `rapidocr-onnxruntime`. Hỗ trợ chế độ chụp frozen-screen.
- `translator.py`: Module dịch chính, liên kết Pinyin, Hán Việt Offline và dịch đa tầng (Offline Argos / Online Deep-Translator).
- `handwriting.py`: Cửa sổ bảng viết tay, xử lý bắt nét chuột và gọi API Google Handwriting.
- `smart_suggestions.py`: Động cơ dự đoán từ và gợi ý câu giao tiếp thông minh dựa trên ngữ cảnh thực tế.
- `dict_data.py`: Cơ sở dữ liệu cho từ điển mini (bộ thủ, từ ghép, ví dụ).
- `compat_patch.py`: Chứa các bản vá tương thích (compatibility patches) chống lỗi khi compile bằng PyInstaller.
- `data/`: Thư mục chứa từ điển Hán Việt (`sinov_readings.csv`, `hanviet_pinyin.csv`).

## ⚠️ Khắc phục sự cố (Troubleshooting)

- **Lỗi không phát âm được (TTS Error):**
  - Đảm bảo bạn có kết nối mạng để sử dụng giọng đọc Neural chất lượng cao. Nếu không, app sẽ dùng giọng đọc có sẵn của Windows.
  - Hãy kiểm tra Windows của bạn đã cài đặt gói ngôn ngữ tiếng Trung (Chinese Language Pack) trong Settings > Time & Language.
- **Dịch Online thỉnh thoảng hiện "Error" hoặc rỗng:**
  - Google/Deep-Translator giới hạn số lượng request. Hãy đợi vài giây và thử lại.
- **Lỗi khi cài đặt thư viện (`pip install`):**
  - Đảm bảo bạn đang sử dụng Python bản 64-bit (phiên bản 3.10 đến 3.12 là ổn định nhất).

## ⚙️ Đóng gói thành `.exe` (Build)

Bạn có thể đóng gói toàn bộ tool này thành 1 file `.exe` độc lập không cần cài Python bằng PyInstaller.

```bash
pip install pyinstaller
python build_exe.py
```
File thực thi cuối cùng sẽ được tạo ở thư mục `dist/`.

## 🤝 Giấy phép (License)
MIT License.
