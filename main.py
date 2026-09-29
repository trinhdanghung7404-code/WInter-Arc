import os
import sys
import ctypes
from ctypes import Structure, c_int, byref

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "winter_arc.log")

# Đảm bảo pythonw.exe không bị crash do UnicodeEncodeError khi sys.stdout là cp1252 hoặc None
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
from src.scheduler_service import scheduler_instance

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(BASE_DIR, "ui")
INDEX_PATH = os.path.join(UI_DIR, "index.html")

# Kích thước chuẩn gọn gàng, tinh tế, chống cắt xén
WIN_WIDTH = 365
WIN_HEIGHT_EXPANDED = 600
WIN_HEIGHT_COMPACT = 310
WIN_HEIGHT = WIN_HEIGHT_EXPANDED

class MARGINS(Structure):
    _fields_ = [
        ("cxLeftWidth", c_int),
        ("cxRightWidth", c_int),
        ("cyTopHeight", c_int),
        ("cyBottomHeight", c_int)
    ]

# Cấu hình chuẩn 64-bit cho SetWindowPos và DWM Glass Transparency
user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
dwmapi.DwmExtendFrameIntoClientArea.argtypes = [ctypes.c_void_p, ctypes.POINTER(MARGINS)]
dwmapi.DwmExtendFrameIntoClientArea.restype = ctypes.c_int
user32.SetWindowPos.argtypes = [
    ctypes.c_void_p, # hWnd
    ctypes.c_void_p, # hWndInsertAfter
    ctypes.c_int,    # X
    ctypes.c_int,    # Y
    ctypes.c_int,    # cx
    ctypes.c_int,    # cy
    ctypes.c_uint    # uFlags
]
user32.SetWindowPos.restype = ctypes.c_bool

user32.ReleaseCapture.argtypes = []
user32.ReleaseCapture.restype = ctypes.c_int
user32.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
user32.SendMessageW.restype = ctypes.c_void_p

user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
user32.ShowWindow.restype = ctypes.c_bool
user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
user32.IsWindowVisible.restype = ctypes.c_bool
user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
user32.SetForegroundWindow.restype = ctypes.c_bool

HWND_TOPMOST = ctypes.c_void_p(-1)
HWND_NOTOPMOST = ctypes.c_void_p(-2)
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

