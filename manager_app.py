import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "manager.log")

class SafeStream:
    def __init__(self, filepath):
        self.filepath = filepath
        self._f = None
        try:
            self._f = open(filepath, "a", encoding="utf-8", errors="replace")
        except Exception:
            pass

    def write(self, text):
        if self._f:
            try:
                self._f.write(text)
                self._f.flush()
            except Exception:
                pass

    def flush(self):
        if self._f:
            try:
                self._f.flush()
            except Exception:
                pass

try:
    if sys.stdout is None or getattr(sys.stdout, 'encoding', None) != 'utf-8':
        sys.stdout = SafeStream(LOG_FILE)
    if sys.stderr is None or getattr(sys.stderr, 'encoding', None) != 'utf-8':
        sys.stderr = SafeStream(LOG_FILE)
except Exception:
    pass

import webview
from src import app_logic
from src.bot_service import bot_instance

UI_DIR = os.path.join(BASE_DIR, "ui")
MANAGER_HTML = os.path.join(UI_DIR, "manager.html")

class ManagerApi:
    def get_protocols(self):
        """Lấy danh sách toàn bộ mục tiêu từ data/protocols.json"""
        return app_logic.load_protocols()

    def get_day_data(self, date_str=None):
        """Lấy dữ liệu và danh sách nhiệm vụ của một ngày cụ thể"""
        return app_logic.get_today_data(date_str)

    def add_protocol(self, item):
        """Thêm mục tiêu mới và lưu trực tiếp vào data/protocols.json"""
        return app_logic.add_protocol(item)

    def delete_protocol(self, item_id):
        """Xóa mục tiêu khỏi data/protocols.json"""
        return app_logic.delete_protocol(item_id)

    def update_protocol(self, item_id, fields):
        """Cập nhật thuộc tính mục tiêu trong data/protocols.json"""
        return app_logic.update_protocol(item_id, fields)

    def get_config(self):
        """Lấy cấu hình chung và Telegram từ data/config.json"""
        return app_logic.load_config()

    def save_config(self, cfg):
        """Lưu cấu hình chung và cập nhật Telegram Bot"""
        app_logic.save_config(cfg)
        try:
            bot_instance.restart()
        except Exception:
            pass
        return True

    def send_test_telegram(self):
        """Gửi tin nhắn test tới Telegram iPhone"""
        success, msg = bot_instance.send_broadcast(
            "⚡ <b>[TEST] PROTOCOL MANAGER TEST PING</b>\n\n"
            "Your discipline protocols have been synchronized.",
            with_buttons=True
        )
        return {"success": success, "message": msg}

    def test_ai_coach(self, custom_prompt=None):
        """Kiểm tra kết nối AI Coach và gửi thông điệp thử sang Telegram"""
        from src import ai_service
        success, reply = ai_service.test_ai_connection(custom_prompt)
        if success:
            bot_instance.send_broadcast(
                f"🛡️ <b>[AI DISCIPLINE COACH]</b>\n\n{reply}",
                with_buttons=False
            )
            return {"success": True, "message": reply}
        else:
            return {"success": False, "message": reply}

    def get_weather(self, force_refresh=False):
        return app_logic.get_weather_data(force_refresh)

    def search_city(self, query):
        return app_logic.search_city_locations(query)

    def set_weather_location(self, city, lat=None, lon=None):
        return app_logic.update_weather_location(city, lat, lon)

def main():
    print("[MANAGER] Starting Winter Arc Protocol Manager...")
    api = ManagerApi()
    
    window = webview.create_window(
        title="Winter Arc Protocol Manager // Discipline Protocols",
        url=MANAGER_HTML,
        width=980,
        height=760,
        resizable=True,
        min_size=(780, 580),
        js_api=api
    )
    
    webview.start(debug=False)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"\n[FATAL ERROR] {e}\n")
            traceback.print_exc(file=f)
