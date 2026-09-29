import os
import json
import logging
import threading
import telebot
from telebot import types
from datetime import date
from . import app_logic

logger = logging.getLogger("WinterArcBot")

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
        
        for task in today_data["tasks"]:
            status_icon = "✅" if task["completed"] else "⬜"
            btn_text = f"{status_icon} {task['icon']} {task['name']}"
            callback_data = f"toggle:{task['id']}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback_data))

        markup.add(types.InlineKeyboardButton("🔄 Làm mới trạng thái", callback_data="refresh"))
        return markup, today_data

    def start_polling(self):
        token, chat_id = self.get_token_and_chat()
        if not token:
            print("[BOT] Chưa cấu hình Telegram Bot Token trong config.json. Bot đang chờ...")
            return

        try:
            self.bot = telebot.TeleBot(token, parse_mode="HTML")
            self._register_handlers()
            self.is_running = True
            
            def poll_worker():
                print("[BOT] Telegram Bot đã khởi động lắng nghe...")
                while self.is_running:
                    try:
                        self.bot.infinity_polling(timeout=10, long_polling_timeout=5)
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
        self.start_polling()

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start(message):
            chat_id = str(message.chat.id)
            # Tự động lưu Chat ID của người dùng vào cấu hình
            cfg = app_logic.load_config()
            cfg.setdefault("telegram", {})["chat_id"] = chat_id
            app_logic.save_config(cfg)

            keyboard, today = self.build_task_keyboard()
            welcome_msg = (
                f"❄️ <b>WINTER ARC PROTOCOL — ĐÃ KẾT NỐI IPHONE!</b>\n\n"
                f"Chào Chiến Binh! Máy tính và iPhone của bạn đã đồng bộ thành công.\n"
                f"📅 <b>{today['weekday']} ({today['date_str']})</b>\n"
                f"🔥 <b>Winter Arc:</b> Ngày {today['day_num']}/{today['total_days']}\n"
                f"⚡ <b>Chuỗi No Nut:</b> {today['nonut_streak']} ngày\n\n"
                f"<i>Bấm các nút bên dưới để check-in trực tiếp:</i>"
            )
            self.bot.send_message(chat_id, welcome_msg, reply_markup=keyboard)

        @self.bot.message_handler(commands=['status'])
        def handle_status(message):
            keyboard, today = self.build_task_keyboard()
            status_text = (
                f"📊 <b>BÁO CÁO TIẾN ĐỘ HÔM NAY</b>\n"
                f"📅 {today['weekday']} — Ngày {today['day_num']}/{today['total_days']}\n"
                f"🎯 Tiến độ: <b>{today['completed_count']}/{today['total_tasks']} nhiệm vụ ({today['completion_rate']}%)</b>\n"
                f"🇬🇧 Tiếng Anh đã học: <b>{today['english_minutes']}/120 phút</b>\n"
                f"🔥 No Nut Streak: <b>{today['nonut_streak']} ngày</b>\n"
                f"❄️ Full Winter Arc Streak: <b>{today['winter_arc_streak']} ngày</b>"
            )
            self.bot.send_message(message.chat.id, status_text, reply_markup=keyboard)

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            try:
                data = call.data
                if data.startswith("toggle:"):
                    task_id = data.split(":", 1)[1]
                    updated = app_logic.toggle_task(task_id)
                    
                    # Tìm tên task để hiện alert
                    task_name = task_id
                    for t in updated["tasks"]:
                        if t["id"] == task_id:
                            status_str = "Hoàn thành ✅" if t["completed"] else "Đã bỏ chọn ⬜"
                            task_name = f"{t['name']}: {status_str}"
                            break

                    self.bot.answer_callback_query(call.id, text=task_name)
                    
                    # Cập nhật lại giao diện tin nhắn với các nút mới
                    new_keyboard, today = self.build_task_keyboard()
                    new_text = (
                        f"📊 <b>CẬP NHẬT TIẾN ĐỘ HÔM NAY</b>\n"
                        f"📅 {today['weekday']} — Ngày {today['day_num']}/{today['total_days']}\n"
                        f"🎯 Hoàn thành: <b>{today['completed_count']}/{today['total_tasks']} ({today['completion_rate']}%)</b>\n"
                        f"🔥 No Nut: <b>{today['nonut_streak']} ngày</b> | Winter Arc: <b>{today['winter_arc_streak']} ngày</b>\n\n"
                        f"<i>Tick ngay trên tin nhắn này:</i>"
                    )
                    self.bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=new_text,
                        reply_markup=new_keyboard
                    )
                elif data == "refresh":
                    new_keyboard, today = self.build_task_keyboard()
                    self.bot.answer_callback_query(call.id, text="Đã làm mới dữ liệu!")
                    self.bot.edit_message_reply_markup(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=new_keyboard
                    )
            except Exception as e:
                print(f"[Callback Error]: {e}")

    def send_broadcast(self, text, with_buttons=True):
        token, chat_id = self.get_token_and_chat()
        if not token:
            return False, "Chưa nhập Telegram Bot Token"

        # Nếu chưa khởi tạo bot, khởi tạo nhanh
        if not self.bot:
            try:
                self.bot = telebot.TeleBot(token, parse_mode="HTML")
            except Exception as e:
                return False, f"Lỗi khởi tạo Bot: {e}"

        # Nếu chưa có chat_id, tự động dò tìm từ tin nhắn gần nhất người dùng gửi vào Bot
        if not chat_id:
            try:
                updates = self.bot.get_updates(limit=10)
                if updates:
                    # Lấy tin nhắn mới nhất
                    for u in reversed(updates):
                        msg_obj = u.message or u.edited_message or u.channel_post
                        if msg_obj and msg_obj.chat:
                            chat_id = str(msg_obj.chat.id)
                            # Tự động lưu vào config.json
                            cfg = app_logic.load_config()
                            cfg.setdefault("telegram", {})["chat_id"] = chat_id
                            app_logic.save_config(cfg)
                            print(f"[BOT] Đã tự động phát hiện và lưu Chat ID: {chat_id}")
                            break
            except Exception as e:
                print(f"[BOT Auto-Detect Chat ID Error]: {e}")

        if not chat_id:
            return False, "Chưa tìm thấy tin nhắn từ bạn! Hãy mở @winter_arc_h11ng_bot trên Telegram và bấm START trước nhé."

        try:
            if with_buttons:
                keyboard, _ = self.build_task_keyboard()
                self.bot.send_message(chat_id, text, reply_markup=keyboard)
            else:
                self.bot.send_message(chat_id, text)
            return True, "Thành công"
        except Exception as e:
            return False, str(e)


bot_instance = WinterArcBot()
