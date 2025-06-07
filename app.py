import os
import threading
from flask import Flask, request, jsonify, send_from_directory
from backend.audioloader import AudioLoader
from backend.PartialFileSender import send_file_partial

audio_loader = AudioLoader()
app = Flask(__name__)
songs_view = {}
songs_status = {}
lock = threading.Lock()

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
    return send_from_directory('static', 'index.html')

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
        # Dodajemy partial filename, aby frontend mógł streamować z częściowego pliku podczas pobierania
        songs_with_partial = []
        for url, data in songs_view.items():
            partial_filename = audio_loader.get_partial_filename(url)
            song_data = dict(data)
            song_data['partial_filename'] = partial_filename
            songs_with_partial.append(song_data)
    return jsonify({'songs': songs_with_partial})

@app.route('/audio/<filename>')
def serve_audio(filename):
    file_path = os.path.join("static", "downloads", filename)
    if not os.path.exists(file_path):
        # Sprawdź czy istnieje plik .part z tym samym prefiksem
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

if __name__ == '__main__':
    app.run(debug=True)
