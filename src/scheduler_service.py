import os
import time

# Ép múi giờ hệ thống sang Giờ Việt Nam (Asia/Ho_Chi_Minh - GMT+7) trên server Linux/Cloud
os.environ["TZ"] = "Asia/Ho_Chi_Minh"
if hasattr(time, "tzset"):
    try:
        time.tzset()
    except Exception:
        pass

import threading
import schedule
from datetime import date, datetime
from . import app_logic
from .bot_service import bot_instance

def job_morning_pushups():
    today = app_logic.get_today_data()
    msg = (
        f"🌅 <b>[07:00 SÁNG] — 50 CÁI CHỐNG ĐẨY KHỞI ĐỘNG!</b>\n\n"
        f"Dậy đi chiến binh! Ngày thứ <b>{today['day_num']}/{today['total_days']}</b> của Winter Arc.\n"
        f"Làm ngay 50 cái chống đẩy để kích hoạt cơ thể trước khi chuẩn bị lên công ty.\n"
        f"Không tìm lý do, bắt đầu ngay!"
    )
    bot_instance.send_broadcast(msg, with_buttons=True)

def job_evening_briefing():
    today = app_logic.get_today_data()
    weekday_idx = date.today().weekday()
    
    if weekday_idx in (1, 3, 5): # T3, T5, T7
        detail = "💻 <b>Trọng tâm tối nay: LÀM ĐỒ ÁN + 2 TIẾNG TIẾNG ANH.</b>\nTối ưu hóa từng phút, không lướt điện thoại vô bổ!"
    else: # T2, T4, T6, CN
        detail = "🏋️ <b>Trọng tâm tối nay: THỂ DỤC (20:30 – 21:30) + 2 TIẾNG TIẾNG ANH.</b>\nĂn uống nhẹ nhàng để sẵn sàng cho ca tập 20:30!"

    msg = (
        f"🌆 <b>[18:00 TAN LÀM] — KẾ HOẠCH TÁC CHIẾN TỐI NAY</b>\n\n"
        f"{detail}\n\n"
        f"<i>Tiến độ hiện tại: {today['completed_count']}/{today['total_tasks']} nhiệm vụ.</i>"
    )
    bot_instance.send_broadcast(msg, with_buttons=True)

def job_workout_reminder():
    weekday_idx = date.today().weekday()
    if weekday_idx in (0, 2, 4, 6): # Chỉ nhắc vào các tối rảnh T2, T4, T6, CN
        msg = (
            f"⚡ <b>[20:25] — 5 PHÚT NỮA VÀO CA TẬP THỂ DỤC!</b>\n\n"
            f"Khung giờ: <b>20:30 – 21:30</b>.\n"
            f"Bỏ điện thoại xuống, bật playlist nhạc tập, khởi động khớp và chiến hết mình trong 60 phút!"
        )
        bot_instance.send_broadcast(msg, with_buttons=True)

def job_night_review():
    today = app_logic.get_today_data()
    lvl = today.get("level_info", {})
    stk = today.get("streak_info", {})
    rate = today.get("completion_rate", 0)

    # 1. Đánh giá chuỗi hôm nay
    if rate == 100:
        streak_result = "🔥 <b>XUẤT SẮC: Bạn đã hoàn thành 100% nhiệm vụ! Đạt Chuỗi Lửa bất bại!</b>"
    elif rate >= 50:
        streak_result = f"⚪ <b>CẢNH BÁO: Bạn hoàn thành {rate}% (Chuỗi Xám: {stk.get('consecutive_grey', 1)}/3). Cần cố gắng hơn để giữ chuỗi!</b>"
    else:
        streak_result = "💀 <b>BẠN ĐÃ KHÔNG HOÀN THÀNH ĐỦ 50% NHIỆM VỤ! Chuỗi kỷ luật đã bị đặt lại về 0!</b>"

    # 2. Kiểm tra thăng cấp Level (Ngày cuối cùng của Level: ngày 30, 60 hoặc 90)
    level_milestone_msg = ""
    day_in_lvl = lvl.get("day_in_level", 1)
    current_lvl = lvl.get("level", 1)

    if day_in_lvl == 30:
        next_lvl = current_lvl + 1
        level_milestone_msg = (
            f"\n\n🎉 <b>CHÚC MỪNG CHIẾN BINH — HOÀN THÀNH CHẶNG 30 NGÀY!</b>\n"
            f"🏆 Bạn đã hoàn thành toàn bộ chặng <b>{lvl.get('title')}</b>!\n"
            f"Ngày mai bạn sẽ chính thức bước chân vào <b>LEVEL {next_lvl}</b> với bản lĩnh kiên cường hơn!"
        )
    elif day_in_lvl == 1 and today["day_num"] > 1:
        level_milestone_msg = (
            f"\n\n👑 <b>CHÀO ĐÓN BẠN ĐẾN VỚI {lvl.get('badge')}!</b>\n"
            f"<i>{lvl.get('desc')}</i>"
        )

    msg = (
        f"🌙 <b>[22:30] — TỔNG KẾT NGÀY & KHÓA SỔ KỶ LUẬT</b>\n\n"
        f"📅 Ngày <b>{today['day_num']}/{today['total_days']}</b> ({today['weekday']})\n"
        f"🏆 Cấp độ: <b>{lvl.get('badge')}</b> — {lvl.get('title')}\n"
        f"🎯 Tiến độ hôm nay: <b>{today['completed_count']}/{today['total_tasks']} ({rate}%)</b>\n\n"
        f"{streak_result}\n\n"
        f"• Tiếng Anh: {today['english_minutes']}/120 phút\n"
        f"• No Nut Streak: {today['nonut_streak']} ngày 🔥"
        f"{level_milestone_msg}"
    )
    bot_instance.send_broadcast(msg, with_buttons=True)