class DesktopApi:
    def __init__(self, window_holder, tray_holder=None):
        self._window_holder = window_holder
        self._tray_holder = tray_holder if tray_holder is not None else {}
        self.is_on_top = True

    def _get_win(self):
        return self._window_holder.get("window")

    def toggle_widget_visibility(self):
        try:
            win = self._get_win()
            if win and hasattr(win, 'native'):
                hwnd = ctypes.c_void_p(win.native.Handle.ToInt64())
                is_vis = user32.IsWindowVisible(hwnd)
                if is_vis:
                    user32.ShowWindow(hwnd, 0) # SW_HIDE
                else:
                    user32.ShowWindow(hwnd, 5) # SW_SHOW
                    user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"[Toggle Visibility Error]: {e}")
        return True

    def hide_window(self):
        try:
            win = self._get_win()
            if win and hasattr(win, 'native'):
                hwnd = ctypes.c_void_p(win.native.Handle.ToInt64())
                user32.ShowWindow(hwnd, 0) # SW_HIDE
                tray = self._tray_holder.get("tray")
                if tray:
                    try:
                        tray.notify("Widget đã được thu gọn xuống khay hệ thống. Bấm vào icon ở đây để mở lại!", "Winter Arc")
                    except Exception:
                        pass
        except Exception as e:
            print(f"[Hide Error]: {e}")
        return True

    def show_window(self):
        try:
            win = self._get_win()
            if win and hasattr(win, 'native'):
                hwnd = ctypes.c_void_p(win.native.Handle.ToInt64())
                user32.ShowWindow(hwnd, 5) # SW_SHOW
                user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"[Show Error]: {e}")
        return True

    def start_drag(self):
        """
        Kéo cửa sổ bằng native Windows WM_NCLBUTTONDOWN (HTCAPTION).
        Chỉ 1 lần gọi duy nhất từ mousedown, Windows tự xử lý kéo mượt 100%,
        0ms latency, không flood IPC mousemove, chống lag tuyệt đối.
        """
        try:
            win = self._get_win()
            if win and hasattr(win, 'native'):
                hwnd = ctypes.c_void_p(win.native.Handle.ToInt64())
                user32.ReleaseCapture()
                user32.SendMessageW(hwnd, 0x00A1, ctypes.c_void_p(2), ctypes.c_void_p(0))
        except Exception as e:
            print(f"[Drag Error]: {e}")
        return True

    def move_delta(self, dx, dy):
        return True

    def get_today(self):
        return app_logic.get_today_data()

    def toggle_task(self, task_id):
        return app_logic.toggle_task(task_id)

    def add_focus_minutes(self, task_type, minutes):
        return app_logic.add_focus_time(task_type, minutes)

    def toggle_pin(self):
        """Bật/tắt ghim Always-on-Top an toàn 100% qua Win32 SetWindowPos (không block UI thread)"""
        self.is_on_top = not self.is_on_top
        try:
            win = self._get_win()
            if win and hasattr(win, 'native'):
                hwnd = ctypes.c_void_p(win.native.Handle.ToInt64())
                target_hwnd = HWND_TOPMOST if self.is_on_top else HWND_NOTOPMOST
                u_flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW
                res = user32.SetWindowPos(hwnd, target_hwnd, 0, 0, 0, 0, u_flags)
                print(f"[PIN] Ghim: {self.is_on_top}, SetWindowPos: {res}")
        except Exception as e:
            print(f"[Window Pin Error]: {e}")
        return self.is_on_top

    def get_pin_status(self):
        return self.is_on_top

    def set_compact_mode(self, is_compact):
        """
        Chuyển đổi kích thước cửa sổ giữa Chế độ Thu Gọn (310px) và Mở Rộng (540px).
        Tự động chống tràn viền màn hình (Anti-clipping), phản hồi 0ms cực mượt.
        """
        try:
            win = self._get_win()
            if win and hasattr(win, 'native'):
                hwnd = ctypes.c_void_p(win.native.Handle.ToInt64())
                rect = (ctypes.c_long * 4)()
                user32.GetWindowRect(hwnd, rect)
                curr_x = rect[0]
                curr_y = rect[1]
                
                new_w = WIN_WIDTH
                new_h = WIN_HEIGHT_COMPACT if is_compact else WIN_HEIGHT_EXPANDED
                
                screen_w, screen_h = get_screen_bounds()
                if not is_compact and (curr_y + new_h > screen_h - 40):
                    curr_y = max(10, screen_h - 40 - new_h)
                    user32.SetWindowPos(hwnd, None, curr_x, curr_y, new_w, new_h, SWP_NOZORDER | SWP_NOACTIVATE)
                else:
                    user32.SetWindowPos(hwnd, None, 0, 0, new_w, new_h, SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE)
        except Exception as e:
            print(f"[Set Compact Error]: {e}")
        return is_compact

    def get_config(self):
        return app_logic.load_config()

    def save_config(self, cfg):
        app_logic.save_config(cfg)
        bot_instance.restart()
        scheduler_instance.start()
        return True

    def open_manager(self):
        """Mở màn hình quản lý mục tiêu chuyên dụng (chạy độc lập, không block widget)"""
        try:
            import subprocess
            manager_script = os.path.join(BASE_DIR, "manager_app.py")
            python_exe = sys.executable
            subprocess.Popen([python_exe, manager_script])
            return True
        except Exception as e:
            print(f"[Open Manager Error]: {e}")
            return False

    def get_protocols(self):
        return app_logic.load_protocols()

    def add_protocol(self, item):
        return app_logic.add_protocol(item)

    def delete_protocol(self, item_id):
        return app_logic.delete_protocol(item_id)

    def update_protocol(self, item_id, fields):
        return app_logic.update_protocol(item_id, fields)

    def send_test_telegram(self):
        success, msg = bot_instance.send_broadcast(
            "⚡ <b>[TEST CONNECT] WINTER ARC WIDGETS ĐÃ KẾT NỐI!</b>\n\n"
            "Thông báo từ máy tính của bạn đã bắn thành công tới iPhone!\n"
            "Từ bây giờ các mốc 07:00, 18:00, 20:25, 22:30 sẽ tự động nhắc nhở bạn.",
            with_buttons=True
        )
        return {"success": success, "message": msg}

def get_screen_bounds():
    try:
        import clr
        clr.AddReference("System.Windows.Forms")
        from System.Windows.Forms import Screen
        area = Screen.PrimaryScreen.WorkingArea
        return area.Width, area.Height
    except Exception:
        return 1920, 1080

