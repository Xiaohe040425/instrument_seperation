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

    # 打印已註冊的路由，用於調試
    print("已註冊的路由:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint} - {rule.rule} [{', '.join(rule.methods)}]")

    return app