def job_custom_protocol_reminder(proto_id):
    """Bắn thông báo Telegram khi đến giờ hẹn riêng của một mục tiêu To-Do/Protocol"""
    try:
        protocols = app_logic.load_protocols()
        proto = next((p for p in protocols if p.get("id") == proto_id), None)
        if not proto or proto.get("active") is False:
            return

        # Kiểm tra xem hôm nay có nằm trong lịch tác chiến của task không
        weekday_idx = date.today().weekday()
        schedule_days = proto.get("days", [0, 1, 2, 3, 4, 5, 6])
        if weekday_idx not in schedule_days:
            return

        # Kiểm tra xem mục tiêu này hôm nay đã hoàn thành chưa (nếu xong rồi thì không làm phiền)
        today = app_logic.get_today_data()
        task_in_today = next((t for t in today.get("tasks", []) if t["id"] == proto_id), None)
        if task_in_today and task_in_today.get("completed"):
            print(f"[SCHEDULER] Bỏ qua nhắc nhở '{proto.get('name')}' vì đã hoàn thành trước đó.")
            return

        remind_time = proto.get("remind_time", "")
        name = proto.get("name", "Nhiệm vụ kỷ luật")
        icon = proto.get("icon", "🎯")
        time_desc = proto.get("time_desc", "")

        desc_text = f"\n📌 <i>Ghi chú: {time_desc}</i>" if time_desc else ""

        msg = (
            f"⏰ <b>[{remind_time}] — ĐẾN GIỜ: {name.upper()}!</b>\n\n"
            f"{icon} Mục tiêu: <b>{name}</b>{desc_text}\n\n"
            f"⚡ <i>Kỷ luật tạo nên bản lĩnh — Bắt đầu ngay bây giờ!</i>\n"
            f"<i>Bấm nút bên dưới để xác nhận hoàn thành ngay trên iPhone:</i>"
        )
        print(f"[SCHEDULER] Đang gửi thông báo Telegram cho mục tiêu: {name} (Lúc {remind_time})")
        bot_instance.send_broadcast(msg, with_buttons=True)
    except Exception as e:
        print(f"[SCHEDULER Protocol Reminder Error]: {e}")

class SchedulerService:
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.last_proto_mtime = 0

    def setup_schedule(self):
        """Đọc config và danh sách protocols để lên lịch tất cả các mốc thông báo"""
        schedule.clear()

        # 1. Các mốc thông báo tổng thể
        cfg = app_logic.load_config()
        times = cfg.get("schedule", {})
        
        t_morning = times.get("morning_pushups", "07:00")
        t_evening = times.get("evening_briefing", "18:00")
        t_workout = times.get("workout_reminder", "20:25")
        t_night = times.get("night_review", "22:30")

        schedule.every().day.at(t_morning).do(job_morning_pushups)
        schedule.every().day.at(t_evening).do(job_evening_briefing)
        schedule.every().day.at(t_workout).do(job_workout_reminder)
        schedule.every().day.at(t_night).do(job_night_review)

        # 2. Các mốc giờ nhắc nhở riêng của từng protocol (remind_time)
        custom_count = 0
        try:
            protocols = app_logic.load_protocols()
            for p in protocols:
                if p.get("active") is False:
                    continue
                remind_t = (p.get("remind_time") or "").strip()
                # Kiểm tra định dạng HH:MM
                if remind_t and len(remind_t) == 5 and ":" in remind_t:
                    pid = p.get("id")
                    schedule.every().day.at(remind_t).do(job_custom_protocol_reminder, proto_id=pid)
                    custom_count += 1
        except Exception as e:
            print(f"[SCHEDULER Setup Custom Error]: {e}")

        print(f"[SCHEDULER] Đã nạp lịch nhắc Telegram: 4 mốc hệ thống + {custom_count} mục tiêu có giờ riêng.")

    def start(self):
        self.setup_schedule()
        self.is_running = True
        
        def run_loop():
            while self.is_running:
                # Tự động reload lại schedule nếu protocols.json hoặc config.json có thay đổi
                try:
                    if os.path.exists(app_logic.PROTOCOLS_PATH):
                        mtime = os.path.getmtime(app_logic.PROTOCOLS_PATH)
                        if self.last_proto_mtime != 0 and mtime != self.last_proto_mtime:
                            print("[SCHEDULER] Phát hiện protocols.json thay đổi, đang tự động nạp lại lịch...")
                            self.setup_schedule()
                        self.last_proto_mtime = mtime
                except Exception:
                    pass

                schedule.run_pending()
                time.sleep(15)

        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False

scheduler_instance = SchedulerService()

