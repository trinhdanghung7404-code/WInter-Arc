import os
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
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "telegram_bot": "running" if bot_instance.is_running else "waiting"
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
