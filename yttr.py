import os
import sys
import whisper
import openai
import json
from datetime import datetime
from dotenv import load_dotenv
import yt_dlp
from pathlib import Path
import torch
import torch.backends.mps

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import threading
from functools import wraps
from tkinter import scrolledtext

# 用於將系統文字重寫到UI上
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget
    # TODO 要解決可能會被打字的問題(這是問題嗎?感覺問題也不大)
    def write(self, text):
        self.widget.config(state="normal")
        self.widget.insert(tk.END, text)
        self.widget.config(state="disabled")
        self.widget.see(tk.END)  # 自動滾動到最新輸出

    def flush(self):
        pass  # 為了兼容 sys.stdout，不做任何操作
    
class tk_ui:
    def __init__(self,width = 1200,height = 800):
        # 載入 .env 檔案
        load_dotenv()
        self.width = width
        self.height = height

        
        # 設置 OpenAI API key
        self.api_key = os.getenv('OPENAI_API_KEY')
        # 從 .env 讀取其他設定
        self.whisper_model = os.getenv('WHISPER_MODEL', 'small')
        self.language = os.getenv('LANGUAGE', 'zh')
        self.output_path = os.path.abspath(os.getenv('OUTPUT_PATH', './transcripts'))

    def bulid_ui(self):
        # UI 視窗設定
        windows = tk.Tk()
        windows.title('時間軸小幫手')
        windows.geometry(f'{self.width}x{self.height}') 
        windows.resizable(False, True)

        # 讓第一行與第三行可以隨著窗口大小擴展
        windows.grid_columnconfigure(0, weight=1)
        windows.grid_rowconfigure(3, weight=1)



#OpenAI API 設置
    # 外框
    
        api_key_labelframe = tk.LabelFrame(windows, text='OpenAI API 設置', padx=10, pady=10)
        api_key_labelframe.grid(row=0, column=0, padx=10, pady=10, sticky="ew")


    # API Key
        #文字
        tk.Label(api_key_labelframe, text='API Key:').grid(row=0, column=0, sticky='w', pady=2) 

        #輸入框
        self.api_key_input = tk.Entry(api_key_labelframe, width=60, show='*')
        self.api_key_input.insert(0, self.api_key)
        self.api_key_input.grid(row=0, column=1, sticky='w', padx=5)

        #顯示按鈕
        self.api_key_button = tk.Button(api_key_labelframe, text='顯示', padx=30, command=self.toggle_password)
        self.api_key_button.grid(row=0, column=2, padx=5)

    #語言
        #預設列表
        language_list = ['zh','en',]

        #文字
        tk.Label(api_key_labelframe, text='語言:').grid(row=1, column=0, sticky='w', pady=2)

        #下拉選單
        self.language_label_input = ttk.Combobox(api_key_labelframe, values=language_list, width=10)
        self.language_label_input.grid(row=1, column=1, sticky='w', padx=5)
        self.language_label_input.set(self.language)

#YouTube 影片設置      
    # 外框  
        youtube_input_labelframe = tk.LabelFrame(windows, text='YouTube 影片設置', padx=10, pady=10)
        youtube_input_labelframe.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

    #URL
        #文字
        tk.Label(youtube_input_labelframe, text='URL:').grid(row=0, column=0, sticky='w', pady=2)

        #輸入框
        self.youtube_url_input = tk.Entry(youtube_input_labelframe, width=100)
        self.youtube_url_input.grid(row=0, column=1, sticky='w', padx=5)

    #輸出目錄
        #文字
        tk.Label(youtube_input_labelframe, text='輸出目錄:').grid(row=1, column=0, sticky='w', pady=2)

        #輸入框
        self.output_path_input = tk.Entry(youtube_input_labelframe, width=100)
        self.output_path_input.insert(0, self.output_path)
        self.output_path_input.grid(row=1, column=1, sticky='w', padx=5)

        #按鈕
        self.output_path_button = tk.Button(youtube_input_labelframe, text='瀏覽', padx=30, command=self.select_directory)
        self.output_path_button.grid(row=1, column=2, padx=5)

