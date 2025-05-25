"""
SoundFont downloader utility
Downloads basic soundfont for audio conversion
"""

import requests
from pathlib import Path
import os


def download_basic_soundfont():
    """Download a basic soundfont file"""

    # 創建soundfonts資料夾
    soundfont_dir = Path(__file__).parent.parent / "soundfonts"
    soundfont_dir.mkdir(exist_ok=True)

    # GeneralUser GS SoundFont (免費且高品質)
    soundfont_url = "https://www.schristiancollins.com/generaluser/GeneralUser_GS.sf2"
    soundfont_file = soundfont_dir / "GeneralUser_GS.sf2"

    if soundfont_file.exists():
        print(f"✅ SoundFont already exists: {soundfont_file}")
        return str(soundfont_file)

    print("📥 Downloading basic SoundFont...")
    print("   This may take a few minutes...")

    try:
        response = requests.get(soundfont_url, stream=True)
        response.raise_for_status()

        # 下載檔案
        with open(soundfont_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ SoundFont downloaded successfully: {soundfont_file}")
        return str(soundfont_file)

    except Exception as e:
        print(f"❌ Download failed: {e}")
        print(
            "💡 You can manually download from: https://www.schristiancollins.com/generaluser/"
        )
        return None


if __name__ == "__main__":
    download_basic_soundfont()
