import json
import logging
import urllib.request
import urllib.error
from . import app_logic

logger = logging.getLogger("WinterArcAI")

PERSONA_PRESETS = {
    "david_goggins": (
        "You are David Goggins — extreme mental toughness, tough love, zero excuses, no sugarcoating. "
        "You speak with raw intensity, demanding 100% effort every single day. Call out laziness directly. "
        "Format using clean Telegram HTML (<b>, <i>). Keep it punchy, aggressive, and deeply motivating."
    ),
    "stoic": (
        "You are a wise Stoic philosopher mentor (Marcus Aurelius / Epictetus style). "
        "You communicate in calm, deeply reflective, highly disciplined, and impactful English. "
        "Remind the warrior of control over mind, virtue, and daily duty. Format in clean Telegram HTML."
    ),
    "drill_sergeant": (
        "You are a military Drill Sergeant. Uncompromising discipline, strict orders, high urgency. "
        "Demand prompt execution of all protocols. Call out slacking immediately."
    ),
    "brother": (
        "You are a supportive, caring, but strict older brother. You want the best for them and hold them accountable with firmness. "
        "Format in clean Telegram HTML."
    ),
    "custom": ""
}

def get_active_persona():
    cfg = app_logic.load_config()
    ai_cfg = cfg.get("ai", {})
    custom = (ai_cfg.get("custom_prompt") or "").strip()
    persona_key = ai_cfg.get("persona", "david_goggins").lower()
    
    if custom:
        return custom
    return PERSONA_PRESETS.get(persona_key, PERSONA_PRESETS["david_goggins"])

def get_ai_config():
    cfg = app_logic.load_config()
    ai_cfg = cfg.get("ai", {})
    api_key = ai_cfg.get("api_key", "").strip()
    provider = ai_cfg.get("provider", "gemini").lower()
    return api_key, provider

def is_ai_enabled():
    api_key, _ = get_ai_config()
    return bool(api_key)