def main():
    cfg = app_logic.load_config()
    cloud_url = (cfg.get("cloud_url") or "").strip()

    if cloud_url:
        print(f"[SYSTEM] Chế độ Cloud đang bật ({cloud_url}). Bot & Scheduler được ủy quyền cho Render chạy 24/7.")
        # Kéo dữ liệu mới nhất từ Cloud về
        try:
            from src import cloud_sync
            cloud_sync.sync_down()
        except Exception:
            pass
    else:
        print("[SYSTEM] Chế độ Local: Khởi chạy Bot Telegram & Scheduler trên máy tính...")
        bot_instance.start_polling()
        scheduler_instance.start()


    screen_w, screen_h = get_screen_bounds()
    pos_x = max(20, screen_w - WIN_WIDTH - 25)
    pos_y = 25

    window_holder = {}
    tray_holder = {}
    api = DesktopApi(window_holder, tray_holder)

    window = webview.create_window(
        title="Winter Arc iOS Widgets",
        url=INDEX_PATH,
        width=WIN_WIDTH,
        height=WIN_HEIGHT,
        x=pos_x,
        y=pos_y,
        resizable=False,
        frameless=True,
        easy_drag=False,
        on_top=True,
        transparent=True,
        background_color='#000000',
        js_api=api
    )
    window_holder["window"] = window

    def setup_pystray():
        try:
            import pystray
            from pystray import MenuItem as item
            from PIL import Image

            def toggle_action(icon, item):
                api.toggle_widget_visibility()

            def open_mgr_action(icon, item):
                api.open_manager()

            def set_wp_action(icon, item):
                try:
                    import subprocess
                    subprocess.Popen([
                        r"C:\Users\Admin\Documents\Module4-main\.venv\Scripts\pythonw.exe",
                        os.path.join(BASE_DIR, "set_wallpaper.py")
                    ], cwd=BASE_DIR)
                    icon.notify("Đã cập nhật hình nền Winter Arc 4K!", "Winter Arc")
                except Exception as ex:
                    print(f"[Tray Wallpaper Error]: {ex}")

            def quit_action(icon, item):
                try:
                    icon.stop()
                except Exception:
                    pass
                win = window_holder.get("window")
                if win:
                    try:
                        win.destroy()
                    except Exception:
                        pass
                import os
                os._exit(0)

            menu = pystray.Menu(
                item('👁️ Hiện / Ẩn Desktop Widget', toggle_action, default=True),
                item('⚙️ Quản lý mục tiêu (Protocol Manager)', open_mgr_action),
                item('❄️ Đổi hình nền Winter Arc 4K', set_wp_action),
                pystray.Menu.SEPARATOR,
                item('🚪 Thoát hoàn toàn', quit_action)
            )

            icon_img = Image.open(os.path.join(BASE_DIR, "app_icon.ico"))
            tray_icon = pystray.Icon("WinterArc", icon_img, "Winter Arc Command Center", menu)
            tray_holder["tray"] = tray_icon
            tray_icon.run_detached()
            print("[SYSTEM TRAY] Pystray Icon đã gắn vào khay hệ thống thành công!")
            try:
                tray_icon.notify("Widget đang chạy ngầm trong khay hệ thống. Click icon ở đây để Ẩn / Hiện widget!", "Winter Arc đã khởi động!")
            except Exception:
                pass
        except Exception as e:
            print(f"[Pystray Error]: {e}")

    def on_shown():
        try:
            if hasattr(window, 'native'):
                form = window.native
                hwnd = ctypes.c_void_p(form.Handle.ToInt64())
                margins = MARGINS(-1, -1, -1, -1)
                dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
                import clr
                clr.AddReference("System.Drawing")
                from System.Drawing import Color
                form.BackColor = Color.Black

                def on_closing(sender, e):
                    try:
                        e.Cancel = True
                        api.hide_window()
                    except Exception:
                        pass

                form.FormClosing += on_closing
        except Exception as e:
            print(f"[DWM / Close Error]: {e}")

    window.events.shown += on_shown

    # Khởi động Tray Icon trên luồng Win32 riêng biệt, chống xung đột WebView2 100%
    setup_pystray()

    try:
        webview.start(debug=False)
    finally:
        if "tray" in tray_holder:
            try:
                tray_holder["tray"].stop()
            except Exception:
                pass
        bot_instance.stop_polling()
        scheduler_instance.stop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"\n[FATAL ERROR] {e}\n")
            traceback.print_exc(file=f)
