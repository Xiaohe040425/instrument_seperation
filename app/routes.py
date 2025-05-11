from flask import (
    Blueprint,
    render_template,
    current_app,
    jsonify,
    request,
    flash,
    redirect,
    url_for,
    session,
    send_from_directory,
)
import os
from werkzeug.utils import secure_filename
from app.utils import allowed_file, generate_job_id, get_file_size, get_formatted_time
import json
import shutil

# 建立藍圖
main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """首頁路由"""
    return render_template("index.html")


@main_bp.route("/health")
def health_check():
    """健康檢查路由，用於確認API正常運作"""
    return jsonify({"status": "ok", "message": "系統正常運作中"})


@main_bp.route("/upload", methods=["POST"])
def upload_file():
    """處理檔案上傳"""
    # 檢查是否有檔案
    if "file" not in request.files:
        flash("沒有選擇檔案", "danger")
        return redirect(url_for("main.index"))

    file = request.files["file"]

    # 檢查檔案是否為空
    if file.filename == "":
        flash("沒有選擇檔案", "danger")
        return redirect(url_for("main.index"))

    # 檢查檔案類型是否允許
    if not allowed_file(file.filename):
        allowed_exts = ", ".join(current_app.config["ALLOWED_EXTENSIONS"])
        flash(f"檔案類型不支援。允許的類型：{allowed_exts}", "danger")
        return redirect(url_for("main.index"))

    # 生成工作ID並保存檔案
    job_id = generate_job_id()
    filename = secure_filename(file.filename)

    # 為每個工作建立獨立的目錄
    job_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], job_id)
    os.makedirs(job_dir, exist_ok=True)

    file_path = os.path.join(job_dir, filename)
    file.save(file_path)

    # 獲取檔案大小
    filesize = get_file_size(file_path)

    # 儲存工作資訊
    job_info = {
        "job_id": job_id,
        "filename": filename,
        "original_filename": file.filename,
        "file_path": file_path,
        "upload_time": get_formatted_time(),
        "filesize": filesize,
        "status": "uploaded",
    }

    # 將工作資訊保存為JSON檔案
    with open(os.path.join(job_dir, "job_info.json"), "w", encoding="utf-8") as f:
        json.dump(job_info, f, ensure_ascii=False, indent=4)

    # 轉到結果頁面
    return redirect(url_for("main.result_page", job_id=job_id))


@main_bp.route("/result/<job_id>")
def result_page(job_id):
    """結果頁面路由"""
    # 讀取工作資訊
    job_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], job_id)
    job_info_path = os.path.join(job_dir, "job_info.json")

    if not os.path.exists(job_info_path):
        flash("找不到工作資訊", "danger")
        return redirect(url_for("main.index"))

    with open(job_info_path, "r", encoding="utf-8") as f:
        job_info = json.load(f)

    # 模擬輸入文件列表
    input_files = [
        {
            "name": job_info["original_filename"],
            "type": job_info["filename"].split(".")[-1].upper(),
        }
    ]

    # 檢查是否已經有處理結果
    results_dir = os.path.join(current_app.config["DOWNLOAD_FOLDER"], job_id)
    if os.path.exists(results_dir) and os.path.exists(
        os.path.join(results_dir, "analysis_result.json")
    ):
        with open(
            os.path.join(results_dir, "analysis_result.json"), "r", encoding="utf-8"
        ) as f:
            analysis_result = json.load(f)

        # 獲取輸出文件列表
        output_files = [
            {"name": track["instrument"] + ".MIDI", "type": "MIDI"}
            for track in analysis_result.get("tracks", [])
        ]

        # 計算進度為100%
        progress = 100
    else:
        # 沒有結果時，輸出文件列表為空，進度為0
        output_files = []
        progress = 0

    return render_template(
        "result.html",
        job_id=job_id,
        input_files=input_files,
        output_files=output_files,
        progress=progress,
    )


