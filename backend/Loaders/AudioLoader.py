import os
from yt_dlp import YoutubeDL
import imageio_ffmpeg

class AudioLoader:
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = output_dir
        self.ffmpeg_location = imageio_ffmpeg.get_ffmpeg_exe()
        os.makedirs(self.output_dir, exist_ok=True)

    def download_mp3(self,url: str) -> str:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
        }
        if self.ffmpeg_location:
            ydl_opts['ffmpeg_location'] = self.ffmpeg_location

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_file = os.path.splitext(filename)[0] + ".mp3"
            return mp3_file
