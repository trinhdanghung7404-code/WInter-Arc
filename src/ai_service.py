import json
import logging
import requests
from . import app_logic

logger = logging.getLogger("WinterArcAI")

SYSTEM_PERSONA = (
    "You are a stoic, disciplined, tough-love Winter Arc personal discipline mentor and brother. "
    "You communicate in crisp, impactful Vietnamese with a confident, motivating, and no-excuses tone. "
    "Rules:\n"
    "1. Praise consistency and 100% flame streaks (🔥) enthusiastically.\n"
    "2. Be brutally honest and call out half-hearted effort or grey streaks (⚪) without sugarcoating.\n"
    "3. Keep responses punchy, concise (around 3 to 5 short paragraphs max), and format with clean HTML tags supported by Telegram (<b>, <i>, <code>).\n"
    "4. End with a sharp warrior mindset takeaway for the upcoming days."
)

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
    models = ["gemini-flash-latest", "gemini-3.5-flash", "gemini-3.7-flash"]
    last_err = None
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_PERSONA}\n\nTask:\n{prompt}"}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800
        }
    }

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            else:
                err_msg = resp.text
                try:
                    err_msg = resp.json().get("error", {}).get("message", resp.text)
                except Exception:
                    pass
                last_err = f"Gemini Error ({resp.status_code}): {err_msg}"
        except Exception as e:
            last_err = str(e)
            
    raise Exception(last_err or "Gemini API unavailable")

def call_openai(api_key, prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PERSONA},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 800
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    else:
        err_msg = resp.text
        try:
            err_msg = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            pass
        raise Exception(f"OpenAI API Error ({resp.status_code}): {err_msg}")

def generate_ai_text(prompt):
    api_key, provider = get_ai_config()
    if not api_key:
        return None
    
    # Auto-detect if key is OpenAI format
    if api_key.startswith("sk-"):
        return call_openai(api_key, prompt)
    else:
        return call_gemini(api_key, prompt)

