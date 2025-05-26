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
import time
import threading
from werkzeug.utils import secure_filename
import json
import shutil
import uuid
from datetime import datetime
from app.utils import allowed_file, generate_job_id, get_file_size, get_formatted_time

# 建立藍圖
main_bp = Blueprint("main", __name__)
job_progress = {}


# 在routes.py中添加清理函數
def cleanup_job_progress(job_id, delay=60):
    """延遲清理工作進度資訊"""

    def cleanup():
        time.sleep(delay)
        if job_id in job_progress:
            del job_progress[job_id]
            print(f"清理工作進度資訊: {job_id}")

    cleanup_thread = threading.Thread(target=cleanup)
    cleanup_thread.daemon = True
    cleanup_thread.start()


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
    print("進入upload_file函數")

    # 檢查是否有檔案
    if "files[]" not in request.files:
        print("沒有找到'files[]'參數")
        flash("沒有選擇檔案", "danger")
        return redirect(url_for("main.index"))

    files = request.files.getlist("files[]")
    print(f"接收到的檔案數量: {len(files)}")

    # 檢查是否有選擇檔案
    if not files or files[0].filename == "":
        print("沒有檔案或第一個檔案名為空")
        flash("沒有選擇檔案", "danger")
        return redirect(url_for("main.index"))

    # 生成工作ID
    job_id = generate_job_id()
    print(f"生成的job_id: {job_id}")

    # 為工作建立獨立的目錄
    job_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], job_id)
    os.makedirs(job_dir, exist_ok=True)

    # 保存檔案資訊
    file_info_list = []

    for file in files:
        # 檢查檔案類型是否允許
        if not allowed_file(file.filename):
            print(f"檔案類型不支援: {file.filename}")
            allowed_exts = ", ".join(current_app.config["ALLOWED_EXTENSIONS"])
            flash(
                f"檔案 {file.filename} 類型不支援。允許的類型：{allowed_exts}", "danger"
            )
            continue

        # 安全的檔案名稱
        filename = secure_filename(file.filename)
        file_path = os.path.join(job_dir, filename)

        # 保存檔案
        file.save(file_path)
        print(f"檔案已保存: {file_path}")

        # 獲取檔案大小
        filesize = get_file_size(file_path)

        # 添加到檔案資訊列表
        file_info_list.append(
            {
                "filename": filename,
                "original_filename": file.filename,
                "file_path": file_path,
                "filesize": filesize,
            }
        )

    # 如果沒有成功上傳任何檔案，返回首頁
    if not file_info_list:
        print("沒有成功上傳任何檔案")
        flash("沒有成功上傳任何檔案", "danger")
        return redirect(url_for("main.index"))

    # 儲存工作資訊
    job_info = {
        "job_id": job_id,
        "upload_time": get_formatted_time(),
        "status": "uploaded",
        "files": file_info_list,
    }

    # 將工作資訊保存為JSON檔案
    job_info_path = os.path.join(job_dir, "job_info.json")
    with open(job_info_path, "w", encoding="utf-8") as f:
        json.dump(job_info, f, ensure_ascii=False, indent=4)
    print(f"工作資訊已保存: {job_info_path}")

    # 打印重定向URL
    redirect_url = url_for("main.result_page", job_id=job_id)
    print(f"重定向到: {redirect_url}")

    # 轉到結果頁面
    return redirect(redirect_url)


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

    # 獲取輸入文件列表
    input_files = [
        {
            "name": file_info["original_filename"],
            "type": file_info["filename"].split(".")[-1].upper(),
        }
        for file_info in job_info["files"]
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
    # 讀取工作資訊
    job_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], job_id)
    job_info_path = os.path.join(job_dir, "job_info.json")

    if not os.path.exists(job_info_path):
        return jsonify({"status": "error", "message": "找不到工作資訊"})

    with open(job_info_path, "r", encoding="utf-8") as f:
        job_info = json.load(f)

    # 初始化進度追蹤
    job_progress[job_id] = {
        "status": "processing",
        "progress": 0,
        "stage": "初始化中...",
    }

    # 獲取當前Flask應用實例
    app = current_app._get_current_object()

    # 在背景執行轉換過程
    def background_conversion():
        try:
            # 在背景線程中設置應用上下文
            with app.app_context():
                stages = [
                    {"progress": 10, "stage": "分析音檔結構..."},
                    {"progress": 25, "stage": "提取音樂特徵..."},
                    {"progress": 45, "stage": "分配管樂器..."},
                    {"progress": 65, "stage": "生成MIDI檔案..."},
                    {"progress": 80, "stage": "轉換音頻格式..."},
                    {"progress": 95, "stage": "整合混音結果..."},
                    {"progress": 100, "stage": "轉換完成"},
                ]

                for stage in stages:
                    time.sleep(1.2)  # 每個階段延遲1.2秒，總共約8.4秒
                    job_progress[job_id]["progress"] = stage["progress"]
                    job_progress[job_id]["stage"] = stage["stage"]
                    print(f"Job {job_id}: {stage['progress']}% - {stage['stage']}")

                # 準備輸出檔案列表（根據您的實際檔案）
                output_tracks = [
                    {
                        "name": "S00_French_Horn.MIDI",
                        "instrument": "S00_French_Horn",
                        "type": "MIDI",
                        "role": "法國號",
                        "score": 9,
                    },
                    {
                        "name": "S00_French_Horn.WAV",
                        "instrument": "S00_French_Horn",
                        "type": "WAV",
                        "role": "法國號",
                        "score": 9,
                    },
                    {
                        "name": "S01_Tuba.MIDI",
                        "instrument": "S01_Tuba",
                        "type": "MIDI",
                        "role": "低音號",
                        "score": 8,
                    },
                    {
                        "name": "S01_Tuba.WAV",
                        "instrument": "S01_Tuba",
                        "type": "WAV",
                        "role": "低音號",
                        "score": 8,
                    },
                    {
                        "name": "S02_Trumpet.MIDI",
                        "instrument": "S02_Trumpet",
                        "type": "MIDI",
                        "role": "小號",
                        "score": 9,
                    },
                    {
                        "name": "S02_Trumpet.WAV",
                        "instrument": "S02_Trumpet",
                        "type": "WAV",
                        "role": "小號",
                        "score": 9,
                    },
                    {
                        "name": "S03_Trumpet.MIDI",
                        "instrument": "S03_Trumpet",
                        "type": "MIDI",
                        "role": "小號2",
                        "score": 8,
                    },
                    {
                        "name": "S03_Trumpet.WAV",
                        "instrument": "S03_Trumpet",
                        "type": "WAV",
                        "role": "小號2",
                        "score": 8,
                    },
                    {
                        "name": "S08.MIDI",
                        "instrument": "S08",
                        "type": "MIDI",
                        "role": "特殊音軌",
                        "score": 7,
                    },
                    {
                        "name": "S08.WAV",
                        "instrument": "S08",
                        "type": "WAV",
                        "role": "特殊音軌",
                        "score": 7,
                    },
                    {
                        "name": "mix.MIDI",
                        "instrument": "mix",
                        "type": "MIDI",
                        "role": "混音",
                        "score": 10,
                    },
                    {
                        "name": "mix.WAV",
                        "instrument": "mix",
                        "type": "WAV",
                        "role": "混音",
                        "score": 10,
                    },
                ]

                # 模擬分析結果
                analysis_result = {
                    "job_id": job_id,
                    "completion_time": get_formatted_time(),
                    "file_count": len(job_info["files"]),
                    "track_count": len(output_tracks),
                    "duration": 180,
                    "difficulty": 7,
                    "tracks": output_tracks,
                    "files": job_info["files"],
                }

                # 保存分析結果
                results_dir = os.path.join(
                    current_app.config["DOWNLOAD_FOLDER"], job_id
                )
                os.makedirs(results_dir, exist_ok=True)

                with open(
                    os.path.join(results_dir, "analysis_result.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    json.dump(analysis_result, f, ensure_ascii=False, indent=4)

                # 更新工作狀態
                job_info["status"] = "converted"
                with open(job_info_path, "w", encoding="utf-8") as f:
                    json.dump(job_info, f, ensure_ascii=False, indent=4)

                # 標記為完成
                job_progress[job_id]["status"] = "completed"
                print(f"Job {job_id}: 轉換完成")

                # 60秒後清理進度資訊
                cleanup_job_progress(job_id, 60)

        except Exception as e:
            print(f"背景轉換過程發生錯誤: {e}")
            job_progress[job_id]["status"] = "error"
            job_progress[job_id]["stage"] = f"處理失敗: {str(e)}"
            job_progress[job_id]["message"] = str(e)

    # 啟動背景線程
    conversion_thread = threading.Thread(target=background_conversion)
    conversion_thread.daemon = True
    conversion_thread.start()

    return jsonify({"status": "success", "message": "開始轉換處理"})


@main_bp.route("/api/status/<job_id>")
def get_job_status(job_id):
    """獲取工作狀態"""
    # 如果有進度追蹤資訊，優先使用
    if job_id in job_progress:
        progress_info = job_progress[job_id]
        response_data = {
            "status": progress_info["status"],
            "progress": progress_info["progress"],
            "stage": progress_info.get("stage", "處理中..."),
            "job_id": job_id,
        }

        # 如果有錯誤，添加錯誤信息
        if progress_info["status"] == "error":
            response_data["message"] = progress_info.get("message", "未知錯誤")

        return jsonify(response_data)

    # 否則使用原來的檔案檢查邏輯
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
        return jsonify({"status": "completed", "progress": 100, "job_id": job_id})
    else:
        return jsonify({"status": "waiting", "progress": 0, "job_id": job_id})


@main_bp.route("/statistic/<job_id>/<chart_type>")
def statistic_page(job_id, chart_type):
    """統計頁面路由"""
    # 檢查工作和圖表類型存在
    job_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], job_id)
    results_dir = os.path.join(current_app.config["DOWNLOAD_FOLDER"], job_id)

    if not os.path.exists(job_dir) or not os.path.exists(results_dir):
        flash("找不到工作資訊或分析結果", "danger")
        return redirect(url_for("main.index"))

    # 直接使用圖表檔案名稱作為選項
    chart_files = [
        {
            "id": "S00_breathing",
            "filename": "S00_breathing.png",
            "display_name": "S00_breathing.png",
        },
        {
            "id": "S00_difficulty",
            "filename": "S00_difficulty.png",
            "display_name": "S00_difficulty.png",
        },
        {
            "id": "S01_breathing",
            "filename": "S01_breathing.png",
            "display_name": "S01_breathing.png",
        },
        {
            "id": "S01_difficulty",
            "filename": "S01_difficulty.png",
            "display_name": "S01_difficulty.png",
        },
        {
            "id": "S03_breathing",
            "filename": "S03_breathing.png",
            "display_name": "S03_breathing.png",
        },
        {
            "id": "S03_difficulty",
            "filename": "S03_difficulty.png",
            "display_name": "S03_difficulty.png",
        },
    ]

    # 檢查選擇的圖表類型是否有效
    valid_chart_ids = [c["id"] for c in chart_files]
    if chart_type not in valid_chart_ids:
        chart_type = "S00_breathing"  # 預設圖表

    # 找到當前選擇的圖表
    current_chart = next(
        (c for c in chart_files if c["id"] == chart_type), chart_files[0]
    )

    return render_template(
        "statistic.html",
        job_id=job_id,
        chart_type=chart_type,
        chart_files=chart_files,
        current_chart=current_chart,
    )