#啟動停止鈕
    #外框
        button_labelframe = tk.LabelFrame(windows, borderwidth=0, highlightthickness=0)
        button_labelframe.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        # 為了置中設置的
        button_labelframe.grid_columnconfigure(0, weight=1)
        button_labelframe.grid_columnconfigure(1, weight=1)

        # 開始按鈕
        self.start_button = tk.Button(button_labelframe, text='開始轉錄', padx=30, state="normal", command=self.start)
        self.start_button.grid(row=0, column=0, padx=5, pady=10, sticky="e")

        # 停止按鈕
        self.stop_button = tk.Button(button_labelframe, text='停止', padx=30, state="disabled", command=self.stop)
        self.stop_button.grid(row=0, column=1, padx=5, pady=10, sticky="w")

#處理日置
    #外框
        log_labelframe = tk.LabelFrame(windows, text='處理日誌', padx=10, pady=10)
        log_labelframe.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        log_labelframe.grid_columnconfigure(0, weight=1)
        log_labelframe.grid_rowconfigure(0, weight=1)
    #顯示區域
        self.log_text = scrolledtext.ScrolledText(log_labelframe, wrap=tk.WORD,state="disabled", height=10)
        self.log_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # 重定向 sys.stdout 到文字區域
        sys.stdout = TextRedirector(self.log_text)

        windows.mainloop()
#按鈕邏輯
    def toggle_password(self):
        """切換密碼顯示與隱藏"""
        button_text = self.api_key_button.cget("text")
        if button_text == "顯示":
            self.api_key_input.config(show="")
            self.api_key_button.config(text="隱藏")
        else:
            self.api_key_input.config(show="*")
            self.api_key_button.config(text="顯示")

    def select_directory(self):
        """選擇目錄"""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_path_input.delete(0, tk.END)
            self.output_path_input.insert(0, folder_selected)

    def start(self):
        try:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            api_key = self.api_key_input.get()
            language = self.language_label_input.get()
            output_path = self.output_path_input.get()
            url = self.youtube_url_input.get()
            whisper_model = self.whisper_model

            self.transcriber = YouTubeTranscriber(api_key=api_key, language=language,output_path=output_path,whisper_model=whisper_model)
            # 使用線程來跑
            self.transcription_thread = threading.Thread(target=self.transcriber.process_video, args=(url,))
            self.transcription_thread.start()

        except Exception as e:
            print(f"錯誤: {str(e)}")
            sys.exit(1)

    def stop(self):
        self.stop_button.config(state="disabled")
        if self.transcriber:
            self.transcriber.stop_transcription()
            print("停止請求已發送")

            # TODO 應該確認完全停止後才開放start按鈕
            self.start_button.config(state="normal")


