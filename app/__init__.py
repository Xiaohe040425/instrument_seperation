from flask import Flask
from config import Config
import os


def create_app(config_class=Config):
    # 建立 Flask 應用實例
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 確保上傳和下載目錄存在
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["DOWNLOAD_FOLDER"], exist_ok=True)

    # 註冊路由
    from app.routes import main_bp

    app.register_blueprint(main_bp)

    return app