@main_bp.route("/api/charts/<job_id>/<chart_type>")
def get_chart(job_id, chart_type):
    """獲取圖表數據API"""

    # 圖表檔案映射
    chart_file_mapping = {
        "S00_breathing": "S00_breathing.png",
        "S00_difficulty": "S00_difficulty.png",
        "S01_breathing": "S01_breathing.png",
        "S01_difficulty": "S01_difficulty.png",
        "S03_breathing": "S03_breathing.png",
        "S03_difficulty": "S03_difficulty.png",
    }

    # 獲取對應的圖表檔案
    chart_filename = chart_file_mapping.get(chart_type, "S00_breathing.png")
    chart_url = f"/static/img/{chart_filename}"

    return jsonify(
        {
            "status": "success",
            "chart_url": chart_url,
            "chart_type": chart_type,
            "chart_file": chart_filename,
        }
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

    # 創建臨時目錄來存放檔案
    temp_dir = os.path.join(results_dir, "temp_output")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Demo檔案來源目錄
        demo_files_dir = os.path.join(current_app.root_path, "demo_files")

        # 要複製的檔案列表（根據您的實際檔案）
        demo_files = [
            "S00_French_Horn.mid",
            "S00_French_Horn.wav",
            "S01_Tuba.mid",
            "S01_Tuba.wav",
            "S02_Trumpet.mid",
            "S02_Trumpet.wav",
            "S03_Trumpet.wav",
            "S08.mid",
            "S08.wav",
            "mix.mid",
            "mix.wav",
        ]

        # 複製所有demo檔案到臨時目錄
        for filename in demo_files:
            demo_path = os.path.join(demo_files_dir, filename)
            output_path = os.path.join(temp_dir, filename)

            if os.path.exists(demo_path):
                shutil.copy2(demo_path, output_path)
                print(f"複製檔案: {filename}")
            else:
                # 如果demo檔案不存在，創建一個佔位檔案
                with open(output_path, "w") as f:
                    f.write(f"Demo output for {filename}")
                print(f"創建佔位檔案: {filename}")

        # 創建ZIP文件
        zip_filename = f"converted_results_{job_id}.zip"
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

        print(f"ZIP檔案創建成功: {zip_filename}")

        # 提供ZIP檔案下載
        return send_from_directory(
            directory=os.path.dirname(zip_path),
            path=os.path.basename(zip_path),
            as_attachment=True,
            download_name=zip_filename,
        )

    except Exception as e:
        print(f"下載處理錯誤: {e}")
        flash(f"下載處理過程中發生錯誤: {str(e)}", "danger")
        return redirect(url_for("main.result_page", job_id=job_id))

    finally:
        # 清理臨時目錄（無論成功與否）
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
