from flask import Flask, request, jsonify

from backend.Loaders.AudioLoader import AudioLoader

audioloader = AudioLoader()
app = Flask(__name__)
@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing URL'}), 400

    url = data['url']
    try:
        audioloader.download_mp3(url)
        return jsonify(
            {'success': 'Audio downloaded successfully'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)