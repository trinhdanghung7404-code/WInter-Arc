import threading
import requests
from . import app_logic

def get_cloud_url():
    """Lấy đường dẫn Cloud Server từ config.json"""
    try:
        cfg = app_logic.load_config()
        url = cfg.get("cloud_url", "").strip()
        if url:
            return url.rstrip("/")
    except Exception:
        pass
    return None

def sync_down():
    """Kéo dữ liệu mới nhất từ Cloud về Local (chạy ngầm khi mở app)"""
    cloud_url = get_cloud_url()
    if not cloud_url:
        return

    def worker():
        try:
            resp = requests.get(f"{cloud_url}/api/sync", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "storage" in data and isinstance(data["storage"], dict):
                    # Hợp nhất lịch sử: dữ liệu trên cloud có gì mới thì cập nhật
                    local_storage = app_logic.load_storage()
                    cloud_storage = data["storage"]
                    
                    # Merge streak & history
                    if "history" in cloud_storage:
                        local_storage.setdefault("history", {}).update(cloud_storage["history"])
                    if "streaks" in cloud_storage:
                        local_storage["streaks"] = cloud_storage["streaks"]

                    app_logic.save_storage(local_storage)
                    print("[CLOUD SYNC] Đã đồng bộ dữ liệu từ Cloud về Desktop thành công!")
        except Exception as e:
            # Mất mạng hoặc Cloud chưa online -> chạy offline bình thường
            print(f"[CLOUD SYNC Info]: Không thể kết nối Cloud Server ({e}), chạy chế độ Local.")

    threading.Thread(target=worker, daemon=True).start()

def sync_toggle(task_id):
    """Báo cho Cloud biết một nhiệm vụ vừa được tick trên Desktop"""
    cloud_url = get_cloud_url()
    if not cloud_url:
        return

    def worker():
        try:
            requests.post(f"{cloud_url}/api/toggle", json={"task_id": task_id}, timeout=8)
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()

def sync_protocols_up():
    """Đẩy danh sách mục tiêu mới từ Local lên Cloud"""
    cloud_url = get_cloud_url()
    if not cloud_url:
        return

    def worker():
        try:
            protocols = app_logic.load_protocols()
            requests.post(f"{cloud_url}/api/sync", json={"protocols": protocols}, timeout=10)
            print("[CLOUD SYNC] Đã đẩy protocols lên Cloud!")
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()

def sync_config_up():
    """Đẩy cấu hình (AI key, Telegram, v.v.) từ Local lên Cloud"""
    cloud_url = get_cloud_url()
    if not cloud_url:
        return

    def worker():
        try:
            cfg = app_logic.load_config()
            clean_cfg = {k: v for k, v in cfg.items() if k != "cloud_url"}
            requests.post(f"{cloud_url}/api/sync", json={"config": clean_cfg}, timeout=10)
            print("[CLOUD SYNC] Đã đẩy config lên Cloud!")
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()