def generate_weekly_review(data):
    """
    Tạo báo cáo tuần do AI Coach nhận xét.
    Nếu không có AI Key hoặc lỗi mạng, trả về báo cáo tiêu chuẩn mẫu.
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

    # Báo cáo chuẩn fallback nếu chưa có AI Key
    fallback_text = (
        f"📊 <b>WINTER ARC — BÁO CÁO TỔNG KẾT TUẦN</b>\n\n"
        f"🏆 <b>Cấp độ:</b> {level_info.get('badge', 'LEVEL 1')} — {level_info.get('title', 'Recruit')}\n"
        f"⚡ <b>Chuỗi hiện tại:</b> {current_streak} ngày\n"
        f"🎯 <b>Tỷ lệ hoàn thành cả tuần:</b> {total_done}/{total_assigned} ({overall_rate}%)\n\n"
        f"• Ngày 100% (Chuỗi Lửa 🔥): <b>{flame_days} ngày</b>\n"
        f"• Ngày 50-99% (Chuỗi Xám ⚪): <b>{grey_days} ngày</b>\n"
        f"• Ngày bỏ lỡ (<50% 💀): <b>{missed_days} ngày</b>\n"
        f"• Tổng giờ học Tiếng Anh: <b>{english_hours} giờ</b>\n\n"
        f"<i>💡 Gắn Gemini API Key trong Protocol Manager để nhận lời nhận xét chi tiết từ AI Coach!</i>"
    )

    if not is_ai_enabled():
        return fallback_text

    prompt = (
        f"Hãy nhận xét về kết quả kỷ luật 7 ngày vừa qua của chiến binh Winter Arc:\n"
        f"- Cấp độ hiện tại: {level_info.get('badge', 'LEVEL 1')} ({level_info.get('title', 'Recruit')})\n"
        f"- Chuỗi hiện tại: {current_streak} ngày\n"
        f"- Tỷ lệ hoàn thành tổng thể: {total_done}/{total_assigned} ({overall_rate}%)\n"
        f"- Số ngày đạt 100% (Chuỗi Lửa 🔥): {flame_days}/7 ngày\n"
        f"- Số ngày làm nửa vời (Chuỗi Xám ⚪): {grey_days}/7 ngày\n"
        f"- Số ngày lười biếng / bỏ lỡ (<50%): {missed_days}/7 ngày\n"
        f"- Tổng giờ học Tiếng Anh tuần qua: {english_hours} giờ\n\n"
        f"Chi tiết từng ngày:\n" + "\n".join(days_stat) + "\n\n"
        f"Yêu cầu:\n"
        f"1. Mở đầu bằng tiêu đề chuẩn Telegram HTML: 🛡️ <b>[AI COACH] BÁO CÁO KỶ LUẬT TUẦN QUA</b>\n"
        f"2. Đánh giá thẳng thắn phong độ tuần qua (khen ngợi nếu giữ chuỗi lửa, chỉnh đốn nếu có chuỗi xám hoặc ngày bỏ cuộc).\n"
        f"3. Nêu rõ mục tiêu tối quan trọng cho tuần tới.\n"
        f"4. Giữ phong thái lạnh lùng, kỷ luật thép, khích lệ tự tôn bản lĩnh."
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
    Tạo báo cáo tháng / chặng 30 ngày (Level milestone)
    """
    level = data.get("level", 1)
    day_num = data.get("day_num", 30)
    flame_count = data.get("flame_count", 0)
    grey_count = data.get("grey_count", 0)
    english_hours = round(data.get("english_minutes", 0) / 60, 1)
    title = data.get("title", "Recruit")

    fallback_text = (
        f"👑 <b>WINTER ARC — BÁO CÁO KỶ LUẬT CHẶNG 30 NGÀY (LEVEL {level})</b>\n\n"
        f"🏆 <b>Danh hiệu:</b> {title}\n"
        f"📅 Đã đi qua: <b>{day_num}/90 ngày</b>\n"
        f"🔥 Tổng ngày đạt Chuỗi Lửa: <b>{flame_count} ngày</b>\n"
        f"⚪ Ngày Chuỗi Xám: <b>{grey_count} ngày</b>\n"
        f"📖 Tổng giờ Tiếng Anh: <b>{english_hours} giờ</b>\n\n"
        f"<i>Bước sang chặng tiếp theo với tiêu chuẩn kỷ luật cao hơn nữa!</i>"
    )

    if not is_ai_enabled():
        return fallback_text

    prompt = (
        f"Chiến binh vừa hoàn thành chặng 30 ngày của Level {level} ({title}).\n"
        f"- Ngày thứ: {day_num}/90 ngày Winter Arc.\n"
        f"- Tổng số ngày hoàn thành 100% (Chuỗi Lửa 🔥): {flame_count} ngày.\n"
        f"- Số ngày chuỗi xám: {grey_count} ngày.\n"
        f"- Tổng giờ học Tiếng Anh tích lũy: {english_hours} giờ.\n\n"
        f"Yêu cầu:\n"
        f"1. Tiêu đề Telegram HTML: 👑 <b>[AI COACH] TỔNG KẾT CHẶNG 30 NGÀY (LEVEL {level})</b>\n"
        f"2. Đánh giá sự biến chuyển tâm lý và sức chịu đựng của chiến binh sau 30 ngày.\n"
        f"3. Nhắc nhở rằng chặng đường tiếp theo sẽ khắc nghiệt hơn, đòi hỏi tập trung cao độ hơn.\n"
        f"4. Văn phong truyền lửa, chuẩn Stoic warrior."
    )

    try:
        ai_reply = generate_ai_text(prompt)
        if ai_reply:
            return ai_reply
    except Exception as e:
        logger.error(f"Generate monthly review error: {e}")

    return fallback_text


def chat_with_coach(user_message, today_context=None):
    """
    Trả lời tin nhắn tự do của người dùng qua Telegram
    """
    if not is_ai_enabled():
        return (
            "🤖 <i>AI Coach chưa được kích hoạt. Hãy vào Protocol Manager dán Google Gemini API Key để trò chuyện cùng huấn luyện viên!</i>"
        )

    context_str = ""
    if today_context:
        context_str = (
            f"\n[Bối cảnh hiện tại của người dùng hôm nay]:\n"
            f"- Ngày thứ: {today_context.get('day_num')}/{today_context.get('total_days')}\n"
            f"- Tiến độ hôm nay: {today_context.get('completed_count')}/{today_context.get('total_tasks')} ({today_context.get('completion_rate')}%)\n"
            f"- Chuỗi: {today_context.get('winter_arc_streak')} ngày\n"
        )

    prompt = (
        f"Chiến binh Winter Arc vừa nhắn cho bạn tin nhắn này:\n"
        f"\"{user_message}\"\n"
        f"{context_str}\n"
        f"Hãy trả lời người dùng ngắn gọn (2-4 câu), phong thái người anh/huấn luyện viên kỷ luật, "
        f"thực tế, không sáo rỗng, kéo họ về kỷ luật và hành động."
    )

    try:
        return generate_ai_text(prompt)
    except Exception as e:
        return f"⚠️ <i>Lỗi kết nối AI: {e}</i>"


def test_ai_connection():
    """Kiểm tra kết nối tới AI API"""
    api_key, provider = get_ai_config()
    if not api_key:
        return False, "Chưa nhập API Key"
    
    prompt = "Trả lời đúng 1 câu duy nhất truyền cảm hứng kỷ luật cho chiến binh Winter Arc."
    try:
        reply = generate_ai_text(prompt)
        return True, reply
    except Exception as e:
        return False, str(e)