class YouTubeTranscriber:
    def __init__(self,api_key,whisper_model,language,output_path):
        # 建立輸出目錄
        self.output_dir = Path(f'{output_path}')
        self.output_dir.mkdir(exist_ok=True)

        self.api_key =api_key
        self.whisper_model =whisper_model
        self.language =language
        self.stop_flag = False
        openai.api_key = self.api_key

        # 初始化設備
        self.device = self.get_device()
        print(f"使用設備: {self.device}")

    def stop_transcription(self):
        self.stop_flag = True  # 設定停止旗標

    def check_stop_flag(func):
        """裝飾器：如果 stop_flag 為 True，就停止執行該函式"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.stop_flag:
                print(f"⚠ {func.__name__} 被取消 (stop_flag=True)")
                return  # **直接返回，不執行函式**
            return func(self, *args, **kwargs)
        return wrapper
    
    @check_stop_flag
    def get_device(self):
        """檢查並返回可用的計算設備"""
        if torch.backends.mps.is_available():
            print("使用 MPS (Apple GPU) 進行處理")
            return "mps"
        elif torch.cuda.is_available():
            print("使用 CUDA GPU 進行處理")
            return "cuda"
        else:
            print("使用 CPU 進行處理")
            return "cpu"

    @check_stop_flag
    def sanitize_filename(self, filename):
        """清理檔案名稱，移除非法字元"""
        # 移除或替換非法字元
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '[', ']']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        # 移除開頭和結尾的空格及點
        filename = filename.strip('. ')
        # 如果檔名為空，使用預設名稱
        if not filename:
            filename = 'untitled'
        return filename

    @check_stop_flag
    def download_audio(self, url):
        """下載 YouTube 影片的音訊"""
        try:
            print(f"正在下載影片音訊: {url}")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'paths': {'home': str(self.output_dir)},
                'outtmpl': {'default': '%(id)s.%(ext)s'},
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'quiet': False,
                'no_warnings': False
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 獲取影片信息
                info = ydl.extract_info(url, download=False)
                video_id = info['id']
                video_title = info['title']
                
                # 檢查文件是否已存在
                output_path = self.output_dir / f"{video_id}.mp3"
                if not output_path.exists():
                    # 下載音訊
                    ydl.download([url])
                    print(f"音訊下載完成: {output_path}")
                else:
                    print(f"音訊檔案已存在: {output_path}")
                
                return str(output_path), video_title
                
        except Exception as e:
            print(f"下載音訊時發生錯誤: {str(e)}")
            raise
    
    @check_stop_flag
    def transcribe_audio(self, audio_path, language="zh"):
        """使用 Whisper 轉錄音訊"""
        try:
            print("正在載入 Whisper 模型...")
            
            # 載入模型並移至指定設備
            model = whisper.load_model(self.whisper_model)
            
            # 如果是 MPS 設備，需要特別處理
            if self.device == "mps":
                try:
                    model.to(torch.device(self.device))
                    print("成功將模型移至 MPS 設備")
                except Exception as e:
                    print(f"警告：無法使用 MPS 設備，切換回 CPU: {str(e)}")
                    self.device = "cpu"
            
            print(f"使用 {self.whisper_model} 模型進行轉錄...")
            print(f"音訊檔案: {audio_path}")
            
            # 進行轉錄
            result = model.transcribe(
                audio_path,
                language=language,
                task="transcribe",
                temperature=0.2,
                fp16=self.device != "cpu"  # 在 GPU 上使用 FP16 加速
            )
            
            return result
            
        except Exception as e:
            print(f"轉錄音訊時發生錯誤: {str(e)}")
            raise
    @check_stop_flag
    def find_latest_whisper_result(self, video_title):
        """查找最新的 Whisper 轉錄結果"""
        safe_title = self.sanitize_filename(video_title)
        dir_path = self.output_dir / safe_title
        
        if not dir_path.exists():
            return None, None
            
        # 查找所有 whisper_raw_*.json 文件
        json_files = list(dir_path.glob("whisper_raw_*.json"))
        if not json_files:
            return None, None
            
        # 取得最新的文件
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        timestamp = latest_file.stem.split('whisper_raw_')[-1]
        
        # 讀取 JSON 文件
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            return result, timestamp
        except Exception as e:
            print(f"讀取既有轉錄結果時發生錯誤: {str(e)}")
            return None, None
        
    @check_stop_flag
    def format_timestamps(self, segments):
        """格式化時間戳記"""
        formatted_text = ""
        for seg in segments:
            minutes = int(seg["start"] // 60)
            seconds = int(seg["start"] % 60)
            formatted_text += f"[{minutes:02d}:{seconds:02d}] {seg['text']}\n"
        return formatted_text

    @check_stop_flag
    def save_transcription(self, result, video_title, timestamp=None):
        """保存 Whisper 轉錄結果"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        safe_title = self.sanitize_filename(video_title)
        transcription_dir = self.output_dir / safe_title
        transcription_dir.mkdir(exist_ok=True)
        
        # 保存原始轉錄結果為 JSON
        json_path = transcription_dir / f"whisper_raw_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        # 保存純文本版本
        text_path = transcription_dir / f"whisper_text_{timestamp}.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
            
        return transcription_dir
        formatted_text = ""
        for seg in segments:
            minutes = int(seg["start"] // 60)
            seconds = int(seg["start"] % 60)
            formatted_text += f"[{minutes:02d}:{seconds:02d}] {seg['text']}\n"
        return formatted_text
    
    @check_stop_flag
    def optimize_transcript(self, transcript_text):
        """使用 GPT-4 優化逐字稿"""
        try:
            print("正在使用 GPT-4 優化逐字稿...")
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": f"請將以下逐字稿整理為段落清晰、語句通順的文本：\n\n{transcript_text}"
                }],
                temperature=0.3
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"優化逐字稿時發生錯誤: {str(e)}")
            raise
    
    @check_stop_flag
    def generate_topics(self, transcript_with_timestamps):
        """使用 GPT-4 生成議題時間軸"""
        try:
            print("正在使用 GPT-4 生成議題時間軸...")
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": (
                        "請根據以下帶時間戳的逐字稿內容，列出主要議題段落的時間點與標題。"
                        "只需要回覆下述格式，不需要添加其他內容"
                        "格式要求：每行一個時間點，格式為 HH:MM:SS 標題\n"
                        "以下為範例"
                        "07:01 如何一句話激怒里亞\n"
                        "21:22 討論台V與日V的比較\n"
                        "39:44 里亞是原住民\n"
                        "51:29 當後勤遇到公主病的V\n"
                        "01:01:19 Vtuber的身體健康問題\n"
                        f"{transcript_with_timestamps}"
                    )
                }],
                temperature=0.3
            )
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"生成議題時間軸時發生錯誤: {str(e)}")
            raise

    @check_stop_flag
    def process_video(self, url, language="zh", force_transcribe=False):
        """處理完整的影片轉錄流程"""
        try:
            # 1. 下載音訊
            audio_path, video_title = self.download_audio(url)
            
            # 2. 檢查是否有現有的轉錄結果
            existing_result, existing_timestamp = self.find_latest_whisper_result(video_title)
            
            if existing_result and not force_transcribe:
                print(f"\n找到現有的轉錄結果，使用時間戳: {existing_timestamp}")
                transcription_result = existing_result
                timestamp = existing_timestamp
                video_output_dir = self.output_dir / self.sanitize_filename(video_title)
            else:
                # 需要重新轉錄
                print("\n開始新的 Whisper 轉錄...")
                transcription_result = self.transcribe_audio(audio_path, language)
                
                # 立即保存 Whisper 結果
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                video_output_dir = self.save_transcription(transcription_result, video_title, timestamp)
                print(f"已保存 Whisper 轉錄結果至: {video_output_dir}")
            
            # 3. 優化逐字稿
            print("\n開始 GPT-4 優化...")
            try:
                optimized_text = self.optimize_transcript(transcription_result["text"])
                
                # 4. 生成議題時間軸
                transcript_with_timestamps = self.format_timestamps(transcription_result["segments"])
                topics_timeline = self.generate_topics(transcript_with_timestamps)
                
                # 5. 儲存 GPT 處理結果
                # 儲存優化後的逐字稿
                with open(video_output_dir / f"gpt_transcript_{timestamp}.txt", "w", encoding="utf-8") as f:
                    f.write(optimized_text)
                
                # 儲存議題時間軸
                with open(video_output_dir / f"gpt_topics_{timestamp}.txt", "w", encoding="utf-8") as f:
                    f.write(topics_timeline)
                
                print(f"\nGPT 處理完成！所有檔案已儲存至: {video_output_dir}")
            except Exception as e:
                print(f"\nGPT 處理過程發生錯誤: {str(e)}")
                print(f"但 Whisper 轉錄結果已保存在: {video_output_dir}")
            
            return video_output_dir
            
        except Exception as e:
            print(f"處理影片時發生錯誤: {str(e)}")
            raise
            
        except Exception as e:
            print(f"處理影片時發生錯誤: {str(e)}")
            raise
            
        except Exception as e:
            print(f"處理影片時發生錯誤: {str(e)}")
            raise

def main():
    windows = tk_ui()
    windows.bulid_ui()

if __name__ == "__main__":
    main()
