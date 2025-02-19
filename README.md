# YouTubeTranscriber

這是一個使用 [OpenAI Whisper](https://github.com/openai/whisper) 與 GPT API（預設 GPT-4）來**自動轉錄並摘要/整理 YouTube 影片逐字稿**的程式。  
透過此工具，你可以：

- **下載** 指定 YouTube 影片的音訊  
- **使用 Whisper** 進行聽打與轉錄  
- **使用 GPT** 自動優化文字與生成議題時間軸  
- 將結果保存成多種格式（JSON、文字檔案、GPT 整理後的結果等）

---

## 功能特色

1. **音訊自動下載**：透過 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 下載最佳音訊並轉成 mp3。  
2. **支援多種 Whisper 模型**：可透過設定檔 (.env) 指定不同的模型大小（如 `tiny`, `base`, `small`, `medium`, `large`）。  
3. **自動偵測/選擇運算資源**：  
   - Apple MPS (Metal Performance Shaders)  
   - CUDA (NVIDIA GPU)  
   - CPU  
4. **GPT-4 整理優化**：將逐字稿段落化、語意通順化，同時生成議題時間軸。  
5. **多檔案輸出**：  
   - Whisper 的原始 JSON 結果  
   - 純文字逐字稿  
   - GPT 整理後的文字檔案  
   - GPT 生成的議題時間軸

---

## 系統需求

- Python 3.9+（建議使用 3.10 或以上）  
- ffmpeg（`yt-dlp` 下載 mp3 後需要此工具做音訊轉碼）  
- 建議使用 GPU 或 Apple Silicon (M1/M2) 以加速 Whisper 轉錄。若無 GPU 或 Apple Silicon，也可以使用 CPU（速度會較慢）。

---

## 安裝步驟

1. **下載或 Clone 此專案**  
   ```bash
   git clone <此專案的 GitHub 連結>
   cd <專案資料夾>

2. **準備 Python 虛擬環境（建議）**
   ```bash
   python -m venv venv
   source venv/bin/activate        # Mac/Linux
   # 若是 Windows：
   # venv\Scripts\activate

3. **安裝所需套件**
   ```bash
   pip install -r requirements.txt
  -	這會安裝 whisper, openai, yt-dlp, python-dotenv, torch 等依賴。
  -	請注意：若要使用 GPU (CUDA) 或 MPS，需要安裝對應的 torch 版本，請參考 PyTorch 官網 取得正確的安裝指令。

4. **設定 .env 檔案**
   -	在專案根目錄建立一個 .env 檔，或者複製 env.example（若有提供）為 .env。
   -	在 .env 檔內填入下列變數：
   ```bash
   OPENAI_API_KEY=你的OpenAI金鑰
   WHISPER_MODEL=small   # (可換成 tiny, base, medium, large 等)
   LANGUAGE=zh           # (預設中文轉錄，如需英文或其他語言可自行調整)

6. **確認ffmpeg安裝**
   - yt-dlp 在下載音訊後，需要透過 ffmpeg 進行轉檔。
   - 請確認系統可執行 ffmpeg 指令，若無請安裝：
    - macOS: brew install ffmpeg
    - Ubuntu/Debian: sudo apt-get install ffmpeg
    - Windows: 參考 FFmpeg 官網 的安裝教學

---

##使用方式

1. **執行Python腳本**
   ```bash
   python yttr.py ""<Youtube URL>""
    例如：
   python yttr.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


2.	**程式流程**
   - 讀取 .env 中的環境變數，包含 OpenAI API key。
   - 下載目標 YouTube 影片的音訊 (mp3 檔)。
   - 呼叫 Whisper 進行轉錄，產生逐字稿。
   - 呼叫 GPT-4 (或其他 GPT 模型) 進行文字優化與議題時間軸生成。
   - 所有輸出檔案會存放在 transcripts/ 資料夾下（依照影片標題建立子資料夾）。
	
 3.	**輸出內容說明**
    - whisper_raw_YYYYMMDD_HHMMSS.json：Whisper 的原始轉錄結果。
    - whisper_text_YYYYMMDD_HHMMSS.txt：Whisper 的純文字逐字稿。
    - gpt_transcript_YYYYMMDD_HHMMSS.txt：GPT 處理後的優化文稿。
    - gpt_topics_YYYYMMDD_HHMMSS.txt：GPT 依照時間戳自動生成的主題/議題清單。
