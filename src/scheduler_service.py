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

def job_morning_briefing():
    today = app_logic.get_today_data()
    from . import ai_service
    
    cfg = app_logic.load_config()
    use_ai = cfg.get("ai", {}).get("use_ai_daily_briefings", True)
    ai_msg = ai_service.generate_daily_morning_briefing(today) if (use_ai and ai_service.is_ai_enabled()) else None
    
    if ai_msg:
        msg = f"{ai_msg}\n\n<i>Tap below to check-in your protocols:</i>"
    else:
        tasks = today.get("tasks", [])
        if tasks:
            task_list_str = "\n".join([f"• <b>{t['name']}</b>" for t in tasks])
        else:
            task_list_str = "• <i>No specific protocols scheduled for today. Rest & maintain discipline.</i>"

        msg = (
            f"🌅 <b>[07:00 AM] — MORNING DISCIPLINE BRIEFING</b>\n\n"
            f"Wake up warrior! Day <b>{today['day_num']}/{today['total_days']}</b> of Winter Arc.\n\n"
            f"<b>Today's Scheduled Protocols ({len(tasks)} items):</b>\n"
            f"{task_list_str}\n\n"
            f"Zero excuses. Begin execution now!"
        )
    bot_instance.send_broadcast(msg, with_buttons=True)

def job_evening_briefing():
    today = app_logic.get_today_data()
    tasks = today.get("tasks", [])
    pending = [t for t in tasks if not t.get("completed")]
    
    if pending:
        pending_str = "\n".join([f"• <b>{t['name']}</b>" for t in pending])
        detail = f"<b>Remaining Protocols to Finish Tonight ({len(pending)}):</b>\n{pending_str}\n\nStay focused, zero mindless doomscrolling, conquer the rest of your day!"
    else:
        detail = "🎯 <b>All protocols completed today! Outstanding discipline! Keep the momentum!</b>"

    msg = (
        f"🌆 <b>[18:00 PM] — EVENING PROGRESS REPORT</b>\n\n"
        f"{detail}\n\n"
        f"<i>Current Progress: {today['completed_count']}/{today['total_tasks']} protocols ({today['completion_rate']}%).</i>"
    )
    bot_instance.send_broadcast(msg, with_buttons=True)

def job_workout_reminder():
    today = app_logic.get_today_data()
    tasks = today.get("tasks", [])
    workout_task = next((t for t in tasks if any(k in t.get("name", "").lower() or k in t.get("id", "").lower() for k in ["workout", "gym", "tập", "the_duc"])), None)
    
    if not workout_task:
        return # Skip workout reminder if no workout is scheduled today
        
    if workout_task.get("completed"):
        return # Already finished

    msg = (
        f"⚡ <b>[20:25] — 5 MINUTES TO WORKOUT SESSION!</b>\n\n"
        f"Protocol: <b>{workout_task.get('name')}</b>\n"
        f"Put the phone down, play your workout music, stretch, and give 100% intensity for tonight's session!"
    )
    bot_instance.send_broadcast(msg, with_buttons=True)