@main_bp.route("/api/convert/<job_id>", methods=["POST"])
def convert_file(job_id):
    """開始文件轉換處理"""
    try:
        # 讀取工作資訊
        job_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], job_id)
        job_info_path = os.path.join(job_dir, "job_info.json")

        if not os.path.exists(job_info_path):
            return jsonify({"status": "error", "message": "找不到工作資訊"})

        with open(job_info_path, "r", encoding="utf-8") as f:
            job_info = json.load(f)

        # 模擬轉換過程
        # 實際應用中，這裡會呼叫您的後端模組進行處理

        # 模擬分析結果
        analysis_result = {
            "job_id": job_id,
            "filename": job_info["filename"],
            "completion_time": get_formatted_time(),
            "track_count": 5,  # 假設值
            "duration": 180,  # 秒
            "difficulty": 7,  # 1-10
            "tracks": [
                {
                    "name": "主旋律",
                    "instrument": "Trumpet1",
                    "role": "主旋律",
                    "score": 9,
                },
                {
                    "name": "和聲1",
                    "instrument": "Trombone",
                    "role": "和弦墊底",
                    "score": 8,
                },
                {"name": "和聲2", "instrument": "Horn", "role": "和弦墊底", "score": 7},
                {
                    "name": "低音部",
                    "instrument": "Tuba",
                    "role": "主律動（基底）",
                    "score": 9,
                },
                {
                    "name": "打擊樂",
                    "instrument": "Drums",
                    "role": "節奏樂器",
                    "score": 8,
                },
            ],
        }

        # 保存分析結果
        results_dir = os.path.join(current_app.config["DOWNLOAD_FOLDER"], job_id)
        os.makedirs(results_dir, exist_ok=True)

        with open(
            os.path.join(results_dir, "analysis_result.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=4)

        # 更新工作狀態
        job_info["status"] = "converted"

        with open(job_info_path, "w", encoding="utf-8") as f:
            json.dump(job_info, f, ensure_ascii=False, indent=4)

        return jsonify({"status": "success", "message": "轉換完成"})
    except Exception as e:
        # 記錄例外以便排錯
        print(f"轉換處理時發生錯誤: {str(e)}")
        return jsonify({"status": "error", "message": f"處理過程中發生錯誤: {str(e)}"})


@main_bp.route("/api/status/<job_id>")
def get_job_status(job_id):
    """獲取工作狀態"""
    job_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], job_id)
    job_info_path = os.path.join(job_dir, "job_info.json")

    if not os.path.exists(job_info_path):
        return jsonify({"status": "error", "message": "找不到工作資訊"})

    with open(job_info_path, "r", encoding="utf-8") as f:
        job_info = json.load(f)

    # 檢查是否已經完成
    results_dir = os.path.join(current_app.config["DOWNLOAD_FOLDER"], job_id)
    if os.path.exists(results_dir) and os.path.exists(
        os.path.join(results_dir, "analysis_result.json")
    ):
        progress = 100
        status = "completed"
    else:
        # 模擬進度
        if job_info["status"] == "uploaded":
            progress = 0
            status = "waiting"
        else:
            progress = 50  # 假設進度
            status = "processing"

    return jsonify({"status": status, "progress": progress, "job_id": job_id})


@main_bp.route("/statistic/<job_id>/<chart_type>")
def statistic_page(job_id, chart_type):
    """統計頁面路由"""
    # 檢查工作和圖表類型存在
    job_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], job_id)
    results_dir = os.path.join(current_app.config["DOWNLOAD_FOLDER"], job_id)

    if not os.path.exists(job_dir) or not os.path.exists(results_dir):
        flash("找不到工作資訊或分析結果", "danger")
        return redirect(url_for("main.index"))

    # 可用的圖表類型
    chart_types = [
        {"id": "breathing", "name": "換氣頓點圖"},
        {"id": "difficulty", "name": "難度分析圖"},
        {"id": "technical", "name": "技術曲線圖"},
    ]

    # 檢查選擇的圖表類型是否有效
    if chart_type not in [c["id"] for c in chart_types]:
        chart_type = "breathing"  # 預設圖表類型

    return render_template(
        "statistic.html", job_id=job_id, chart_type=chart_type, chart_types=chart_types
    )


@main_bp.route("/api/charts/<job_id>/<chart_type>")
def get_chart(job_id, chart_type):
    """獲取圖表數據API"""
    # 實際應用中，這裡會從您的後端獲取實際的圖表數據或圖片
    # 目前我們只返回一些佔位圖片或數據

    # 模擬返回圖片URL
    chart_url = f"/static/img/placeholder_{chart_type}.png"

    return jsonify(
        {"status": "success", "chart_url": chart_url, "chart_type": chart_type}
    )


@main_bp.route("/download/<job_id>")
def download_results(job_id):
    """下載處理結果"""
    # 檢查結果目錄是否存在
    results_dir = os.path.join(current_app.config["DOWNLOAD_FOLDER"], job_id)
    if not os.path.exists(results_dir):
        flash("找不到處理結果", "danger")
        return redirect(url_for("main.result_page", job_id=job_id))

    # 讀取分析結果
    analysis_path = os.path.join(results_dir, "analysis_result.json")
    if not os.path.exists(analysis_path):
        flash("找不到分析結果", "danger")
        return redirect(url_for("main.result_page", job_id=job_id))

    # 創建臨時目錄來存放MIDI檔案
    temp_dir = os.path.join(results_dir, "temp_midi")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 讀取分析結果
        with open(analysis_path, "r", encoding="utf-8") as f:
            analysis_result = json.load(f)

        # 為每個軌道創建模擬MIDI檔案
        for track in analysis_result.get("tracks", []):
            midi_filename = f"{track['instrument']}.MIDI"
            midi_path = os.path.join(temp_dir, midi_filename)

            # 創建簡單的示例MIDI檔案
            with open(midi_path, "w") as f:
                f.write(f"This is a placeholder for {midi_filename}")

        # 創建ZIP文件
        zip_filename = f"converted_files_{job_id}.zip"
        zip_path = os.path.join(current_app.config["DOWNLOAD_FOLDER"], zip_filename)

        # 刪除已存在的ZIP檔案（如果有）
        if os.path.exists(zip_path):
            os.remove(zip_path)

        # 創建新的ZIP檔案
        shutil.make_archive(zip_path[:-4], "zip", temp_dir)

        # 確認ZIP檔案已創建
        if not os.path.exists(zip_path):
            flash("創建ZIP檔案失敗", "danger")
            return redirect(url_for("main.result_page", job_id=job_id))

        # 提供ZIP檔案下載
        return send_from_directory(
            directory=os.path.dirname(zip_path),
            path=os.path.basename(zip_path),
            as_attachment=True,
            download_name=zip_filename,
        )

    except Exception as e:
        # 捕獲並顯示任何錯誤
        flash(f"下載處理過程中發生錯誤: {str(e)}", "danger")
        return redirect(url_for("main.result_page", job_id=job_id))

    finally:
        # 清理臨時目錄（無論成功與否）
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
