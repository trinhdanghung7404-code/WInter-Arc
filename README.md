# ❄️ WINTER ARC COMMAND CENTER (WACC)

> **Hệ thống kỷ luật cá nhân 92 ngày (Winter Arc: 01/10 – 01/01)**
> Chạy Local 100% trên PC • Widget phong cách Apple Squircle Glassmorphism • Quản lý mục tiêu tùy biến không hardcode • Bắn thông báo & Check-in 2 chiều qua Telegram iPhone.

---

## 🎯 3 Cách Mở Màn Hình Quản Lý Mục Tiêu (Protocol Manager)

Bạn có thể thêm, sửa, xóa bất kỳ mục tiêu nào và lưu trực tiếp vào file `data/protocols.json` (100% không hardcode):

1. **Từ Desktop Widget:**
   * Bấm nút **`⚙️ Quản lý`** ở thanh tiêu đề bảng nhiệm vụ.
   * Hoặc bấm icon **`⚙️`** ở góc trên cùng của hộp Focus Timer.
   * Hoặc bấm nút **`⚙️ Thêm Mục Tiêu / Sửa protocols.json`** ở đáy danh sách nhiệm vụ.
2. **Từ File Explorer (1-Click):**
   * Nhấp đúp vào file **`manager.bat`** trong thư mục dự án.

---

## 🧩 3 Loại Mục Tiêu Được Hỗ Trợ

1. **`✅ To-Do trong ngày`:**
   * Các hành động làm xong lúc nào tick lúc đó (ví dụ: Chống đẩy 50 cái, chạy bộ, tập thể dục...).
2. **`⏱️ Focus Timer`:**
   * Nhiệm vụ có đồng hồ đếm ngược (Học Tiếng Anh, Làm Đồ Án, Deep Work...).
   * Chọn số phút mục tiêu (30p, 60p, 90p, 120p...). Tự động tích lũy phút học vào báo cáo ngày.
3. **`🌅 Xác nhận hôm qua (Retro)`:**
   * Dành cho **No Nut**, **Không lướt điện thoại trước khi ngủ**, **Ngủ trước 23h30**...
   * **Nguyên lý:** Phải qua 24h trọn vẹn của ngày hôm trước thì sáng hôm sau mới đánh giá được! Khi bạn tick vào mục này, hệ thống sẽ lưu kết quả vào ngày hôm qua và cộng streak mà không ảnh hưởng tới ngày hôm nay.

---

---

## 🚀 Khởi Động Nhanh & Chạy Ngầm (Zero Console Window)

Hệ thống đã được đóng gói thành các **Shortcut trên Desktop** với icon riêng sang trọng (Apple Titanium & Neon Glow) và tự động khởi động cùng Windows:

* **Desktop Shortcut: `Winter Arc.lnk`**: Khởi chạy widget chạy ngầm hoàn toàn qua `pythonw.exe` (không hiện bất kỳ cửa sổ console/cmd đen nào).
* **Desktop Shortcut: `Winter Arc Manager.lnk`**: Mở trực tiếp màn hình Quản lý mục tiêu (thêm/sửa/xóa nhiệm vụ).
* **Desktop Shortcut: `Stop Winter Arc.lnk`**: 1-click tắt toàn bộ tiến trình chạy ngầm khi muốn dừng.
* **Tự động chạy cùng Windows**: Đã được đặt vào thư mục `Startup`, mỗi khi bật máy tính lên widget sẽ tự động xuất hiện trên Desktop sẵn sàng phục vụ bạn!

Các file script tiện ích trong thư mục dự án:
* **`start_silent.vbs`**: Chạy ngầm widget hoàn toàn im lặng.
* **`stop.bat`**: Dừng toàn bộ tiến trình `pythonw.exe` của Winter Arc.
* **`manager.bat`**: Mở Protocol Manager từ dòng lệnh.
* **`set_wallpaper.bat`**: Đặt hình nền dãy núi tuyết cực quang 4K lên Desktop.

---

## 📱 Kết nối Telegram với iPhone (Nhận nhắc nhở & Tick 2 chiều)

1. Mở app **Telegram** trên iPhone, tìm kiếm: **`@BotFather`**.
2. Gửi lệnh: `/newbot` và đặt tên bot để nhận **Bot Token**.
3. Mở **Protocol Manager** (`manager.bat`) hoặc bấm nút **📲** trên widget:
   * Dán Bot Token vào ô và bấm **Lưu Cài Đặt**.
4. Trên iPhone, mở bot và bấm **Start** (hoặc gửi `/start`).
5. Bấm nút **"Bắn Thử 📲"** trên widget máy tính để kiểm tra đồng bộ!
