from flask import Blueprint, render_template, current_app, jsonify

# 建立藍圖
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """首頁路由"""
    return render_template("index.html", title="管樂編曲系統")


@main_bp.route("/health")
def health_check():
    """健康檢查路由，用於確認API正常運作"""
    return jsonify({"status": "ok", "message": "系統正常運作中"})
