import json
import os
from datetime import datetime, date, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
STORAGE_PATH = os.path.join(DATA_DIR, "storage.json")
PROTOCOLS_PATH = os.path.join(DATA_DIR, "protocols.json")

WEEKDAY_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    try:
        from . import cloud_sync
        cloud_sync.sync_config_up()
    except Exception:
        pass

def load_storage():
    if not os.path.exists(STORAGE_PATH):
        return {"streaks": {"nonut": 0, "winter_arc": 0}, "history": {}}
    try:
        with open(STORAGE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"streaks": {"nonut": 0, "winter_arc": 0}, "history": {}}

def save_storage(data):
    with open(STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_note(note_text, target_date_str=None):
    today_str = target_date_str or date.today().strftime("%Y-%m-%d")
    storage = load_storage()
    history = storage.setdefault("history", {})
    record = history.setdefault(today_str, {
        "tasks": {},
        "focus_times": {},
        "notes": ""
    })
    existing = (record.get("notes") or "").strip()
    if existing:
        record["notes"] = existing + "\n• " + note_text.strip()
    else:
        record["notes"] = "• " + note_text.strip()
    save_storage(storage)
    return record["notes"]

def get_notes(target_date_str=None):
    today_str = target_date_str or date.today().strftime("%Y-%m-%d")
    storage = load_storage()
    return storage.get("history", {}).get(today_str, {}).get("notes", "")

def load_all_protocols():
    """Đọc toàn bộ danh sách protocols từ file protocols.json (bao gồm cả các protocol cũ / đã xóa để lưu vết lịch sử)"""
    if not os.path.exists(PROTOCOLS_PATH):
        return []
    try:
        with open(PROTOCOLS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("protocols", [])
    except Exception as e:
        print(f"[Protocols Load Error]: {e}")
        return []

def load_protocols(include_inactive=False):
    """Đọc danh sách mục tiêu đang hoạt động (active) cho Manager và hiển thị hiện tại"""
    all_p = load_all_protocols()
    if include_inactive:
        return all_p
    return [p for p in all_p if p.get("active", True) and not p.get("deleted_at")]

def save_protocols(protocols_list):
    """Lưu danh sách mục tiêu vào file protocols.json"""
    with open(PROTOCOLS_PATH, "w", encoding="utf-8") as f:
        json.dump({"protocols": protocols_list}, f, ensure_ascii=False, indent=2)
    try:
        from . import cloud_sync
        cloud_sync.sync_protocols_up()
    except Exception:
        pass

def add_protocol(new_item):
    """Thêm một mục tiêu mới vào file protocols.json"""
    protocols = load_all_protocols()
    # Tự động sinh ID nếu chưa có
    if not new_item.get("id"):
        new_item["id"] = "task_" + str(int(datetime.now().timestamp()))
    new_item.setdefault("active", True)

    # Chặn đặt lịch cho ngày quá khứ. Cho phép hôm nay nếu giờ đặt >= hiện tại + 2 tiếng.
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    min_time = (now + timedelta(hours=2)).strftime("%H:%M")

    if new_item.get("schedule_type") == "dates":
        specific = new_item.get("specific_dates", [])
        if any(d < today_str for d in specific):
            raise ValueError("Cannot schedule for past dates.")
        if today_str in specific:
            remind_t = (new_item.get("remind_time") or "").strip()
            if remind_t and remind_t < min_time:
                raise ValueError(f"When scheduling for today ({today_str}), time must be at least 2 hours in advance (>= {min_time}).")

    protocols.append(new_item)
    save_protocols(protocols)
    return load_protocols()

def delete_protocol(item_id):
    """
    Xóa mục tiêu an toàn (Soft Delete):
    - Đánh dấu active = False, deleted_at = ngày hiện tại
    - Giữ lại lịch sử trong quá khứ (< today) để khi xem lại ngày cũ vẫn nguyên vẹn 100%!
    """
    protocols = load_all_protocols()
    today_str = date.today().strftime("%Y-%m-%d")

    for p in protocols:
        if p.get("id") == item_id:
            p["active"] = False
            p["deleted_at"] = today_str
            # Nếu là lịch theo ngày cụ thể, chỉ giữ lại các ngày trong quá khứ để bảo toàn lịch sử
            if p.get("schedule_type") == "dates" or p.get("specific_dates"):
                past_dates = [d for d in p.get("specific_dates", []) if d < today_str]
                p["specific_dates"] = past_dates
            break

    save_protocols(protocols)
    return load_protocols()

def update_protocol(item_id, updated_fields):
    """Update protocol in protocols.json"""
    protocols = load_all_protocols()
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    min_time = (now + timedelta(hours=2)).strftime("%H:%M")

    if updated_fields.get("schedule_type") == "dates":
        new_specific = updated_fields.get("specific_dates", [])
        if any(d < today_str for d in new_specific):
            raise ValueError("Cannot schedule for past dates.")
        if today_str in new_specific:
            remind_t = (updated_fields.get("remind_time") or "").strip()
            if remind_t and remind_t < min_time:
                raise ValueError(f"When scheduling for today ({today_str}), time must be at least 2 hours in advance (>= {min_time}).")

    for p in protocols:
        if p.get("id") == item_id:
            p.update(updated_fields)
            break
    save_protocols(protocols)
    return load_protocols()

def get_day_number(target_date=None):
    cfg = load_config()
    start_str = cfg.get("start_date", "2026-10-01")
    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
    except Exception:
        start_dt = date(2026, 10, 1)
        
    curr_date = target_date or date.today()
    delta = (curr_date - start_dt).days + 1
    total = cfg.get("total_days", 92)
    return max(1, delta), total

def get_task_definitions_for_date(curr_date):
    """
    Lấy danh sách nhiệm vụ hợp lệ cho một ngày cụ thể dựa trên protocols.json:
    - Nếu curr_date là ngày quá khứ (< today): Bao gồm cả các protocol đã bị xóa SAU ngày đó để bảo toàn lịch sử.
    - Nếu curr_date là hôm nay hoặc tương lai (>= today): Chỉ lấy các protocol đang active (chưa bị xóa).
    - Tự động khôi phục các task_id đã lưu trong history của ngày quá khứ.
    """
    all_raw_protocols = load_all_protocols()
    today_str = date.today().strftime("%Y-%m-%d")
    curr_date_str = curr_date.strftime("%Y-%m-%d")
    is_past_day = (curr_date_str < today_str)
    weekday = curr_date.weekday()

    tasks_for_day = []
    task_map = {}

    for p in all_raw_protocols:
        pid = p.get("id")
        is_active = p.get("active", True)
        deleted_at = p.get("deleted_at")

        if is_past_day:
            # Ngày trong quá khứ: protocol hợp lệ nếu ngày đó xảy ra TRƯỚC thời điểm xóa
            if deleted_at and curr_date_str >= deleted_at:
                continue
            if not is_active and not deleted_at:
                # Nếu bị tắt thủ công mà không có deleted_at thì bỏ qua
                pass
        else:
            # Ngày hôm nay hoặc tương lai: chỉ lấy protocol đang active và chưa xóa
            if not is_active or deleted_at:
                continue

        schedule_type = p.get("schedule_type", "")
        days = p.get("days", [])
        specific_dates = p.get("specific_dates", [])

        # Auto-detect schedule_type if not explicitly set
        if not schedule_type:
            if specific_dates and (not days or len(days) == 0):
                schedule_type = "dates"
            elif specific_dates and days:
                schedule_type = "both"
            else:
                schedule_type = "weekly"

        is_match = False
        if schedule_type == "dates":
            is_match = (curr_date_str in specific_dates)
        elif schedule_type == "both":
            is_match = (weekday in days) or (curr_date_str in specific_dates)
        else: # weekly
            is_match = (weekday in (days or []))

        if is_match and pid not in task_map:
            task_map[pid] = p
            tasks_for_day.append(p)

    # Khôi phục các task đã từng được ghi nhận trong history của ngày quá khứ (nếu có)
    if is_past_day:
        storage = load_storage()
        day_rec = storage.get("history", {}).get(curr_date_str, {})
        recorded_tasks = day_rec.get("tasks", {})
        for rec_tid in recorded_tasks.keys():
            if rec_tid not in task_map:
                # Tìm metadata trong toàn bộ danh sách protocol cũ
                raw_match = next((p for p in all_raw_protocols if p.get("id") == rec_tid), None)
                if raw_match:
                    task_map[rec_tid] = raw_match
                    tasks_for_day.append(raw_match)
                else:
                    # Tạo metadata dự phòng hiển thị đẹp
                    clean_name = rec_tid.replace("task_", "").replace("_", " ").title()
                    fallback_p = {
                        "id": rec_tid,
                        "name": clean_name,
                        "icon": "🎯",
                        "type": "todo",
                        "active": False
                    }
                    task_map[rec_tid] = fallback_p
                    tasks_for_day.append(fallback_p)

    return tasks_for_day

def get_today_data(target_date_str=None):
    if target_date_str:
        try:
            today = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        except Exception:
            today = date.today()
    else:
        today = date.today()
    real_today = date.today()
    is_future = (today > real_today)
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    weekday_idx = today.weekday()
    weekday_name = WEEKDAY_EN[weekday_idx]
    
    storage = load_storage()
    history = storage.setdefault("history", {})
    
    day_record = history.setdefault(today_str, {
        "tasks": {},
        "focus_times": {},
        "notes": ""
    })
    
    yesterday_record = history.setdefault(yesterday_str, {
        "tasks": {},
        "focus_times": {},
        "notes": ""
    })

    task_defs = get_task_definitions_for_date(today)
    tasks_result = []
    timer_tasks_result = []
    completed_count = 0

    for t in task_defs:
        tid = t["id"]
        t_type = t.get("type", "todo")
        
        if is_future:
            is_done = False
            eval_date_label = "Upcoming"
        else:
            # Retro: check yesterday's record
            if t_type == "retro":
                is_done = yesterday_record["tasks"].get(tid, False)
                eval_date_label = f"Yesterday ({yesterday.strftime('%b %d')})"
            else:
                is_done = day_record["tasks"].get(tid, False)
                eval_date_label = "Today"

        if is_done:
            completed_count += 1

        task_item = {
            **t,
            "completed": is_done,
            "eval_label": eval_date_label
        }
        tasks_result.append(task_item)

        # Lọc riêng các nhiệm vụ có timer để gửi cho bộ đếm giờ
        if t_type == "timer":
            studied_mins = 0 if is_future else day_record.get("focus_times", {}).get(tid, 0)
            timer_tasks_result.append({
                "id": tid,
                "name": t.get("name", "Task"),
                "icon": t.get("icon", "⏱️"),
                "target_minutes": t.get("target_minutes", 60),
                "studied_minutes": studied_mins,
                "completed": is_done
            })

    day_num, total_days = get_day_number(today)
    completion_rate = int((completed_count / len(task_defs)) * 100) if task_defs and not is_future else 0

    nonut_streak = calculate_streak("nonut", history)
    streak_info = calculate_winter_arc_streak(history)
    winter_arc_streak = streak_info.get("streak", 0)
    level_info = calculate_level_info(day_num, total_days)

    storage["streaks"]["nonut"] = nonut_streak
    storage["streaks"]["winter_arc"] = winter_arc_streak
    save_storage(storage)

    english_mins = 0 if is_future else day_record.get("focus_times", {}).get("english", 0)
    project_mins = 0 if is_future else day_record.get("focus_times", {}).get("project", 0)

    return {
        "date_str": today_str,
        "yesterday_str": yesterday_str,
        "is_future": is_future,
        "weekday": weekday_name,
        "day_num": day_num,
        "total_days": total_days,
        "level_info": level_info,
        "streak_info": streak_info,
        "tasks": tasks_result,
        "timer_tasks": timer_tasks_result,
        "english_minutes": english_mins,
        "project_minutes": project_mins,
        "completed_count": completed_count,
        "total_tasks": len(task_defs),
        "completion_rate": completion_rate,
        "nonut_streak": nonut_streak,
        "winter_arc_streak": winter_arc_streak,
        "all_protocols": load_protocols()
    }


def toggle_task(task_id, force_date_str=None):
    """
    Tick hoàn thành hoặc bỏ tick một nhiệm vụ.
    Tự động xác định: Nếu là loại retro (xác nhận hôm qua) thì lưu vào ngày hôm qua!
    Khóa không cho phép tick các ngày tương lai!
    """
    today = date.today()
    yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

    # Chặn hoàn thành các sự kiện trong tương lai
    if force_date_str and force_date_str > today_str:
        return get_today_data(force_date_str)

    # Tìm định nghĩa loại nhiệm vụ
    protocols = load_protocols()
    task_type = "todo"
    for p in protocols:
        if p.get("id") == task_id:
            task_type = p.get("type", "todo")
            break

    target_date = force_date_str or (yesterday_str if task_type == "retro" else today_str)

    storage = load_storage()
    history = storage.setdefault("history", {})
    record = history.setdefault(target_date, {
        "tasks": {},
        "focus_times": {},
        "notes": ""
    })

    curr_val = record["tasks"].get(task_id, False)
    record["tasks"][task_id] = not curr_val

    save_storage(storage)

    try:
        from . import cloud_sync
        cloud_sync.sync_toggle(task_id)
    except Exception:
        pass

    return get_today_data(force_date_str)

def add_focus_time(task_id, minutes):
    today_str = date.today().strftime("%Y-%m-%d")
    storage = load_storage()
    record = storage.setdefault("history", {}).setdefault(today_str, {
        "tasks": {},
        "focus_times": {},
        "notes": ""
    })

    focus_dict = record.setdefault("focus_times", {})
    focus_dict[task_id] = focus_dict.get(task_id, 0) + minutes

    # Tìm target_minutes của task này trong protocols.json
    protocols = load_protocols()
    target_mins = 60
    for p in protocols:
        if p.get("id") == task_id:
            target_mins = p.get("target_minutes", 60)
            break

    if focus_dict[task_id] >= target_mins:
        record["tasks"][task_id] = True

    save_storage(storage)
    return get_today_data()

def calculate_streak(task_id, history):
    streak = 0
    curr = date.today()
    
    # Kiểm tra xem hôm nay hoặc hôm qua có làm không
    today_str = curr.strftime("%Y-%m-%d")
    yesterday_str = (curr - timedelta(days=1)).strftime("%Y-%m-%d")
    
    today_done = history.get(today_str, {}).get("tasks", {}).get(task_id, False)
    yesterday_done = history.get(yesterday_str, {}).get("tasks", {}).get(task_id, False)
    
    if today_done:
        streak += 1
        curr -= timedelta(days=1)
    elif yesterday_done:
        streak += 1
        curr = curr - timedelta(days=2)
    else:
        return 0

    while True:
        d_str = curr.strftime("%Y-%m-%d")
        if history.get(d_str, {}).get("tasks", {}).get(task_id, False):
            streak += 1
            curr -= timedelta(days=1)
        else:
            break
            
    return streak

def get_day_performance(d, history):
    """
    Tính tỉ lệ hoàn thành nhiệm vụ của một ngày cụ thể:
    - rate: % hoàn thành (0 - 100)
    - status: 'fire' (100%), 'grey' (50% - 99%), 'lost' (< 50%)
    """
    d_str = d.strftime("%Y-%m-%d")
    rec = history.get(d_str, {}).get("tasks", {})
    defs = get_task_definitions_for_date(d)
    if not defs:
        return 0, 0, 0, "none"
        
    total = len(defs)
    done = sum(1 for t in defs if rec.get(t["id"], False))
    rate = int((done / total) * 100) if total else 0

    if rate == 100:
        status = "fire"
    elif rate >= 50:
        status = "grey"
    else:
        status = "lost"

    return rate, done, total, status

def calculate_winter_arc_streak(history):
    """
    Chính sách tính Streak Winter Arc chuẩn:
    1. Làm hết 100%: Chuỗi Lửa 🔥 (Flame Streak)
    2. Làm nửa (50% - 99%): Chuỗi Xám ⚪ (Grey Streak)
    3. Nếu có > 3 ngày chuỗi xám liên tiếp: MẤT CHUỖI (= 0)
    4. Không làm gì (< 50%): MẤT CHUỖI (= 0)
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    rate_today, _, total_today, status_today = get_day_performance(today, history)
    rate_yesterday, _, total_yesterday, status_yesterday = get_day_performance(yesterday, history)
    
    # Nếu hôm nay đã đạt từ 50% trở lên thì tính cả hôm nay
    if status_today in ("fire", "grey"):
        curr = today
    else:
        # Nếu hôm nay chưa xong (đang trong ngày), kiểm tra hôm qua
        if status_yesterday == "lost":
            return {
                "streak": 0,
                "type": "none",
                "badge": "No streak yet",
                "consecutive_grey": 0,
                "warning": False,
                "warning_msg": ""
            }
        curr = yesterday

    streak = 0
    consecutive_grey = 0
    current_day_status = None
    first_day = True

    while True:
        rate, done, total, status = get_day_performance(curr, history)
        if total == 0:
            break
            
        if first_day:
            current_day_status = status

        if status == "fire":
            streak += 1
            # Gặp ngày 100% thì reset chuỗi xám liên tiếp
            consecutive_grey = 0
        elif status == "grey":
            consecutive_grey += 1
            # QUY TẮC CỐT LÕI: Nếu > 3 ngày xám liên tiếp -> MẤT CHUỖI!
            if consecutive_grey > 3:
                return {
                    "streak": 0,
                    "type": "lost",
                    "badge": "Streak Lost (>3 grey days)",
                    "consecutive_grey": consecutive_grey,
                    "warning": True,
                    "warning_msg": "You have more than 3 consecutive grey days. Streak reset to 0!"
                }
            streak += 1
        else:
            # status == 'lost' (< 50%): Streak resets here
            break

        first_day = False
        curr -= timedelta(days=1)

    # Evaluate streak badge
    streak_type = current_day_status or "fire"
    warning = (streak_type == "grey" and consecutive_grey >= 2)
    warning_msg = f"Warning: You have {consecutive_grey}/3 consecutive grey days. Push harder to protect your streak!" if warning else ""

    if streak_type == "fire":
        badge = f"🔥 {streak} days undefeated"
    elif streak_type == "grey":
        badge = f"⚪ {streak} days (Grey {consecutive_grey}/3)"
    else:
        badge = f"{streak} days"

    return {
        "streak": streak,
        "type": streak_type,
        "badge": badge,
        "consecutive_grey": consecutive_grey,
        "warning": warning,
        "warning_msg": warning_msg
    }

def calculate_full_streak(history):
    """Hàm tương thích ngược trả về số nguyên streak"""
    res = calculate_winter_arc_streak(history)
    return res.get("streak", 0)

def calculate_level_info(day_num, total_days=90):
    """
    Chính sách Cấp độ Level: Mỗi mốc 30 ngày là 1 Level
    - Level 1: Ngày 1 - 30 (Tân Binh - Phá vỡ quán tính)
    - Level 2: Ngày 31 - 60 (Chiến Binh - Kỷ luật thép)
    - Level 3: Ngày 61 - 90 (Bậc Thầy - Bất khả chiến bại)
    """
    level = min(3, max(1, ((day_num - 1) // 30) + 1))
    day_in_level = ((day_num - 1) % 30) + 1
    
    level_metadata = {
        1: {
            "title": "Recruit (Foundation)",
            "badge": "🌱 LEVEL 1",
            "desc": "First 30 days: Breaking old habits and forging baseline discipline",
            "icon": "🌱"
        },
        2: {
            "title": "Warrior (Iron Discipline)",
            "badge": "⚡ LEVEL 2",
            "desc": "Middle 30 days: Solidifying iron habits, speed, and endurance",
            "icon": "⚡"
        },
        3: {
            "title": "Master (Apex Command)",
            "badge": "👑 LEVEL 3",
            "desc": "Final 30 days: Reaching apex state, complete self-mastery",
            "icon": "👑"
        }
    }
    
    meta = level_metadata.get(level, level_metadata[1])
    is_milestone = (day_in_level == 1 and day_num > 1) # Vừa thăng cấp hôm nay

    return {
        "level": level,
        "day_in_level": day_in_level,
        "days_left_in_level": 30 - day_in_level,
        "title": meta["title"],
        "badge": meta["badge"],
        "desc": meta["desc"],
        "icon": meta["icon"],
        "is_milestone": is_milestone
    }


def get_90_day_matrix():
    cfg = load_config()
    start_str = cfg.get("start_date", "2026-10-01")
    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
    except Exception:
        start_dt = date(2026, 10, 1)

    total_days = cfg.get("total_days", 92)
    storage = load_storage()
    history = storage.get("history", {})

    matrix = []
    today = date.today()

    for i in range(total_days):
        day_date = start_dt + timedelta(days=i)
        d_str = day_date.strftime("%Y-%m-%d")
        rec = history.get(d_str, {}).get("tasks", {})
        task_defs = get_task_definitions_for_date(day_date)
        
        done_count = sum(1 for t in task_defs if rec.get(t["id"], False))
        total_count = len(task_defs)
        rate = int((done_count / total_count) * 100) if total_count else 0
        
        is_today = (day_date == today)
        is_future = (day_date > today)
        is_won = (rate == 100)

        matrix.append({
            "day_index": i + 1,
            "date": d_str,
            "rate": rate,
            "done_count": done_count,
            "total_count": total_count,
            "is_today": is_today,
            "is_future": is_future,
            "is_won": is_won
        })

    return matrix


def get_weekly_summary():
    """Tổng hợp dữ liệu 7 ngày gần nhất để gửi cho AI Coach phân tích"""
    storage = load_storage()
    history = storage.get("history", {})
    today = date.today()
    
    days_stat = []
    total_assigned = 0
    total_done = 0
    flame_days = 0
    grey_days = 0
    missed_days = 0
    total_english_mins = 0

    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        weekday_name = WEEKDAY_EN[d.weekday()]
        rec = history.get(d_str, {})
        tasks_done = rec.get("tasks", {})
        focus_times = rec.get("focus_times", {})
        
        task_defs = get_task_definitions_for_date(d)
        cnt_total = len(task_defs)
        cnt_done = sum(1 for t in task_defs if tasks_done.get(t["id"], False))
        rate = int((cnt_done / cnt_total) * 100) if cnt_total else 0
        
        total_assigned += cnt_total
        total_done += cnt_done
        total_english_mins += focus_times.get("english", 0)

        if rate == 100 and cnt_total > 0:
            flame_days += 1
            tag = "🔥 100%"
        elif rate >= 50:
            grey_days += 1
            tag = f"⚪ {rate}%"
        else:
            missed_days += 1
            tag = f"💀 {rate}%"

        days_stat.append(f"• {weekday_name} ({d.strftime('%d/%m')}): {cnt_done}/{cnt_total} ({tag})")

    overall_rate = int((total_done / total_assigned) * 100) if total_assigned else 0
    day_num, total_days = get_day_number(today)
    level_info = calculate_level_info(day_num, total_days)
    streak_info = calculate_winter_arc_streak(history)

    return {
        "days_stat": days_stat,
        "total_assigned": total_assigned,
        "total_done": total_done,
        "overall_rate": overall_rate,
        "flame_days": flame_days,
        "grey_days": grey_days,
        "missed_days": missed_days,
        "english_minutes": total_english_mins,
        "current_streak": streak_info.get("streak", 0),
        "level_info": level_info
    }


def get_monthly_summary():
    """Tổng hợp dữ liệu chặng 30 ngày (hoặc toàn bộ các ngày tính đến nay)"""
    storage = load_storage()
    history = storage.get("history", {})
    today = date.today()
    day_num, total_days = get_day_number(today)
    level_info = calculate_level_info(day_num, total_days)

    flame_count = 0
    grey_count = 0
    missed_count = 0
    total_english_mins = 0

    # Lấy 30 ngày gần nhất
    days_to_check = min(30, day_num)
    for i in range(days_to_check - 1, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        rec = history.get(d_str, {})
        tasks_done = rec.get("tasks", {})
        focus_times = rec.get("focus_times", {})
        
        task_defs = get_task_definitions_for_date(d)
        cnt_total = len(task_defs)
        cnt_done = sum(1 for t in task_defs if tasks_done.get(t["id"], False))
        rate = int((cnt_done / cnt_total) * 100) if cnt_total else 0

        total_english_mins += focus_times.get("english", 0)

        if rate == 100 and cnt_total > 0:
            flame_count += 1
        elif rate >= 50:
            grey_count += 1
        else:
            missed_count += 1

    return {
        "level": level_info.get("level", 1),
        "title": level_info.get("title", "Recruit"),
        "day_num": day_num,
        "flame_count": flame_count,
        "grey_count": grey_count,
        "missed_count": missed_count,
        "english_minutes": total_english_mins
    }

# -----------------------------------------------------------------------------
# Weather & Location Logic (Open-Meteo API)
# -----------------------------------------------------------------------------
_weather_cache = {
    "data": None,
    "timestamp": 0,
    "location_key": None
}

WMO_WEATHER_MAP = {
    0: {"name": "Clear Sky", "icon": "☀️"},
    1: {"name": "Mainly Clear", "icon": "🌤️"},
    2: {"name": "Partly Cloudy", "icon": "⛅"},
    3: {"name": "Overcast", "icon": "☁️"},
    45: {"name": "Fog", "icon": "🌫️"},
    48: {"name": "Depositing Rime Fog", "icon": "🌫️"},
    51: {"name": "Light Drizzle", "icon": "🌦️"},
    53: {"name": "Moderate Drizzle", "icon": "🌦️"},
    55: {"name": "Dense Drizzle", "icon": "🌧️"},
    61: {"name": "Slight Rain", "icon": "🌧️"},
    63: {"name": "Moderate Rain", "icon": "🌧️"},
    65: {"name": "Heavy Rain", "icon": "🌧️"},
    71: {"name": "Slight Snow", "icon": "🌨️"},
    73: {"name": "Moderate Snow", "icon": "🌨️"},
    75: {"name": "Heavy Snow", "icon": "❄️"},
    80: {"name": "Slight Showers", "icon": "🌦️"},
    81: {"name": "Moderate Showers", "icon": "🌧️"},
    82: {"name": "Violent Showers", "icon": "⛈️"},
    95: {"name": "Thunderstorm", "icon": "⛈️"},
    96: {"name": "Thunderstorm & Hail", "icon": "⛈️"},
    99: {"name": "Heavy Thunderstorm", "icon": "⛈️"}
}

def get_weather_data(force_refresh=False):
    """
    Fetches real-time temperature and weather info via Open-Meteo.
    Caches results for 10 minutes to ensure fast response and zero lag.
    """
    import urllib.request
    import time
    
    cfg = load_config()
    weather_cfg = cfg.get("weather", {})
    city = weather_cfg.get("city", "Hanoi").strip() or "Hanoi"
    lat = weather_cfg.get("latitude", 21.0245)
    lon = weather_cfg.get("longitude", 105.8412)

    cache_key = f"{lat}_{lon}"
    now = time.time()

    if not force_refresh and _weather_cache["data"] and _weather_cache["location_key"] == cache_key and (now - _weather_cache["timestamp"]) < 600:
        return _weather_cache["data"]

    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto"
        req = urllib.request.Request(url, headers={"User-Agent": "WinterArc/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            current = data.get("current", {})
            daily = data.get("daily", {})
            
            temp = round(current.get("temperature_2m", 25))
            code = current.get("weather_code", 0)
            meta = WMO_WEATHER_MAP.get(code, {"name": "Clear Sky", "icon": "☀️"})
            
            daily_times = daily.get("time", [])
            daily_codes = daily.get("weather_code", [])
            daily_maxs = daily.get("temperature_2m_max", [])
            daily_mins = daily.get("temperature_2m_min", [])
            daily_rains = daily.get("precipitation_probability_max", [])
            
            temp_max = round(daily_maxs[0]) if daily_maxs else temp
            temp_min = round(daily_mins[0]) if daily_mins else temp
            
            # Tomorrow Forecast
            tomorrow_date = daily_times[1] if len(daily_times) > 1 else (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
            tomorrow_code = daily_codes[1] if len(daily_codes) > 1 else code
            tomorrow_meta = WMO_WEATHER_MAP.get(tomorrow_code, {"name": "Clear Sky", "icon": "☀️"})
            tomorrow_max = round(daily_maxs[1]) if len(daily_maxs) > 1 else temp_max
            tomorrow_min = round(daily_mins[1]) if len(daily_mins) > 1 else temp_min
            tomorrow_rain = round(daily_rains[1]) if len(daily_rains) > 1 else 0
            
            # Multi-day forecast mapping by YYYY-MM-DD
            forecast_map = {}
            for i, d_str in enumerate(daily_times):
                d_code = daily_codes[i] if i < len(daily_codes) else 0
                d_meta = WMO_WEATHER_MAP.get(d_code, {"name": "Clear Sky", "icon": "☀️"})
                d_max = round(daily_maxs[i]) if i < len(daily_maxs) else temp
                d_min = round(daily_mins[i]) if i < len(daily_mins) else temp
                d_rain = round(daily_rains[i]) if i < len(daily_rains) else 0
                forecast_map[d_str] = {
                    "date": d_str,
                    "condition": d_meta["name"],
                    "icon": d_meta["icon"],
                    "temp_max": d_max,
                    "temp_min": d_min,
                    "avg_temp": round((d_max + d_min) / 2),
                    "rain_chance": d_rain,
                    "weather_code": d_code
                }
            
            tomorrow_info = {
                "date": tomorrow_date,
                "temp_max": tomorrow_max,
                "temp_min": tomorrow_min,
                "avg_temp": round((tomorrow_max + tomorrow_min) / 2),
                "condition": tomorrow_meta["name"],
                "icon": tomorrow_meta["icon"],
                "rain_chance": tomorrow_rain,
                "weather_code": tomorrow_code
            }
            
            result = {
                "success": True,
                "city": city,
                "temperature": temp,
                "condition": meta["name"],
                "icon": meta["icon"],
                "humidity": current.get("relative_humidity_2m", 50),
                "wind_speed": current.get("wind_speed_10m", 0),
                "temp_max": temp_max,
                "temp_min": temp_min,
                "weather_code": code,
                "tomorrow": tomorrow_info,
                "forecast_map": forecast_map
            }
            
            _weather_cache["data"] = result
            _weather_cache["timestamp"] = now
            _weather_cache["location_key"] = cache_key
            return result
    except Exception as e:
        print(f"[WEATHER ERROR]: {e}")
        if _weather_cache["data"]:
            return _weather_cache["data"]
        tomorrow_default = {
            "date": (date.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "temp_max": 29,
            "temp_min": 21,
            "avg_temp": 25,
            "condition": "Mainly Clear",
            "icon": "🌤️",
            "rain_chance": 0,
            "weather_code": 1
        }
        return {
            "success": False,
            "city": city,
            "temperature": 26,
            "condition": "Clear Sky",
            "icon": "☀️",
            "humidity": 50,
            "wind_speed": 10,
            "temp_max": 28,
            "temp_min": 22,
            "tomorrow": tomorrow_default,
            "forecast_map": {},
            "error": str(e)
        }

def search_city_locations(query):
    """Geocode city query via Open-Meteo search API"""
    import urllib.request
    import urllib.parse
    
    if not query or not query.strip():
        return []
    
    try:
        encoded = urllib.parse.quote(query.strip())
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=6&language=en&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "WinterArc/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = []
            for item in data.get("results", []):
                results.append({
                    "name": item.get("name"),
                    "country": item.get("country", ""),
                    "admin1": item.get("admin1", ""),
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude")
                })
            return results
    except Exception as e:
        print(f"[GEOCODING ERROR]: {e}")
        return []

def update_weather_location(city_name, lat=None, lon=None):
    """Updates weather location in config.json and forces refresh"""
    cfg = load_config()
    
    if lat is None or lon is None:
        locs = search_city_locations(city_name)
        if locs:
            lat = locs[0]["latitude"]
            lon = locs[0]["longitude"]
            city_name = locs[0]["name"]
        else:
            lat = 21.0245
            lon = 105.8412
            city_name = city_name or "Hanoi"
            
    cfg.setdefault("weather", {})
    cfg["weather"]["city"] = city_name
    cfg["weather"]["latitude"] = lat
    cfg["weather"]["longitude"] = lon
    save_config(cfg)
    
    return get_weather_data(force_refresh=True)


