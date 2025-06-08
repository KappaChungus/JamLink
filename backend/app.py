import json
import os
import threading
from flask import Flask, request, jsonify, send_from_directory
import requests

from backend.AIResultSelectorAgent import AIResultSelectorAgent
from backend.SongSearcher import SongSearcher
from backend.audioloader import AudioLoader
from backend.PartialFileSender import send_file_partial

app = Flask(__name__)
songs_view = {}
songs_status = {}
lock = threading.Lock()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DOWNLOADS_DIR = os.path.join(STATIC_DIR, 'downloads')

audio_loader = AudioLoader(DOWNLOADS_DIR)
song_searcher = SongSearcher()
agent = AIResultSelectorAgent(song_searcher)
print(STATIC_DIR, DOWNLOADS_DIR)

def download_and_update_status(url):
    try:
        status = audio_loader.download(url)
    except Exception as e:
        status = 'Error'
        print(f"Download error for {url}: {e}")
    with lock:
        songs_status[url] = status

@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
    try:
        with lock:
            songs_status[url] = 'Downloading'
        threading.Thread(target=download_and_update_status, args=(url,), daemon=True).start()
        songs_view[url] = audio_loader.get_data(url)
        return jsonify({'success': 'Download started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-audio-list', methods=['GET'])
def get_audio_list():
    with lock:
        songs_with_partial = []
        for url, data in songs_view.items():
            partial_filename = audio_loader.get_partial_filename(url)
            song_data = dict(data)
            song_data['partial_filename'] = partial_filename
            songs_with_partial.append(song_data)
    return jsonify({'songs': songs_with_partial})

@app.route('/audio/<filename>')
def serve_audio(filename):
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    if not os.path.exists(file_path):
        base, ext = os.path.splitext(file_path)
        part_path = None
        for ext_try in ['.webm.part', '.m4a.part', '.webm', '.m4a']:
            candidate = base + ext_try
            if os.path.exists(candidate):
                part_path = candidate
                break
        if part_path:
            file_path = part_path
        else:
            return "File not found", 404
    return send_file_partial(file_path)

@app.route('/download-status', methods=['GET'])
def download_status():
    url = request.args.get('url')
    with lock:
        status = songs_status.get(url, 'Not found')
    return jsonify({'status': status})

@app.route('/search-song')
def search_song():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query'}), 400

    try:
        results = agent.select_best_results(query)

        return jsonify(results)

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
