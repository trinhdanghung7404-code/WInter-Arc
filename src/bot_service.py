import os
import re
import json
import logging
import threading
import telebot
from telebot import types
from datetime import datetime, date, timedelta
from . import app_logic

logger = logging.getLogger("WinterArcBot")

# ==============================================================================
# Helper Parsers for Natural Language & Slash Commands
# ==============================================================================
def parse_time_token(text):
    """
    Extracts time token (e.g. '7:30 am', '7:30pm', '07:30', '19:30', '7am', '8pm', '18h30', '7h').
    Returns (cleaned_text, time_hhmm_or_None)
    """
    pattern_hhmm = re.search(r'\b(0?[0-9]|1[0-9]|2[0-3])[:.h]([0-5][0-9])\s*(am|pm)?\b', text, re.IGNORECASE)
    if pattern_hhmm:
        h = int(pattern_hhmm.group(1))
        m = int(pattern_hhmm.group(2))
        ampm = (pattern_hhmm.group(3) or "").lower()
        if ampm == "pm" and h < 12:
            h += 12
        elif ampm == "am" and h == 12:
            h = 0
        time_str = f"{h:02d}:{m:02d}"
        clean = text[:pattern_hhmm.start()] + text[pattern_hhmm.end():]
        return clean.strip(), time_str

    pattern_h = re.search(r'\b(0?[0-9]|1[0-9]|2[0-3])\s*(am|pm|h)\b', text, re.IGNORECASE)
    if pattern_h:
        h = int(pattern_h.group(1))
        unit = pattern_h.group(2).lower()
        if unit == "pm" and h < 12:
            h += 12
        elif unit == "am" and h == 12:
            h = 0
        time_str = f"{h:02d}:00"
        clean = text[:pattern_h.start()] + text[pattern_h.end():]
        return clean.strip(), time_str

    return text.strip(), None

def parse_day_token(text):
    """
    Extracts day or date from text.
    Returns (cleaned_text, schedule_type, days_list, specific_dates_list, day_label)
    """
    lower = text.lower()
    
    # 1. Everyday / Daily / Hàng ngày
    everyday_match = re.search(r'\b(everyday|daily|hang ngay|hàng ngày|moi ngay|mỗi ngày|all days)\b', lower)
    if everyday_match:
        clean = text[:everyday_match.start()] + text[everyday_match.end():]
        return clean.strip(), "weekly", [0, 1, 2, 3, 4, 5, 6], [], "Everyday"

    # 2. Weekdays
    weekday_map = {
        "monday": 0, "mon": 0, "thứ 2": 0, "thu 2": 0, "t2": 0,
        "tuesday": 1, "tue": 1, "thứ 3": 1, "thu 3": 1, "t3": 1,
        "wednesday": 2, "wed": 2, "thứ 4": 2, "thu 4": 2, "t4": 2,
        "thursday": 3, "thu": 3, "thứ 5": 3, "thu 5": 3, "t5": 3,
        "friday": 4, "fri": 4, "thứ 6": 4, "thu 6": 4, "t6": 4,
        "saturday": 5, "sat": 5, "thứ 7": 5, "thu 7": 5, "t7": 5,
        "sunday": 6, "sun": 6, "chủ nhật": 6, "chu nhat": 6, "cn": 6
    }
    
    for word, w_idx in weekday_map.items():
        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        match = pattern.search(text)
        if match:
            clean = text[:match.start()] + text[match.end():]
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][w_idx]
            return clean.strip(), "weekly", [w_idx], [], f"Every {day_name}"

    # 3. Today / Tomorrow
    today_match = re.search(r'\b(today|hom nay|hôm nay)\b', lower)
    if today_match:
        clean = text[:today_match.start()] + text[today_match.end():]
        today_str = date.today().strftime("%Y-%m-%d")
        return clean.strip(), "dates", [], [today_str], f"Today ({today_str})"

    tomorrow_match = re.search(r'\b(tomorrow|ngay mai|ngày mai)\b', lower)
    if tomorrow_match:
        clean = text[:tomorrow_match.start()] + text[tomorrow_match.end():]
        tm_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        return clean.strip(), "dates", [], [tm_str], f"Tomorrow ({tm_str})"

    # 4. Specific date YYYY-MM-DD or DD/MM
    date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if date_match:
        d_str = date_match.group(1)
        clean = text[:date_match.start()] + text[date_match.end():]
        return clean.strip(), "dates", [], [d_str], d_str

    dm_match = re.search(r'\b(\d{1,2})[/.-](\d{1,2})\b', text)
    if dm_match:
        d_num = int(dm_match.group(1))
        m_num = int(dm_match.group(2))
        try:
            curr_y = date.today().year
            target_d = date(curr_y, m_num, d_num)
            if target_d < date.today():
                target_d = date(curr_y + 1, m_num, d_num)
            d_str = target_d.strftime("%Y-%m-%d")
            clean = text[:dm_match.start()] + text[dm_match.end():]
            return clean.strip(), "dates", [], [d_str], d_str
        except Exception:
            pass

    return text.strip(), None, [], [], None

