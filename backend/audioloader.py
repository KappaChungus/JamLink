import os

from yt_dlp import YoutubeDL


class AudioLoader:
    def __init__(self, output_dir: str = "static/downloads"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def _url_to_basename(url: str) -> str:
        safe = url.replace("://", "_").replace("/", "_").replace("?", "_").replace("&", "_").replace("=", "_")
        return safe

    def get_data(self, url: str):
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Title')
            thumbnail = info.get('thumbnail')
            basename = self._url_to_basename(url)
            # Bez rozszerzenia, zwrócimy basename i docelowe mp3
            filename = basename + ".mp3"
            return {"title": title, "thumbnail": thumbnail, "filename": filename, "basename": basename}

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
