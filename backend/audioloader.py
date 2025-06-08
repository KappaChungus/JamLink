import os
import json
from yt_dlp import YoutubeDL
from googleapiclient.discovery import build

class AudioLoader:
    def __init__(self, output_dir :str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.yt_api_key = self._load_api_key()

    def _load_api_key(self):
        current_dir = os.path.dirname(__file__)
        json_path = os.path.join(current_dir, "api_keys.json")
        if not os.path.exists(json_path):
            raise FileNotFoundError("Plik api_keys.json nie istnieje")
        with open(json_path, "r") as f:
            data = json.load(f)
        if "yt" not in data:
            raise KeyError("Brak klucza 'yt' w api_keys.json")
        return data["yt"]

    @staticmethod
    def _url_to_basename(url: str) -> str:
        safe = url.replace("://", "_").replace("/", "_").replace("?", "_").replace("&", "_").replace("=", "_")
        return safe

    def get_data(self, url: str):
        if "youtube.com" in url or "youtu.be" in url:
            # YouTube API
            video_id = self._extract_video_id(url)
            if not video_id:
                return {"error": "Invalid YouTube URL"}

            try:
                youtube = build('youtube', 'v3', developerKey=self.yt_api_key)
                response = youtube.videos().list(
                    part='snippet',
                    id=video_id
                ).execute()
                if not response['items']:
                    return {"error": "Video not found"}

                snippet = response['items'][0]['snippet']
                title = snippet.get('title', 'Unknown Title')
                thumbnail = snippet['thumbnails']['high']['url']
            except Exception as e:
                return {"error": f"YouTube API error: {e}"}
        else:
            # Fallback do yt_dlp
            try:
                with YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown Title')
                    thumbnail = info.get('thumbnail')
            except Exception as e:
                return {"error": f"yt_dlp error: {e}"}

        basename = self._url_to_basename(url)
        filename = basename + ".mp3"

        return {
            "title": title,
            "thumbnail": thumbnail,
            "filename": filename,
            "basename": basename
        }

    def _extract_video_id(self, url: str) -> str:
        import re
        pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(pattern, url)
        return match.group(1) if match else None

    def download(self, url: str) -> str:
        basename = self._url_to_basename(url)
        outtmpl = os.path.join(self.output_dir, basename + ".%(ext)s")  # wyjście bez .mp3

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'quiet': True,
            # nie używamy konwersji, żeby zachować oryginalny format, pozwoli streamować .webm.part
            # ewentualnie można dodać 'postprocessors' jeśli chcesz, ale to blokuje streaming
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return 'Done'
        except Exception as e:
            print(f"Download error: {e}")
            return 'Error'

    def get_partial_filename(self, url: str):
        basename = self._url_to_basename(url)
        # Sprawdzamy, czy istnieje plik tymczasowy .part z dowolnym rozszerzeniem
        for ext in ['.webm.part', '.m4a.part', '.webm', '.m4a']:
            part_path = os.path.join(self.output_dir, basename + ext)
            if os.path.exists(part_path):
                return basename + ext
        # Jeżeli nie ma pliku częściowego, zwróć docelowy mp3 (może jest pobrany)
        mp3_path = os.path.join(self.output_dir, basename + ".mp3")
        if os.path.exists(mp3_path):
            return basename + ".mp3"
        return None