def parse_task_args(raw_text):
    text = raw_text.strip()
    
    # Check explicit flags like /time ... /day ...
    time_str = None
    time_flag_match = re.search(r'/(?:time|at|gio|giờ)\s+([^\s/]+(?:\s+(?:am|pm))?)', text, re.IGNORECASE)
    if time_flag_match:
        raw_t = time_flag_match.group(1)
        _, parsed_t = parse_time_token(raw_t)
        if parsed_t:
            time_str = parsed_t
            text = text[:time_flag_match.start()] + text[time_flag_match.end():]

    if not time_str:
        text, time_str = parse_time_token(text)

    text, sched_type, days, specific_dates, day_label = parse_day_token(text)

    clean_name = re.sub(r'/(?:name|task|title)\s+', '', text, flags=re.IGNORECASE)
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    min_time_today = (now + timedelta(hours=2)).strftime("%H:%M")

    if not sched_type:
        if time_str and time_str >= min_time_today:
            sched_type = "dates"
            specific_dates = [today_str]
            day_label = f"Today ({today_str})"
        else:
            sched_type = "dates"
            specific_dates = [tomorrow_str]
            day_label = f"Tomorrow ({tomorrow_str})"

    return {
        "name": clean_name,
        "time": time_str,
        "schedule_type": sched_type,
        "days": days,
        "specific_dates": specific_dates,
        "day_label": day_label
    }


