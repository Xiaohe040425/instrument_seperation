import os
import uuid
from datetime import datetime
from flask import current_app


def allowed_file(filename):
    """檢查檔案是否為允許的類型"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def generate_job_id():
    """生成唯一的工作ID"""
    return str(uuid.uuid4())


def get_file_size(file_path):
    """取得檔案大小，並轉換為可讀格式"""
    size_bytes = os.path.getsize(file_path)

    # 轉換為KB、MB等單位
    units = ["B", "KB", "MB", "GB"]
    size = size_bytes
    unit_index = 0

    while size > 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


def get_formatted_time():
    """取得格式化的當前時間"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
