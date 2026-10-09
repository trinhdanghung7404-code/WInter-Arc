import os
import time

# Đánh dấu đây là Cloud Server (Render / Linux) để Bot luôn chạy polling 24/7
os.environ["IS_CLOUD_SERVER"] = "1"

# Ép múi giờ sang Giờ Việt Nam (Asia/Ho_Chi_Minh - GMT+7) trên server Render/Linux
os.environ["TZ"] = "Asia/Ho_Chi_Minh"
if hasattr(time, "tzset"):
    try:
        time.tzset()
    except Exception:
        pass

import json
import threading
from datetime import datetime, date
from flask import Flask, jsonify, request
from src import app_logic
from src.bot_service import bot_instance
from src.scheduler_service import scheduler_instance

app = Flask(__name__)

# ==============================================================================
# HEALTH CHECK & KEEP-ALIVE PING (Dành cho cron-job.org giữ server thức 24/7)
# ==============================================================================
@app.route("/", methods=["GET"])
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "status": "online",
        "service": "Winter Arc Cloud Engine",
        "server_time_vn": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Asia/Ho_Chi_Minh (GMT+7)",
        "telegram_bot": "running" if bot_instance.is_running else "waiting"
    }), 200

@app.route("/api/test_broadcast", methods=["GET"])
def test_broadcast():
    """Endpoint để bạn test bắn thông báo trực tiếp từ máy chủ Render sang điện thoại"""
    success, msg = bot_instance.send_broadcast(
        f"⚡ <b>[RENDER CLOUD]</b> Thông báo thử nghiệm trực tiếp từ máy chủ Render!\n"
        f"🕒 Giờ máy chủ: {datetime.now().strftime('%H:%M:%S (%d/%m/%Y)')}",
        with_buttons=True
    )
    return jsonify({
        "success": success,
        "message": msg,
        "server_time_vn": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }), 200

@app.route("/api/upload_screentime", methods=["POST"])
def upload_screentime():
    """
    Endpoint nhận ảnh chụp màn hình Screen Time từ Apple Shortcuts (iPhone):
    - Đọc ảnh qua Gemini Vision AI
    - Lưu thời gian sử dụng vào storage hôm nay
    - Bắn tin nhắn phân tích & đánh giá kỷ luật về Telegram
    """
    from src import ai_service
    image_bytes = None
    mime_type = "image/jpeg"

    if "file" in request.files:
        f = request.files["file"]
        image_bytes = f.read()
        mime_type = f.mimetype or "image/jpeg"
    elif request.data:
        image_bytes = request.data
    else:
        body = request.get_json(silent=True) or {}
        if "image_base64" in body:
            import base64
            image_bytes = base64.b64decode(body["image_base64"])

    if not image_bytes:
        return jsonify({"error": "Không tìm thấy file ảnh"}), 400

    analysis = ai_service.analyze_screentime_image(image_bytes, mime_type=mime_type)
    
    # Lưu vào storage
    today_str = date.today().strftime("%Y-%m-%d")
    storage = app_logic.load_storage()
    day_rec = storage.setdefault("history", {}).setdefault(today_str, {})
    day_rec["screentime"] = {
        "total_time_str": analysis.get("total_time_str", ""),
        "total_minutes": analysis.get("total_minutes", 0),
        "top_apps": analysis.get("top_apps", []),
        "updated_at": datetime.now().strftime("%H:%M:%S")
    }
    app_logic.save_storage(storage)

    # Gửi tin nhắn về Telegram
    critique_msg = analysis.get("critique", "📱 Đã nhận ảnh Screen Time!")
    bot_instance.send_broadcast(critique_msg, with_buttons=True)

    return jsonify({
        "success": True,
        "message": "Đã phân tích Screen Time và gửi về Telegram!",
        "analysis": analysis
    }), 200

# ==============================================================================
# API ĐỒNG BỘ DỮ LIỆU VỚI DESKTOP
# ==============================================================================
@app.route("/api/today", methods=["GET"])
def get_today():
    """Desktop hoặc Web gọi để lấy dữ liệu hôm nay"""
    return jsonify(app_logic.get_today_data()), 200

@app.route("/api/toggle", methods=["POST"])
def toggle_task():
    """Tick hoàn thành nhiệm vụ"""
    body = request.get_json(silent=True) or {}
    task_id = body.get("task_id")
    if not task_id:
        return jsonify({"error": "Thiếu task_id"}), 400
    
    updated = app_logic.toggle_task(task_id)
    return jsonify(updated), 200

@app.route("/api/sync", methods=["GET", "POST"])
def sync_data():
    """
    Đồng bộ 2 chiều:
    - GET: Desktop kéo dữ liệu mới nhất từ Cloud về (sau khi bạn tick trên điện thoại)
    - POST: Desktop đẩy protocols hoặc storage mới nhất lên Cloud
    """
    if request.method == "GET":
        return jsonify({
            "protocols": app_logic.load_protocols(),
            "storage": app_logic.load_storage(),
            "config": app_logic.load_config()
        }), 200

    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        if "protocols" in body:
            app_logic.save_protocols(body["protocols"])
            scheduler_instance.setup_schedule()
        if "storage" in body:
            app_logic.save_storage(body["storage"])
        if "config" in body:
            # Chỉ cập nhật các trường an toàn, giữ nguyên telegram token/chat nếu có
            cfg = app_logic.load_config()
            cfg.update(body["config"])
            app_logic.save_config(cfg)
            bot_instance.restart()

        return jsonify({"status": "synced", "message": "Đã đồng bộ lên Cloud thành công!"}), 200

# ==============================================================================
# KHỞI CHẠY BOT VÀ HẸN GIỜ TRÊN LUỒNG CHẠY NGẦM CLOUD
# ==============================================================================
def start_background_workers():
    print("[CLOUD] Khởi động Telegram Bot & Scheduler trên Render...")
    bot_instance.start_polling()
    scheduler_instance.start()

# Khởi chạy worker thread
worker_thread = threading.Thread(target=start_background_workers, daemon=True)
worker_thread.start()

if __name__ == "__main__":
    # Render cấp cổng động qua biến môi trường PORT (mặc định 10000 hoặc 5000)
    port = int(os.environ.get("PORT", 10000))
    print(f"[CLOUD] Server Winter Arc đang lắng nghe tại cổng {port}...")
    app.run(host="0.0.0.0", port=port)