# ==============================================================================
# Telegram Bot Service
# ==============================================================================
class WinterArcBot:
    def __init__(self):
        self.bot = None
        self.thread = None
        self.is_running = False

    def get_token_and_chat(self):
        cfg = app_logic.load_config()
        tg = cfg.get("telegram", {})
        token = tg.get("bot_token", "").strip()
        chat_id = tg.get("chat_id", "").strip()
        return token, chat_id

    def build_task_keyboard(self):
        today_data = app_logic.get_today_data()
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        tasks = today_data.get("tasks", [])
        for task in tasks:
            status_icon = "✅" if task["completed"] else "⬜"
            btn_text = f"{status_icon} {task['name']}"
            callback_data = f"toggle:{task['id']}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback_data))

        action_row = [
            types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh"),
            types.InlineKeyboardButton("📝 Notes", callback_data="view_notes")
        ]
        markup.row(*action_row)
        return markup, today_data

    def start_polling(self):
        token, chat_id = self.get_token_and_chat()
        if not token:
            print("[BOT] Telegram Bot Token not configured in config.json. Bot is idle...")
            return

        try:
            self.bot = telebot.TeleBot(token, parse_mode="HTML")
            self._register_handlers()
            self._register_commands_menu()
            self.is_running = True
            
            def poll_worker():
                print("[BOT] Telegram Bot started polling...")
                try:
                    self.bot.remove_webhook()
                except Exception:
                    pass
                while self.is_running:
                    try:
                        self.bot.infinity_polling(timeout=10, long_polling_timeout=5, restart_on_change=False)
                    except Exception as e:
                        print(f"[BOT Polling Error]: {e}")
                        import time
                        time.sleep(5)

            self.thread = threading.Thread(target=poll_worker, daemon=True)
            self.thread.start()
        except Exception as e:
            print(f"[BOT Init Error]: {e}")

    def stop_polling(self):
        self.is_running = False
        if self.bot:
            try:
                self.bot.stop_polling()
            except Exception:
                pass

    def restart(self):
        self.stop_polling()
        cfg = app_logic.load_config()
        if not (cfg.get("cloud_url") or "").strip():
            self.start_polling()

    def _register_commands_menu(self):
        """Đăng ký danh sách lệnh trực tiếp lên menu gợi ý của Telegram"""
        if not self.bot:
            return
        try:
            bot_commands = [
                types.BotCommand("today", "Check-in buttons (✅ / ⬜) for today"),
                types.BotCommand("time", "Schedule protocol (e.g. /time 7:30 am Sunday Task)"),
                types.BotCommand("remind", "Quick reminder (e.g. /remind 07:30 Task)"),
                types.BotCommand("note", "Save memo for today (e.g. /note Mua sữa)"),
                types.BotCommand("notes", "View today's saved notes"),
                types.BotCommand("status", "Progress & Streak summary"),
                types.BotCommand("weekly", "Weekly performance review"),
                types.BotCommand("monthly", "30-day phase report"),
                types.BotCommand("help", "Full command guide & examples")
            ]
            self.bot.set_my_commands(bot_commands)
        except Exception as e:
            print(f"[BOT Set Commands Error]: {e}")

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            chat_id = str(message.chat.id)
            cfg = app_logic.load_config()
            cfg.setdefault("telegram", {})["chat_id"] = chat_id
            app_logic.save_config(cfg)

            keyboard, today = self.build_task_keyboard()
            welcome_msg = (
                f"❄️ <b>WINTER ARC PROTOCOL — CONNECTED!</b>\n\n"
                f"Welcome! Your desktop widget and Telegram bot are synchronized.\n"
                f"📅 <b>{today['weekday']} ({today['date_str']})</b>\n"
                f"🔥 <b>Winter Arc:</b> Day {today['day_num']}/{today['total_days']}\n"
                f"⚡ <b>Streak:</b> {today['winter_arc_streak']} days\n\n"
                f"<i>Tap below to check off your protocols:</i>"
            )
            self.bot.send_message(chat_id, welcome_msg, reply_markup=keyboard)

        @self.bot.message_handler(commands=['today', 'tasks', 'checkin', 'agenda', 'list'])
        def handle_today(message):
            keyboard, today = self.build_task_keyboard()
            tasks = today.get("tasks", [])
            rate = today.get("completion_rate", 0)
            
            header = (
                f"🎯 <b>TODAY'S PROTOCOL CHECK-IN</b>\n"
                f"📅 {today['weekday']} ({today['date_str']}) — Day <b>{today['day_num']}/{today['total_days']}</b>\n"
                f"📊 Progress: <b>{today['completed_count']}/{today['total_tasks']} ({rate}%)</b>\n\n"
                f"<i>Tap any button below to mark as completed (✅ / ⬜):</i>"
            )
            self.bot.send_message(message.chat.id, header, reply_markup=keyboard)

        @self.bot.message_handler(commands=['note', 'memo'])
        def handle_note(message):
            text = message.text
            # Remove command prefix
            note_content = re.sub(r'^/(?:note|memo)\s*', '', text, flags=re.IGNORECASE).strip()
            
            if not note_content:
                today_notes = app_logic.get_notes()
                if today_notes:
                    reply_msg = f"📝 <b>TODAY'S MEMO & NOTES:</b>\n\n{today_notes}\n\n<i>To add a note, type: <code>/note &lt;content&gt;</code></i>"
                else:
                    reply_msg = "📝 <b>No notes yet for today.</b>\n\nType <code>/note &lt;content&gt;</code> (e.g. <code>/note Mua sữa và trứng</code>) to save a memo!"
                self.bot.send_message(message.chat.id, reply_msg)
                return

            saved_all = app_logic.save_note(note_content)
            today_str = date.today().strftime("%Y-%m-%d")
            reply_msg = (
                f"📝 <b>NOTE SAVED! ({today_str})</b>\n\n"
                f"• {note_content}\n\n"
                f"<b>All Notes for Today:</b>\n{saved_all}\n\n"
                f"<i>Tip: Type /notes to view all memos anytime.</i>"
            )
            self.bot.send_message(message.chat.id, reply_msg)

        @self.bot.message_handler(commands=['notes', 'memos'])
        def handle_notes_list(message):
            today_str = date.today().strftime("%Y-%m-%d")
            today_notes = app_logic.get_notes()
            if today_notes:
                reply_msg = f"📝 <b>TODAY'S MEMO & NOTES ({today_str}):</b>\n\n{today_notes}\n\n<i>To add more, type: <code>/note &lt;content&gt;</code></i>"
            else:
                reply_msg = f"📝 <b>No notes recorded for today ({today_str}).</b>\n\nType <code>/note &lt;content&gt;</code> to save a memo anytime!"
            self.bot.send_message(message.chat.id, reply_msg)

        @self.bot.message_handler(commands=['add', 'remind', 'time', 'schedule'])
        def handle_schedule_command(message):
            text = message.text
            raw_args = re.sub(r'^/(?:add|remind|time|schedule)\s*', '', text, flags=re.IGNORECASE).strip()
            
            if not raw_args:
                help_text = (
                    f"⏰ <b>HOW TO SCHEDULE PROTOCOLS & REMINDERS:</b>\n\n"
                    f"You can easily set reminders using natural commands:\n\n"
                    f"• <code>/time 7:30 am Sunday Mua sách</code>\n"
                    f"• <code>/remind 07:30 50 Push up</code>\n"
                    f"• <code>/remind 8pm Sunday Tập Gym</code>\n"
                    f"• <code>/add Đọc sách 30p 21:00 everyday</code>\n"
                    f"• <code>/add Chạy bộ 06:00 tomorrow</code>\n\n"
                    f"<i>Try one now!</i>"
                )
                self.bot.send_message(message.chat.id, help_text)
                return

            parsed = parse_task_args(raw_args)
            task_name = parsed["name"]
            remind_time = parsed["time"] or ""
            sched_type = parsed["schedule_type"]
            days = parsed["days"]
            specific_dates = parsed["specific_dates"]
            day_label = parsed["day_label"]

            if not task_name:
                self.bot.send_message(message.chat.id, "⚠️ Please provide a protocol name! E.g.: <code>/time 7:30 am Sunday Mua sách</code>")
                return

            new_proto = {
                "name": task_name,
                "icon": "",
                "type": "todo",
                "schedule_type": sched_type,
                "days": days,
                "specific_dates": specific_dates,
                "time_desc": "",
                "remind_time": remind_time,
                "active": True
            }

            try:
                app_logic.add_protocol(new_proto)
                
                # Reload scheduler so the reminder is live immediately
                try:
                    from .scheduler_service import scheduler_instance
                    scheduler_instance.setup_schedule()
                except Exception:
                    pass

                time_display = f"⏰ <b>Reminder Time:</b> {remind_time}\n" if remind_time else "⏰ <b>Reminder Time:</b> None (Checklist only)\n"
                
                success_msg = (
                    f"🎯 <b>PROTOCOL SCHEDULED SUCCESSFULLY!</b>\n\n"
                    f"📌 <b>Protocol:</b> {task_name}\n"
                    f"{time_display}"
                    f"📅 <b>Schedule:</b> {day_label}\n\n"
                    f"<i>Synchronized with your Desktop Widget & Telegram reminders!</i>"
                )
                keyboard, _ = self.build_task_keyboard()
                self.bot.send_message(message.chat.id, success_msg, reply_markup=keyboard)

            except ValueError as ve:
                self.bot.send_message(message.chat.id, f"⚠️ <b>Schedule Notice:</b> {str(ve)}")
            except Exception as e:
                self.bot.send_message(message.chat.id, f"❌ <b>Error saving protocol:</b> {str(e)}")

        @self.bot.message_handler(commands=['del', 'delete', 'remove'])
        def handle_delete_command(message):
            text = message.text
            target = re.sub(r'^/(?:del|delete|remove)\s*', '', text, flags=re.IGNORECASE).strip().lower()
            if not target:
                self.bot.send_message(message.chat.id, "⚠️ Please provide the name of the protocol to delete. E.g.: <code>/del 50 Push up</code>")
                return

            protocols = app_logic.load_protocols()
            matched = None
            for p in protocols:
                if target in p.get("name", "").lower() or target == p.get("id", "").lower():
                    matched = p
                    break

            if not matched:
                self.bot.send_message(message.chat.id, f"⚠️ Protocol matching '<i>{target}</i>' not found.")
                return

            app_logic.delete_protocol(matched["id"])
            try:
                from .scheduler_service import scheduler_instance
                scheduler_instance.setup_schedule()
            except Exception:
                pass

            self.bot.send_message(message.chat.id, f"🗑️ Deleted protocol: <b>{matched['name']}</b>")

        @self.bot.message_handler(commands=['status'])
        def handle_status(message):
            keyboard, today = self.build_task_keyboard()
            lvl = today.get("level_info", {})
            stk = today.get("streak_info", {})
            stk_badge = stk.get("badge", f"🔥 {today['winter_arc_streak']} days")
            warning_text = f"\n⚠️ <i>{stk.get('warning_msg')}</i>\n" if stk.get("warning") else ""

            status_text = (
                f"📊 <b>WINTER ARC PROGRESS REPORT</b>\n"
                f"📅 {today['weekday']} — Day <b>{today['day_num']}/{today['total_days']}</b>\n"
                f"🏆 <b>Level:</b> {lvl.get('badge', 'LEVEL 1')} — {lvl.get('title', 'Recruit')}\n"
                f"   <i>(Day {lvl.get('day_in_level', 1)}/30 of this phase)</i>\n\n"
                f"⚡ <b>Discipline Streak:</b> {stk_badge}{warning_text}\n"
                f"🔥 <b>No Nut Streak:</b> {today['nonut_streak']} days\n"
                f"🎯 <b>Today's Protocols:</b> {today['completed_count']}/{today['total_tasks']} ({today['completion_rate']}%)\n"
                f"📖 English Studied: <b>{today['english_minutes']}/120 mins</b>\n\n"
                f"<i>Commands: /today (Check-in), /weekly, /monthly, /note</i>"
            )
            self.bot.send_message(message.chat.id, status_text, reply_markup=keyboard)

        @self.bot.message_handler(commands=['help', 'menu', 'huongdan'])
        def handle_help(message):
            help_msg = (
                f"❄️ <b>WINTER ARC — BẢNG HƯỚNG DẪN & LỆNH ĐIỀU KHIỂN:</b>\n\n"
                f"🎯 <b>Check-in & Theo dõi mục tiêu:</b>\n"
                f"• <code>/today</code> — Bật danh sách nút check-in hôm nay (✅ / ⬜)\n"
                f"• <code>/status</code> — Báo cáo tiến độ, Cấp độ Level & Chuỗi Streak\n"
                f"• <code>/weekly</code> — AI Coach đánh giá hiệu suất 7 ngày qua\n"
                f"• <code>/monthly</code> — Tổng kết chặng 30 ngày chặng đường\n\n"
                f"⏰ <b>Lên lịch & Hẹn giờ nhắc nhở qua tin nhắn:</b>\n"
                f"• <code>/time 7:30 am Sunday Mua sách</code>\n"
                f"• <code>/remind 07:30 50 Push up</code>\n"
                f"• <code>/remind 8pm Sunday Tập Gym</code>\n"
                f"• <code>/add Đọc sách 21:00 everyday</code>\n"
                f"• <code>/del 50 Push up</code> — Xóa mục tiêu khỏi lịch\n\n"
                f"📝 <b>Ghi chú & Sổ tay Memo trong ngày:</b>\n"
                f"• <code>/note Mua vitamin và sữa tươi</code> — Lưu ghi chú nhanh\n"
                f"• <code>/notes</code> — Xem lại tất cả ghi chú đã lưu hôm nay\n\n"
                f"🤖 <b>AI Discipline Coach:</b>\n"
                f"• Nhắn bất kỳ câu hỏi/tâm sự nào để trò chuyện và nhận lời khuyên từ Huấn luyện viên AI!"
            )
            keyboard, _ = self.build_task_keyboard()
            self.bot.send_message(message.chat.id, help_msg, reply_markup=keyboard)

        @self.bot.message_handler(commands=['weekly', 'week'])
        def handle_weekly(message):
            from . import ai_service
            self.bot.send_chat_action(message.chat.id, "typing")
            weekly_data = app_logic.get_weekly_summary()
            review_text = ai_service.generate_weekly_review(weekly_data)
            self.bot.send_message(message.chat.id, review_text)

        @self.bot.message_handler(commands=['monthly', 'month'])
        def handle_monthly(message):
            from . import ai_service
            self.bot.send_chat_action(message.chat.id, "typing")
            monthly_data = app_logic.get_monthly_summary()
            review_text = ai_service.generate_monthly_review(monthly_data)
            self.bot.send_message(message.chat.id, review_text)

        @self.bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
        def handle_user_chat(message):
            from . import ai_service
            if not ai_service.is_ai_enabled():
                return
            self.bot.send_chat_action(message.chat.id, "typing")
            today = app_logic.get_today_data()
            reply = ai_service.chat_with_coach(message.text, today)
            self.bot.reply_to(message, reply)

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            try:
                data = call.data
                if data.startswith("toggle:"):
                    task_id = data.split(":", 1)[1]
                    updated = app_logic.toggle_task(task_id)
                    
                    task_name = task_id
                    for t in updated.get("tasks", []):
                        if t["id"] == task_id:
                            status_str = "Completed ✅" if t["completed"] else "Unchecked ⬜"
                            task_name = f"{t['name']}: {status_str}"
                            break

                    self.bot.answer_callback_query(call.id, text=task_name)
                    
                    new_keyboard, today = self.build_task_keyboard()
                    lvl = today.get("level_info", {})
                    stk = today.get("streak_info", {})
                    stk_badge = stk.get("badge", f"🔥 {today['winter_arc_streak']} days")
                    warning_text = f"\n⚠️ <i>{stk.get('warning_msg')}</i>" if stk.get("warning") else ""

                    new_text = (
                        f"📊 <b>TODAY'S PROGRESS UPDATE</b>\n"
                        f"📅 {today['weekday']} — Day {today['day_num']}/{today['total_days']}\n"
                        f"🏆 {lvl.get('badge', 'LEVEL 1')} (Day {lvl.get('day_in_level', 1)}/30)\n"
                        f"⚡ Streak: <b>{stk_badge}</b>{warning_text}\n"
                        f"🎯 Completed: <b>{today['completed_count']}/{today['total_tasks']} ({today['completion_rate']}%)</b>\n\n"
                        f"<i>Tap below to check off your protocols:</i>"
                    )
                    self.bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=new_text,
                        reply_markup=new_keyboard
                    )

                elif data == "refresh":
                    new_keyboard, today = self.build_task_keyboard()
                    self.bot.answer_callback_query(call.id, text="Data refreshed!")
                    self.bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=new_keyboard
                    )

                elif data == "view_notes":
                    today_notes = app_logic.get_notes()
                    today_str = date.today().strftime("%Y-%m-%d")
                    if today_notes:
                        note_text = f"📝 <b>TODAY'S MEMO & NOTES ({today_str}):</b>\n\n{today_notes}\n\n<i>To add more, type: <code>/note &lt;content&gt;</code></i>"
                    else:
                        note_text = f"📝 <b>No notes for today yet ({today_str}).</b>\n\nType <code>/note &lt;content&gt;</code> to save a memo!"
                    self.bot.answer_callback_query(call.id)
                    self.bot.send_message(call.message.chat.id, note_text)

            except Exception as e:
                print(f"[Callback Error]: {e}")

    def send_broadcast(self, text, with_buttons=True):
        token, chat_id = self.get_token_and_chat()
        if not token:
            return False, "Telegram Bot Token is not configured"

        if not self.bot:
            try:
                self.bot = telebot.TeleBot(token, parse_mode="HTML")
            except Exception as e:
                return False, f"Bot initialization error: {e}"

        if not chat_id:
            try:
                updates = self.bot.get_updates(limit=10)
                if updates:
                    for u in reversed(updates):
                        msg_obj = u.message or u.edited_message or u.channel_post
                        if msg_obj and msg_obj.chat:
                            chat_id = str(msg_obj.chat.id)
                            cfg = app_logic.load_config()
                            cfg.setdefault("telegram", {})["chat_id"] = chat_id
                            app_logic.save_config(cfg)
                            print(f"[BOT] Auto-detected and saved Chat ID: {chat_id}")
                            break
            except Exception as e:
                print(f"[BOT Auto-Detect Chat ID Error]: {e}")

        if not chat_id:
            return False, "No chat detected yet! Please open your bot on Telegram and tap /start first."

        try:
            if with_buttons:
                keyboard, _ = self.build_task_keyboard()
                self.bot.send_message(chat_id, text, reply_markup=keyboard)
            else:
                self.bot.send_message(chat_id, text)
            return True, "Success"
        except Exception as e:
            return False, str(e)


bot_instance = WinterArcBot()

