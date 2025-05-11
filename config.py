class Config(object):
    # 密鑰用於安全簽名
    SECRET_KEY = "your-secret-key"

    # 上傳文件設定
    UPLOAD_FOLDER = "app/uploads"
    DOWNLOAD_FOLDER = "app/downloads"
    ALLOWED_EXTENSIONS = {"wav", "mp3", "mid", "midi"}

    # 檔案大小限制 (16MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
