import time
import pytest

from backend.audioloader import AudioLoader

audio_loader = AudioLoader

@pytest.mark.slow
def test_get_title_real_url():
    loader = audio_loader()
    url = "https://www.youtube.com/watch?v=g2_fdjpBgMI"

    start = time.time()
    title,thumbnail = loader.get_title_and_icon(url)
    duration = time.time() - start

    print(f"get_title took {duration:.2f} seconds, title: {title}")
    assert isinstance(title, str)
    assert isinstance(thumbnail, str)
    assert len(title) > 0


@pytest.mark.slow
def test_download_real_url(tmp_path):
    loader = audio_loader(output_dir=str(tmp_path))
    url = "https://www.youtube.com/watch?v=g2_fdjpBgMI"

    start = time.time()
    loader.download(url)
    duration = time.time() - start

    filename = loader._url_to_filename(url)
    filepath = tmp_path / filename

    print(f"download took {duration:.2f} seconds, file saved at: {filepath}")
    assert filepath.exists()
    assert filepath.stat().st_size > 0
