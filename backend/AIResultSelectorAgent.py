import threading
import openai
import os
import json

from backend import SongSearcher

class AIResultSelectorAgent:
    def __init__(self, song_searcher: SongSearcher):
        self.song_searcher = song_searcher
        current_dir = os.path.dirname(__file__)
        json_path = os.path.join(current_dir, "api_keys.json")
        with open(json_path, "r") as f:
            keys = json.load(f)
        openai.api_key = keys.get("open_ai")
        if not openai.api_key:
            raise ValueError("Missing open ai API key in api_keys.json")

    def select_best_results(self, query, max_results=5):
        yt_results = []
        sc_results = []

        def yt_worker():
            nonlocal yt_results
            try:
                yt_results = self.song_searcher.search_youtube(query, max_results=10)
            except Exception as e:
                print(f"YouTube search failed: {e}")
                yt_results = []

        def sc_worker():
            nonlocal sc_results
            try:
                sc_results = self.song_searcher.search_soundcloud(query, max_results=10)
            except Exception as e:
                print(f"SoundCloud search failed: {e}")
                sc_results = []

        thread_yt = threading.Thread(target=yt_worker)
        thread_sc = threading.Thread(target=sc_worker)

        thread_yt.start()
        thread_sc.start()

        thread_yt.join()
        thread_sc.join()
        print(yt_results, sc_results)

        def format_results(results, platform):
            formatted = []
            for r in results:
                title = r.get('title', 'unknown title')
                url = r.get('url', 'unknown url')
                formatted.append(f"- [{platform}] {title} ({url})")
            return "\n".join(formatted)

        prompt = f"""
Masz zapytanie: "{query}".
Poniżej masz dwie listy wyników wyszukiwania piosenek z dwóch serwisów:

Wyniki YouTube:
{format_results(yt_results, 'YouTube')}

Wyniki SoundCloud:
{format_results(sc_results, 'SoundCloud')}

Twoim zadaniem jest wybrać i uporządkować najlepsze piosenki, biorąc pod uwagę:
- Powtarzające się utwory na obu listach (te traktuj jako bardziej trafne).
- Ocenę trafności wyników względem zapytania.
- Maksymalnie {max_results} piosenek w ostatecznej liście.

Odpowiedz w formacie JSON, lista obiektów z kluczami: title, url, source (YouTube lub SoundCloud).
"""

        response = openai.ChatCompletion.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "Jesteś asystentem wybierającym najlepsze wyniki muzyczne."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=500
        )

        content = response['choices'][0]['message']['content']
        print("AI Response:", content)

        try:
            selected_results = json.loads(content)
        except Exception:
            selected_results = []

        return selected_results