def job_night_review():
    today = app_logic.get_today_data()
    from . import ai_service
    
    cfg = app_logic.load_config()
    use_ai = cfg.get("ai", {}).get("use_ai_daily_briefings", True)
    ai_msg = ai_service.generate_daily_night_review(today) if (use_ai and ai_service.is_ai_enabled()) else None
    
    if ai_msg:
        msg = f"{ai_msg}\n\n<i>Daily Check-in Buttons:</i>"
    else:
        lvl = today.get("level_info", {})
        stk = today.get("streak_info", {})
        rate = today.get("completion_rate", 0)

        # 1. Streak Evaluation
        if rate == 100:
            streak_result = "🔥 <b>OUTSTANDING: 100% Completion achieved! Flame Streak ignited!</b>"
        elif rate >= 50:
            streak_result = f"⚪ <b>WARNING: {rate}% completed (Grey Streak: {stk.get('consecutive_grey', 1)}/3). Push harder tomorrow to protect your streak!</b>"
        else:
            streak_result = "💀 <b>LESS THAN 50% COMPLETED! Streak has reset to 0! Rebound tomorrow!</b>"

        # 2. Level Milestone
        level_milestone_msg = ""
        day_in_lvl = lvl.get("day_in_level", 1)
        current_lvl = lvl.get("level", 1)

        if day_in_lvl == 30:
            next_lvl = current_lvl + 1
            level_milestone_msg = (
                f"\n\n🎉 <b>CONGRATULATIONS WARRIOR — 30-DAY PHASE COMPLETE!</b>\n"
                f"🏆 You conquered <b>{lvl.get('title')}</b>!\n"
                f"Tomorrow you advance to <b>LEVEL {next_lvl}</b>!"
            )
        elif day_in_lvl == 1 and today["day_num"] > 1:
            level_milestone_msg = (
                f"\n\n👑 <b>WELCOME TO {lvl.get('badge')}!</b>\n"
                f"<i>{lvl.get('desc')}</i>"
            )

        msg = (
            f"🌙 <b>[22:30] — DAILY REVIEW & DISCIPLINE CLOSE</b>\n\n"
            f"📅 Day <b>{today['day_num']}/{today['total_days']}</b> ({today['weekday']})\n"
            f"🏆 Level: <b>{lvl.get('badge')}</b> — {lvl.get('title')}\n"
            f"🎯 Progress: <b>{today['completed_count']}/{today['total_tasks']} ({rate}%)</b>\n\n"
            f"{streak_result}\n\n"
            f"• English: {today['english_minutes']}/120 mins\n"
            f"• No Nut Streak: {today['nonut_streak']} days 🔥"
            f"{level_milestone_msg}"
        )
    bot_instance.send_broadcast(msg, with_buttons=True)


def job_weekly_review():
    from . import ai_service
    weekly_data = app_logic.get_weekly_summary()
    msg = ai_service.generate_weekly_review(weekly_data)
    bot_instance.send_broadcast(msg, with_buttons=False)

def job_custom_protocol_reminder(proto_id):
    """Telegram reminder for custom scheduled protocol time"""
    try:
        protocols = app_logic.load_protocols()
        proto = next((p for p in protocols if p.get("id") == proto_id), None)
        if not proto or proto.get("active") is False:
            return

        today_date = date.today()
        today_str = today_date.strftime("%Y-%m-%d")
        weekday_idx = today_date.weekday()

        schedule_type = proto.get("schedule_type", "weekly")
        schedule_days = proto.get("days", [0, 1, 2, 3, 4, 5, 6])
        specific_dates = proto.get("specific_dates", [])

        is_scheduled_today = False
        if schedule_type == "dates":
            is_scheduled_today = (today_str in specific_dates)
        elif schedule_type == "both":
            is_scheduled_today = (weekday_idx in (schedule_days or [])) or (today_str in specific_dates)
        else:
            if specific_dates and (schedule_days is None or len(schedule_days) == 0):
                is_scheduled_today = (today_str in specific_dates)
            else:
                is_scheduled_today = (weekday_idx in (schedule_days or [])) or (today_str in specific_dates)

        if not is_scheduled_today:
            return

        today = app_logic.get_today_data()
        task_in_today = next((t for t in today.get("tasks", []) if t["id"] == proto_id), None)
        if task_in_today and task_in_today.get("completed"):
            print(f"[SCHEDULER] Skipping reminder for '{proto.get('name')}' as it's already completed.")
            return

        remind_time = proto.get("remind_time", "")
        name = proto.get("name", "Protocol")
        icon = proto.get("icon", "🎯")
        time_desc = proto.get("time_desc", "")

        desc_text = f"\n📌 <i>Note: {time_desc}</i>" if time_desc else ""

        msg = (
            f"⏰ <b>[{remind_time}] — TIME FOR: {name.upper()}!</b>\n\n"
            f"Protocol: <b>{name}</b>{desc_text}\n\n"
            f"⚡ <i>Discipline builds identity — execute now!</i>\n"
            f"<i>Tap below to check off immediately:</i>"
        )
        print(f"[SCHEDULER] Sending reminder for: {name} at {remind_time}")
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
        
        t_morning = times.get("morning_briefing") or times.get("morning_pushups", "07:00")
        t_evening = times.get("evening_briefing", "18:00")
        t_workout = times.get("workout_reminder", "20:25")
        t_night = times.get("night_review", "22:30")

        schedule.every().day.at(t_morning).do(job_morning_briefing)
        schedule.every().day.at(t_evening).do(job_evening_briefing)
        schedule.every().day.at(t_workout).do(job_workout_reminder)
        schedule.every().day.at(t_night).do(job_night_review)
        schedule.every().sunday.at("21:00").do(job_weekly_review)

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

