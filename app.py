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
    with lock:
        songs_status[url] = audio_loader.download(url)


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
        threading.Thread(target=download_and_update_status, args=(url,)).start()
        songs_view[url] = audio_loader.get_data(url)
        return jsonify({'success': 'Download started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-audio-list', methods=['GET'])
def get_audio_list():
    return jsonify({'songs': list(songs_view.values())})

@app.route('/audio/<filename>')
def serve_audio(filename):
    file_path = os.path.join("static", "downloads", filename)
    return send_file_partial(file_path)

@app.route('/download-status', methods=['GET'])
def download_status():
    url = request.args.get('url')
    with lock:
        status = songs_status.get(url, 'Not found')
    return jsonify({'status': status})


if __name__ == '__main__':
    app.run(debug=True)
