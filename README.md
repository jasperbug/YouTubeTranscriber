# YouTubeTranscriber

這是一個使用 [OpenAI Whisper](https://github.com/openai/whisper) 與 GPT API（預設 GPT-4O）來**自動轉錄並摘要/整理 YouTube 影片逐字稿**的程式。

透過此工具，你可以：
- **下載** 指定 YouTube 影片的音訊
- **使用 Whisper** 進行聽打與轉錄
- **使用 GPT** 自動優化文字與生成議題時間軸
- **輸出多種格式**（Whisper 原始 JSON、純文字稿、GPT 整理稿、主題時間軸）

## 功能特色

1. **音訊自動下載**：透過 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 下載最佳音訊並轉成 mp3。
2. **支援多種 Whisper 模型**：可透過設定檔 `.env` 指定模型大小（`tiny`, `base`, `small`, `medium`, `large` 等）。
3. **自動偵測運算資源**：可根據系統自動選擇 `MPS` (Apple GPU)、`CUDA` (NVIDIA GPU) 或 `CPU`。
4. **GPT-4 整理優化**：將逐字稿段落化、語意通順化，並同時生成主題時間軸。
5. **多檔案輸出**：
   - Whisper 原始 JSON
   - Whisper 純文字逐字稿
   - GPT 整理後的文字稿
   - GPT 生成的主題/議題時間軸

## 系統需求

- Python 3.9+（建議使用 3.10 或以上）
- ffmpeg（`yt-dlp` 下載 mp3 後需要此工具做音訊轉碼）
- 建議使用 GPU 或 Apple Silicon (M1/M2) 加速 Whisper。若無 GPU 或 Apple Silicon，也可使用 CPU（速度較慢）。

## 安裝步驟

1. **下載或 Clone 專案**
```bash
git clone https://github.com/jasperbug/youtube_video_transcription-analysis.git
cd youtube_video_transcription-analysis
```

2. **建立虛擬環境（建議）**
```bash
# 以 venv 為例
python -m venv venv
source venv/bin/activate  # Mac/Linux
# 若是 Windows：
# venv\Scripts\activate
```

3. **安裝所需套件**
```bash
pip install -r requirements.txt
```
若要使用 GPU 或 MPS，請確保安裝對應的 torch 版本，參考 PyTorch 官網調整安裝指令。

4. **設定 .env 檔案**
```bash
OPENAI_API_KEY=你的OpenAI金鑰
WHISPER_MODEL=small   # (可換成 tiny, base, medium, large 等)
LANGUAGE=zh           # (預設中文轉錄，也可改成 en, ja 等)
```
OPENAI_API_KEY 請至 [OpenAI 平台](https://platform.openai.com/) 申請並取得。

5. **確認 ffmpeg 安裝**
- yt-dlp 下載音訊後，會用 ffmpeg 轉為 mp3。
- 各平臺安裝方式：
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`
  - Windows: [FFmpeg 官網](https://ffmpeg.org/download.html) 下載並安裝

## 使用方式

1. **執行程式**
```bash
python yttr.py "<YouTube URL>"
```
例如：
```bash
python yttr.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

2. **程式流程**
- 讀取 .env 中的環境變數 (尤其是 OPENAI_API_KEY)
- 使用 yt-dlp 下載 YouTube 影片音訊並存成 mp3
- 呼叫 Whisper 進行轉錄，產生逐字稿 JSON 與文字檔
- 呼叫 GPT-4 進行文字優化、段落化與主題時間軸生成
- 輸出檔案儲存在 transcripts/ 下，以影片標題建立子資料夾

3. **輸出檔案說明**
- `whisper_raw_YYYYMMDD_HHMMSS.json`：Whisper 原始轉錄結果 (JSON)
- `whisper_text_YYYYMMDD_HHMMSS.txt`：Whisper 純文字逐字稿
- `gpt_transcript_YYYYMMDD_HHMMSS.txt`：GPT 整理後的內容
- `gpt_topics_YYYYMMDD_HHMMSS.txt`：GPT 依據時間戳產生的主題/議題清單

## 參數設定

| 環境變數 | 用途 | 預設值 | 說明 |
|----------|------|--------|------|
| OPENAI_API_KEY | OpenAI API 金鑰 | (無) | 必填，用於呼叫 GPT-4 或 GPT-3.5-turbo API |
| WHISPER_MODEL | Whisper 模型大小 | small | 可改為 tiny, base, medium, large 等模型 |
| LANGUAGE | Whisper 轉錄語言 | zh | 可改為 en, ja 或其他支援的語言 |

## 常見問題

1. **沒有使用 GPU？**
   - 程式會檢查 `torch.cuda.is_available()` 與 `torch.backends.mps.is_available()`
   - 若沒有偵測到可用 GPU / MPS，就會使用 CPU
   - 請在 [PyTorch 官網](https://pytorch.org/) 下載相符的 GPU/MPS 版本 torch

2. **GPT-4 沒法使用？**
   - 需要有 GPT-4 API 權限，且 .env 中 OPENAI_API_KEY 要正確填寫
   - 若無法使用 GPT-4，可嘗試改用 gpt-3.5-turbo

3. **下載音訊時出錯**
   - 可能是系統沒有安裝 ffmpeg 或網路連線問題
   - 某些地區可能需要科學上網來存取 YouTube

4. **轉錄速度很慢**
   - 建議使用 GPU (NVIDIA CUDA) 或 Apple Silicon (M1/M2) 等硬體加速
   - CPU 轉錄大檔案會需要較長時間

5. **進階用法**
   - 強制重新轉錄：預設若已存在同一影片的轉錄檔，程式會直接使用舊檔

## 聯絡方式

- 如果有任何問題或建議，歡迎在本專案的 Issues 中提出，或透過以下方式聯絡：
  - Twitch: [https://www.twitch.tv/buuuggyy](https://www.twitch.tv/buuuggyy)
  - Discord: 728961559208001588
