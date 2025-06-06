import threading
from flask import Flask, request, jsonify, send_from_directory
from backend.Loaders.AudioLoader import AudioLoader

audioloader = AudioLoader()
app = Flask(__name__)
display_name_map = {}

def download_background(url):
    try:
        audioloader.download_mp3(url)
    except Exception as e:
        print(f"Error downloading {url}: {e}")
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

def download_background(url):
    try:
        title = audioloader.get_title(url)  # pobierz tytuł od razu
        audioloader.download(url)            # pobierz w tle
        display_name_map[url] = title        # zapisz w mapie
    except Exception as e:
        print(f"Error downloading {url}: {e}")
@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
    try:
        threading.Thread(target=download_background, args=(url,), daemon=True).start()
        return jsonify({'success': 'Download started'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-audio-list', methods=['GET'])
def get_audio_list():
    return jsonify({'songs': list(display_name_map.values())})

if __name__ == '__main__':
    app.run(debug=True)
