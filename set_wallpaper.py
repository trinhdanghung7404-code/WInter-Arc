import os
import sys
import ctypes

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def set_wallpaper():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    wallpaper_path = os.path.join(current_dir, "winter_arc_wallpaper.jpg")
    
    if not os.path.exists(wallpaper_path):
        print(f"[ERROR] Không tìm thấy file: {wallpaper_path}")
        return False

    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDWININICHANGE = 0x02

    res = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        wallpaper_path,
        SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
    )
    if res:
        print("[SUCCESS] Đã cài đặt hình nền Winter Arc cho màn hình chính thành công!")
        return True
    else:
        print("[FAILED] Không thể đặt hình nền.")
        return False

if __name__ == "__main__":
    set_wallpaper()
