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

class YouTubeTranscriber:
    def __init__(self):
        # 載入 .env 檔案
        load_dotenv()
        
        # 設置 OpenAI API key
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("請在 .env 檔案中設置 OPENAI_API_KEY")
        openai.api_key = self.api_key
        
        # 從 .env 讀取其他設定
        self.whisper_model = os.getenv('WHISPER_MODEL', 'small')
        self.language = os.getenv('LANGUAGE', 'zh')
        
        # 建立輸出目錄
        self.output_dir = Path('transcripts')
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化設備
        self.device = self.get_device()
        print(f"使用設備: {self.device}")

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

    def format_timestamps(self, segments):
        """格式化時間戳記"""
        formatted_text = ""
        for seg in segments:
            minutes = int(seg["start"] // 60)
            seconds = int(seg["start"] % 60)
            formatted_text += f"[{minutes:02d}:{seconds:02d}] {seg['text']}\n"
        return formatted_text

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
                        "39:44 心智倒退與看台壓力\n"
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
    if len(sys.argv) < 2:
        print("使用方式: python script.py <YouTube URL>")
        return
    
    try:
        url = sys.argv[1]
        transcriber = YouTubeTranscriber()
        transcriber.process_video(url)
    except Exception as e:
        print(f"錯誤: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()