def call_gemini(api_key, prompt):
    models = ["gemini-3-flash-preview", "gemini-3.1-flash-lite-preview", "gemini-flash-latest", "gemini-3.1-pro-preview"]
    last_err = None
    headers = {"Content-Type": "application/json", "User-Agent": "WinterArc/1.0"}
    persona = get_active_persona()
    payload = json.dumps({
        "contents": [
            {
                "parts": [
                    {"text": f"{persona}\n\nTask:\n{prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }).encode("utf-8")

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_body = json.loads(err_body).get("error", {}).get("message", err_body)
            except Exception:
                pass
            last_err = f"Gemini ({e.code}): {err_body}"
            if e.code in (503, 429, 404):
                continue
        except Exception as e:
            last_err = str(e)
            
    raise Exception(last_err or "Gemini API temporarily busy, please try again in a few seconds.")

def call_gemini_vision(api_key, image_bytes, prompt, mime_type="image/jpeg"):
    import base64
    import io
    
    # Tối ưu hoá ảnh bằng Pillow (resize max 1280px, nén JPEG) để gửi siêu nhanh và tránh lỗi payload/400
    final_bytes = image_bytes
    final_mime = mime_type or "image/jpeg"
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(image_bytes))
        if im.mode in ("RGBA", "P", "LA"):
            im = im.convert("RGB")
        im.thumbnail((1280, 1280))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=82)
        final_bytes = buf.getvalue()
        final_mime = "image/jpeg"
    except Exception as img_err:
        print(f"[Vision Image Preprocess Warning]: {img_err}")

    b64_data = base64.b64encode(final_bytes).decode("utf-8")
    persona = get_active_persona()
    
    # Format inlineData chuẩn Google Gemini REST API (camelCase)
    payload = json.dumps({
        "contents": [
            {
                "parts": [
                    {"text": f"{persona}\n\nTask:\n{prompt}"},
                    {
                        "inlineData": {
                            "mimeType": final_mime,
                            "data": b64_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1000
        }
    }).encode("utf-8")

    models = ["gemini-3.1-flash-lite-preview", "gemini-3-flash-preview", "gemini-flash-latest"]
    last_err = None
    headers = {"Content-Type": "application/json", "User-Agent": "WinterArc/1.0"}

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                err_body = json.loads(err_body).get("error", {}).get("message", err_body)
            except Exception:
                pass
            last_err = f"Gemini ({e.code}): {err_body}"
            # Tiếp tục thử model dự phòng nếu gặp bất kỳ lỗi API nào
            continue
        except Exception as e:
            last_err = str(e)
            continue
            
    raise Exception(last_err or "Gemini Vision API error.")

def analyze_screentime_image(image_bytes, mime_type="image/jpeg"):
    """
    Phân tích ảnh chụp màn hình Screen Time trên iPhone bằng Gemini Vision:
    - Trích xuất tổng thời gian sử dụng hôm nay.
    - Trích xuất danh sách các app dùng nhiều nhất.
    - AI Coach đánh giá kỷ luật theo Persona đã chọn.
    """
    api_key, _ = get_ai_config()
    if not api_key:
        return {
            "success": False,
            "error": "Chưa cấu hình Gemini API Key"
        }

    prompt = (
        "Bạn là Huấn luyện viên Kỷ luật Winter Arc. Hãy quan sát và phân tích thật kỹ bức ảnh chụp màn hình này:\n\n"
        "1. Nếu đây là ảnh Screen Time (Thời gian sử dụng màn hình của iPhone):\n"
        "   - Đọc ra TỔNG THỜI GIAN sử dụng hôm nay (ví dụ: 3h 45m, 4 giờ 12 phút...).\n"
        "   - Liệt kê các ỨNG DỤNG tiêu tốn nhiều thời gian nhất (TikTok, Facebook, Game, YouTube, Safari...).\n"
        "   - Đánh giá mức độ kỷ luật (< 3h: Tốt/Khen ngợi; > 4h: Cảnh báo nghiêm khắc/Chỉ trích thói quen lướt mạng xã hội).\n"
        "   - Đưa ra mệnh lệnh/lời khuyên hành động cho chiến binh.\n\n"
        "2. Nếu đây KHÔNG PHẢI ảnh Screen Time:\n"
        "   - Nhận xét ngắn gọn nội dung bức ảnh đang gửi là gì.\n"
        "   - Nhắc chiến binh mở Cài đặt (Settings) -> Thời gian sử dụng (Screen Time) để chụp lại đúng trang.\n\n"
        "3. Hãy viết toàn bộ phản hồi bằng định dạng Telegram HTML chuẩn (dùng các thẻ <b>, <i>, <code>) thật đẹp mắt, mạnh mẽ, truyền lửa theo đúng phong cách persona của bạn."
    )

    try:
        raw_text = call_gemini_vision(api_key, image_bytes, prompt, mime_type=mime_type)
        return {
            "success": True,
            "critique": raw_text.strip()
        }
    except Exception as e:
        print(f"[AI ScreenTime Vision Error]: {e}")
        return {
            "success": False,
            "error": str(e),
            "critique": f"❌ Không thể phân tích ảnh: {e}"
        }

def call_openai(api_key, prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "WinterArc/1.0"
    }
    persona = get_active_persona()
    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": persona},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 800
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        try:
            err_body = json.loads(err_body).get("error", {}).get("message", err_body)
        except Exception:
            pass
        raise Exception(f"OpenAI Error ({e.code}): {err_body}")

def generate_ai_text(prompt):
    api_key, provider = get_ai_config()
    if not api_key:
        return None
    
    if api_key.startswith("sk-"):
        return call_openai(api_key, prompt)
    else:
        return call_gemini(api_key, prompt)

def generate_daily_morning_briefing(today_data):
    """Tạo thông điệp đánh thức buổi sáng tự động dựa trên persona đã cấu hình"""
    if not is_ai_enabled():
        return None
    
    day_num = today_data.get("day_num", 1)
    total_days = today_data.get("total_days", 90)
    tasks = today_data.get("tasks", [])
    task_names = [t.get("name") for t in tasks if t.get("name")]
    streak = today_data.get("winter_arc_streak", 0)
    
    prompt = (
        f"Generate a personalized MORNING BRIEFING for a Winter Arc warrior:\n"
        f"- Day: {day_num}/{total_days} ({today_data.get('weekday', 'Today')})\n"
        f"- Current Flame Streak: {streak} days\n"
        f"- Today's Scheduled Protocols ({len(task_names)} items): {', '.join(task_names) if task_names else 'Daily discipline'}\n\n"
        f"Requirements:\n"
        f"1. Start with title in Telegram HTML: 🌅 <b>[MORNING BRIEFING] DAY {day_num}/{total_days}</b>\n"
        f"2. Deliver a 2-3 paragraph ignition message in your chosen persona.\n"
        f"3. Command them to execute today's protocols with zero excuses."
    )
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        logger.error(f"Generate morning briefing error: {e}")
        return None

def generate_daily_night_review(today_data):
    """Tạo báo cáo tổng kết buổi tối tự động dựa trên persona và tiến độ thực tế"""
    if not is_ai_enabled():
        return None
    
    day_num = today_data.get("day_num", 1)
    total_days = today_data.get("total_days", 90)
    completed = today_data.get("completed_count", 0)
    total_tasks = today_data.get("total_tasks", 0)
    rate = today_data.get("completion_rate", 0)
    streak = today_data.get("winter_arc_streak", 0)
    nonut_streak = today_data.get("nonut_streak", 0)
    
    prompt = (
        f"Generate an end-of-day NIGHT DISCIPLINE REVIEW for this warrior based on today's actual performance:\n"
        f"- Day: {day_num}/{total_days} ({today_data.get('weekday', 'Today')})\n"
        f"- Completed Protocols: {completed}/{total_tasks} ({rate}%)\n"
        f"- Streak: {streak} days\n"
        f"- No Nut Streak: {nonut_streak} days\n\n"
        f"Requirements:\n"
        f"1. Start with Telegram HTML title: 🌙 <b>[NIGHT REVIEW] DAY {day_num}/{total_days} ({rate}%)</b>\n"
        f"2. If rate == 100%, praise their absolute discipline enthusiastically.\n"
        f"3. If rate < 100%, call out the slack and command them to make up for it tomorrow.\n"
        f"4. Keep it punchy (2-3 short paragraphs) in your authentic persona."
    )
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        logger.error(f"Generate night review error: {e}")
        return None

def generate_weekly_review(data):
    """
    Weekly review generated by AI Coach.
    Returns standard fallback report if AI key is missing or network fails.
    """
    days_stat = data.get("days_stat", [])
    total_assigned = data.get("total_assigned", 0)
    total_done = data.get("total_done", 0)
    overall_rate = data.get("overall_rate", 0)
    flame_days = data.get("flame_days", 0)
    grey_days = data.get("grey_days", 0)
    missed_days = data.get("missed_days", 0)
    english_hours = round(data.get("english_minutes", 0) / 60, 1)
    current_streak = data.get("current_streak", 0)
    level_info = data.get("level_info", {})

    fallback_text = (
        f"📊 <b>WINTER ARC — WEEKLY DISCIPLINE REPORT</b>\n\n"
        f"🏆 <b>Level:</b> {level_info.get('badge', 'LEVEL 1')} — {level_info.get('title', 'Recruit')}\n"
        f"⚡ <b>Current Streak:</b> {current_streak} days\n"
        f"🎯 <b>Weekly Completion Rate:</b> {total_done}/{total_assigned} ({overall_rate}%)\n\n"
        f"• 100% Days (Flame Streak 🔥): <b>{flame_days} days</b>\n"
        f"• 50–99% Days (Grey Streak ⚪): <b>{grey_days} days</b>\n"
        f"• Missed Days (<50% 💀): <b>{missed_days} days</b>\n"
        f"• Total English Focus Time: <b>{english_hours} hours</b>\n\n"
        f"<i>💡 Connect your Gemini API Key in Protocol Manager for personalized daily AI Coaching!</i>"
    )

    if not is_ai_enabled():
        return fallback_text

    prompt = (
        f"Review the past 7 days of discipline performance for this Winter Arc warrior:\n"
        f"- Current Level: {level_info.get('badge', 'LEVEL 1')} ({level_info.get('title', 'Recruit')})\n"
        f"- Current Streak: {current_streak} days\n"
        f"- Overall Completion Rate: {total_done}/{total_assigned} ({overall_rate}%)\n"
        f"- 100% Days (Flame Streak 🔥): {flame_days}/7 days\n"
        f"- Mediocre Days (Grey Streak ⚪): {grey_days}/7 days\n"
        f"- Missed / Slack Days (<50%): {missed_days}/7 days\n"
        f"- Total English Study: {english_hours} hours\n\n"
        f"Daily Breakdown:\n" + "\n".join(days_stat) + "\n\n"
        f"Requirements:\n"
        f"1. Start with title in Telegram HTML: 🛡️ <b>[AI COACH] WEEKLY DISCIPLINE REVIEW</b>\n"
        f"2. Candidly assess the week's performance (praise unbroken flame streaks, firmly challenge any grey or missed days).\n"
        f"3. State the top critical priority for the upcoming week.\n"
        f"4. Deliver in an unapologetic, stoic warrior brother tone."
    )

    try:
        ai_reply = generate_ai_text(prompt)
        if ai_reply:
            return ai_reply
    except Exception as e:
        logger.error(f"Generate weekly review error: {e}")
        print(f"[AI SERVICE ERROR]: {e}")

    return fallback_text


def generate_monthly_review(data):
    """
    30-Day milestone report (Level progression)
    """
    level = data.get("level", 1)
    day_num = data.get("day_num", 30)
    flame_count = data.get("flame_count", 0)
    grey_count = data.get("grey_count", 0)
    english_hours = round(data.get("english_minutes", 0) / 60, 1)
    title = data.get("title", "Recruit")

    fallback_text = (
        f"👑 <b>WINTER ARC — 30-DAY PHASE REPORT (LEVEL {level})</b>\n\n"
        f"🏆 <b>Title:</b> {title}\n"
        f"📅 Days Elapsed: <b>{day_num}/90 days</b>\n"
        f"🔥 Flame Days (100%): <b>{flame_count} days</b>\n"
        f"⚪ Grey Days: <b>{grey_count} days</b>\n"
        f"📖 English Focus: <b>{english_hours} hours</b>\n\n"
        f"<i>Step into the next phase with even higher standards!</i>"
    )

    if not is_ai_enabled():
        return fallback_text

    prompt = (
        f"Warrior has completed the 30-day milestone for Level {level} ({title}).\n"
        f"- Current Day: {day_num}/90 days of Winter Arc.\n"
        f"- Total 100% Days (Flame Streak 🔥): {flame_count} days.\n"
        f"- Total Grey Days: {grey_count} days.\n"
        f"- Total Accumulated English Focus: {english_hours} hours.\n\n"
        f"Requirements:\n"
        f"1. Telegram HTML header: 👑 <b>[AI COACH] 30-DAY PHASE REVIEW (LEVEL {level})</b>\n"
        f"2. Assess mental endurance growth and identity transformation over these 30 days.\n"
        f"3. Emphasize that the next phase demands even stricter execution.\n"
        f"4. Deliver in an authentic, high-impact stoic warrior tone."
    )

    try:
        ai_reply = generate_ai_text(prompt)
        if ai_reply:
            return ai_reply
    except Exception as e:
        logger.error(f"Generate monthly review error: {e}")

    return fallback_text


def get_full_warrior_context():
    """Thu thập toàn bộ dữ liệu thời gian thực: nhiệm vụ hôm nay, tiến độ, thời tiết hiện tại & dự báo ngày mai"""
    today = app_logic.get_today_data()
    weather = app_logic.get_weather_data()
    
    tasks_list = today.get("tasks", [])
    tasks_summary = []
    for t in tasks_list:
        status = "Done ✅" if t.get("completed") else "Pending ⬜"
        time_info = f" ({t.get('time_desc')})" if t.get("time_desc") else ""
        tasks_summary.append(f"• {t.get('name')}{time_info}: {status}")
    tasks_str = "\n".join(tasks_summary) if tasks_summary else "No specific protocols scheduled."
    
    city = weather.get("city", "Hanoi")
    today_weather = (
        f"{city}: {weather.get('temperature', 28)}°C, {weather.get('condition', 'Clear Sky')}, "
        f"High: {weather.get('temp_max', 28)}°C, Low: {weather.get('temp_min', 22)}°C, "
        f"Humidity: {weather.get('humidity', 50)}%, Wind: {weather.get('wind_speed', 10)} km/h"
    )
    
    tm = weather.get("tomorrow", {})
    tomorrow_weather = (
        f"{tm.get('date', 'Tomorrow')}: {tm.get('condition', 'Clear')}, "
        f"High: {tm.get('temp_max', 29)}°C, Low: {tm.get('temp_min', 20)}°C, "
        f"Rain Chance: {tm.get('rain_chance', 0)}%"
    )
    
    lvl = today.get("level_info", {})
    
    context = (
        f"[CURRENT WARRIOR CONTEXT & REAL-TIME DATA]:\n"
        f"- Date: {today.get('date_str')} ({today.get('weekday')})\n"
        f"- Winter Arc Progress: Day {today.get('day_num')}/{today.get('total_days')} | Level: {lvl.get('badge', 'LV.1')} ({lvl.get('title', 'Recruit')})\n"
        f"- Overall Completion Today: {today.get('completed_count')}/{today.get('total_tasks')} ({today.get('completion_rate')}%)\n"
        f"- Flame Streak: {today.get('winter_arc_streak', 0)} days | No Nut Streak: {today.get('nonut_streak', 0)} days\n"
        f"- Today's Scheduled Protocols:\n{tasks_str}\n"
        f"- Live Weather Today: {today_weather}\n"
        f"- Tomorrow's Weather Forecast: {tomorrow_weather}\n"
    )
    return context

def generate_daily_morning_briefing(today_data):
    """Tạo thông điệp đánh thức buổi sáng tự động dựa trên persona và dữ liệu thời gian thực"""
    if not is_ai_enabled():
        return None
    
    day_num = today_data.get("day_num", 1)
    total_days = today_data.get("total_days", 90)
    context = get_full_warrior_context()
    
    prompt = (
        f"{context}\n\n"
        f"Task:\n"
        f"Generate a personalized MORNING BRIEFING for this Winter Arc warrior.\n"
        f"Requirements:\n"
        f"1. Start with title in Telegram HTML: 🌅 <b>[MORNING BRIEFING] DAY {day_num}/{total_days}</b>\n"
        f"2. Reference today's weather condition and scheduled protocols.\n"
        f"3. Deliver a 2-3 paragraph ignition message in your chosen persona.\n"
        f"4. Command them to execute today's protocols with zero excuses."
    )
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        logger.error(f"Generate morning briefing error: {e}")
        return None

def generate_daily_night_review(today_data):
    """Tạo báo cáo tổng kết buổi tối tự động dựa trên persona và tiến độ thực tế"""
    if not is_ai_enabled():
        return None
    
    day_num = today_data.get("day_num", 1)
    total_days = today_data.get("total_days", 90)
    rate = today_data.get("completion_rate", 0)
    context = get_full_warrior_context()
    
    prompt = (
        f"{context}\n\n"
        f"Task:\n"
        f"Generate an end-of-day NIGHT DISCIPLINE REVIEW for this warrior based on today's actual performance.\n"
        f"Requirements:\n"
        f"1. Start with Telegram HTML title: 🌙 <b>[NIGHT REVIEW] DAY {day_num}/{total_days} ({rate}%)</b>\n"
        f"2. If rate == 100%, praise their absolute discipline enthusiastically.\n"
        f"3. If rate < 100%, call out the slack and command them to make up for it tomorrow (mention tomorrow's weather).\n"
        f"4. Keep it punchy (2-3 short paragraphs) in your authentic persona."
    )
    try:
        return generate_ai_text(prompt)
    except Exception as e:
        logger.error(f"Generate night review error: {e}")
        return None

def chat_with_coach(user_message, today_context=None):
    """
    Respond to free-form warrior messages via Telegram with full live weather & tasks context
    """
    if not is_ai_enabled():
        return (
            "🤖 <i>AI Coach is not active yet. Enter your Google Gemini API Key in Protocol Manager to chat with your coach!</i>"
        )

    context = get_full_warrior_context()

    prompt = (
        f"{context}\n\n"
        f"A Winter Arc warrior just sent you this message:\n"
        f"\"{user_message}\"\n\n"
        f"Instruction for AI:\n"
        f"Answer their message directly in your assigned persona. "
        f"If they ask about today's weather, tomorrow's forecast, scheduled tasks, workouts, streaks, or discipline, give accurate real-time answers based on the context above. "
        f"Format with clean Telegram HTML (<b>, <i>). Keep it punchy, realistic, zero fluff, pulling them back to immediate discipline and action."
    )

    try:
        return generate_ai_text(prompt)
    except Exception as e:
        return f"⚠️ <i>AI connection error: {e}</i>"

def test_ai_connection(custom_prompt=None):
    """Test AI API connection using real warrior context and the user's custom instruction or query"""
    api_key, provider = get_ai_config()
    if not api_key:
        return False, "API Key is not configured"
    
    context = get_full_warrior_context()
    
    user_query = (custom_prompt or "").strip()
    if not user_query:
        user_query = "Brief me on today's discipline status, scheduled tasks, and the weather now & tomorrow."
    
    prompt = (
        f"{context}\n\n"
        f"User / Warrior Request:\n"
        f"\"{user_query}\"\n\n"
        f"Instruction for AI:\n"
        f"Respond directly to the user's request above in your assigned persona. "
        f"Incorporate the real context (weather today/tomorrow, tasks today, streak) accurately. "
        f"Format with clean Telegram HTML (<b>, <i>). Keep it impactful, clear, and concise."
    )
    
    try:
        reply = generate_ai_text(prompt)
        return True, reply
    except Exception as e:
        return False, str(e)
