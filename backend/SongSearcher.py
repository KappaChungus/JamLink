import os
import json
import requests
from flask import Flask, request, jsonify

class SongSearcher:
    def __init__(self):
        current_dir = os.path.dirname(__file__)
        json_path = os.path.join(current_dir, "api_keys.json")
        with open(json_path, "r") as f:
            keys = json.load(f)
        self.yt_api_key = keys.get("yt")
        self.sc_client_id = keys.get("soundcloud")
        if not self.yt_api_key:
            raise ValueError("Missing YouTAube API key in api_keys.json")
        if not self.sc_client_id:
            raise ValueError("Missing SoundCloud client_id in api_keys.json")
    def search_youtube(self, query, max_results=5):
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': max_results,
            'key': self.yt_api_key
        }
        res = requests.get(search_url, params=params)
        res.raise_for_status()
        items = res.json().get('items', [])
        results = []
        for item in items:
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            results.append({'title': title, 'url': video_url})
        return results

    def search_soundcloud(self, query, max_results=5):

        search_url = "https://api-v2.soundcloud.com/search/tracks"
        params = {
            "q": query,
            "client_id": self.sc_client_id,
            "limit": max_results
        }
        res = requests.get(search_url, params=params)
        res.raise_for_status()
        data = res.json()
        results = []
        for track in data.get('collection', []):
            title = track.get('title')
            url = track.get('permalink_url')
            results.append({'title': title, 'url': url})
        return results