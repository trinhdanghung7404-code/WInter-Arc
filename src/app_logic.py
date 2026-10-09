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
        recalculate_and_save_streaks()
    except Exception:
        pass
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
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    min_time = (now + timedelta(hours=2)).strftime("%H:%M")
    remind_t = (new_item.get("remind_time") or "").strip()

    if new_item.get("schedule_type") == "weekly":
        # Nếu đặt lịch weekly với giờ hẹn < min_time hôm nay -> bắt đầu có hiệu lực từ ngày mai
        if remind_t and remind_t < min_time:
            new_item.setdefault("effective_from", tomorrow_str)
        else:
            new_item.setdefault("effective_from", today_str)

    if new_item.get("schedule_type") == "dates":
        specific = new_item.get("specific_dates", [])
        if any(d < today_str for d in specific):
            raise ValueError("Cannot schedule for past dates.")
        if today_str in specific:
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
        effective_from = p.get("effective_from")
        created_at = p.get("created_at")

        # BẢO VỆ LỊCH SỬ QUÁ KHỨ: Nếu protocol bắt đầu từ ngày effective_from (hoặc created_at),
        # tuyệt đối KHÔNG bao giờ cho xuất hiện ở bất kỳ ngày nào trước ngày đó!
        if effective_from and curr_date_str < effective_from:
            continue
        if created_at and curr_date_str < created_at:
            continue

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

def is_task_done_in_record(tasks_dict, task_id):
    if not tasks_dict:
        return False
    if tasks_dict.get(task_id, False):
        return True
    if task_id in ("nonut", "no_nut"):
        for k, v in tasks_dict.items():
            if v and ("nonut" in k.lower() or "no_nut" in k.lower() or "no nut" in k.lower()):
                return True
    return False

def calculate_streak(task_id, history):
    streak = 0
    curr = date.today()
    
    # Kiểm tra xem hôm nay hoặc hôm qua có làm không
    today_str = curr.strftime("%Y-%m-%d")
    yesterday_str = (curr - timedelta(days=1)).strftime("%Y-%m-%d")
    
    today_done = is_task_done_in_record(history.get(today_str, {}).get("tasks", {}), task_id)
    yesterday_done = is_task_done_in_record(history.get(yesterday_str, {}).get("tasks", {}), task_id)
    
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
        if is_task_done_in_record(history.get(d_str, {}).get("tasks", {}), task_id):
            streak += 1
            curr -= timedelta(days=1)
        else:
            break
            
    return streak

def recalculate_and_save_streaks():
    """Tự động tính toán lại và lưu chuỗi Streak (Winter Arc & No Nut) vào storage.json"""
    try:
        storage = load_storage()
        history = storage.setdefault("history", {})
        nonut_streak = calculate_streak("nonut", history)
        streak_info = calculate_winter_arc_streak(history)
        winter_arc_streak = streak_info.get("streak", 0)
        storage.setdefault("streaks", {})["nonut"] = nonut_streak
        storage["streaks"]["winter_arc"] = winter_arc_streak
        save_storage(storage)
        return storage["streaks"]
    except Exception as e:
        print(f"[Recalculate Streaks Error]: {e}")
        return {}

def get_day_performance(d, history):
    """
    Tính tỉ lệ hoàn thành nhiệm vụ của một ngày cụ thể:
    - rate: % hoàn thành (0 - 100)
    - status: 'fire' (100%), 'grey' (50% - 99%), 'lost' (< 50%)
    - Hỗ trợ chính xác các task dạng retro (đánh giá ngày hôm qua) và task aliases.
    """
    d_str = d.strftime("%Y-%m-%d")
    yesterday_str = (d - timedelta(days=1)).strftime("%Y-%m-%d")
    rec = history.get(d_str, {}).get("tasks", {})
    yesterday_rec = history.get(yesterday_str, {}).get("tasks", {})
    defs = get_task_definitions_for_date(d)
    if not defs:
        return 0, 0, 0, "none"
        
    total = len(defs)
    done = 0
    for t in defs:
        tid = t.get("id")
        t_type = t.get("type", "todo")
        if t_type == "retro":
            is_done = is_task_done_in_record(yesterday_rec, tid) or is_task_done_in_record(rec, tid)
        else:
            is_done = is_task_done_in_record(rec, tid)
        if is_done:
            done += 1

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
    1. Quá khứ: Các ngày đã kết thúc (từ hôm qua trở về trước) đạt 100% -> Chuỗi Lửa 🔥
    2. Các ngày quá khứ đạt 50% - 99% -> Chuỗi Xám ⚪ (tối đa 3 ngày liên tiếp)
    3. Ngày hôm nay (đang diễn ra):
       - Chuỗi đã đạt được từ quá khứ luôn được BẢO VỆ NGUYÊN VẸN!
       - Nếu hôm nay hoàn thành 100% -> Tăng thêm +1 ngày Lửa 🔥!
       - Không làm tụt chuỗi của các ngày trước thành chuỗi xám khi ngày hôm nay chưa kết thúc.
    """
    today = date.today()
    rate_today, done_today, total_today, status_today = get_day_performance(today, history)
    
    # 1. Tính chuỗi của các ngày trong quá khứ đã khép lại (hôm qua trở về trước)
    curr = today - timedelta(days=1)
    past_streak = 0
    consecutive_grey = 0
    has_grey_in_past = False
    
    while True:
        rate, done, total, status = get_day_performance(curr, history)
        if total == 0:
            break
        if status == 'fire':
            past_streak += 1
            consecutive_grey = 0
        elif status == 'grey':
            has_grey_in_past = True
            consecutive_grey += 1
            if consecutive_grey > 3:
                past_streak = 0
                break
            past_streak += 1
        else: # lost (< 50%)
            break
        curr -= timedelta(days=1)

    # 2. Kết hợp với trạng thái hôm nay
    if status_today == 'fire':
        total_streak = past_streak + 1
        streak_type = 'grey' if has_grey_in_past else 'fire'
        badge = f"🔥 {total_streak} days undefeated" if streak_type == 'fire' else f"⚪ {total_streak} days (Grey {consecutive_grey}/3)"
    elif past_streak > 0:
        total_streak = past_streak
        streak_type = 'grey' if has_grey_in_past else 'fire'
        badge = f"🔥 {total_streak} days undefeated" if streak_type == 'fire' else f"⚪ {total_streak} days (Grey {consecutive_grey}/3)"
    else:
        if status_today == 'grey':
            total_streak = 1
            streak_type = 'grey'
            badge = "⚪ 1 day in progress"
        else:
            total_streak = 0
            streak_type = "none"
            badge = "No streak yet"

    warning = (streak_type == "grey" and consecutive_grey >= 2)
    warning_msg = f"Warning: You have {consecutive_grey}/3 consecutive grey days. Push harder to protect your streak!" if warning else ""

    return {
        "streak": total_streak,
        "type": streak_type,
        "badge": badge,
        "consecutive_grey": consecutive_grey,
        "warning": warning,
        "warning_msg": warning_msg,
        "today_status": status_today,
        "today_progress": f"{done_today}/{total_today} ({rate_today}%)"
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

def resolve_weather_meta(weather_code, is_day=1, hour=None):
    """
    Xác định icon và mô tả thời tiết tự động và sống động theo:
    - Buổi trong ngày: Sáng sớm (Bình minh), Buổi sáng, Buổi chiều, Chiều tà (Hoàng hôn), Ban đêm
    - Hiện tượng thời tiết: Nắng, Ít mây, Nhiều mây, U ám, Sương mù, Mưa phùn, Mưa rào, Mưa dông sét, Tuyết...
    """
    if hour is None:
        hour = datetime.now().hour

    is_night = (is_day == 0) or (hour >= 19 or hour < 5)
    is_early_morning = (not is_night) and (5 <= hour < 7)
    is_morning = (not is_night) and (7 <= hour < 12)
    is_afternoon = (not is_night) and (12 <= hour < 17)
    is_sunset = (not is_night) and (17 <= hour < 19)

    # 0: Clear sky
    if weather_code == 0:
        if is_night:
            return {"name": "Đêm quang", "icon": "🌙", "period": "night"}
        elif is_early_morning:
            return {"name": "Bình minh", "icon": "🌅", "period": "sunrise"}
        elif is_sunset:
            return {"name": "Hoàng hôn", "icon": "🌇", "period": "sunset"}
        elif is_afternoon:
            return {"name": "Nắng chiều", "icon": "☀️", "period": "afternoon"}
        else:
            return {"name": "Nắng sáng", "icon": "☀️", "period": "morning"}

    # 1: Mainly clear
    elif weather_code == 1:
        if is_night:
            return {"name": "Đêm ít mây", "icon": "🌙", "period": "night"}
        elif is_early_morning:
            return {"name": "Sáng ít mây", "icon": "🌤️", "period": "sunrise"}
        elif is_sunset:
            return {"name": "Hoàng hôn", "icon": "🌇", "period": "sunset"}
        elif is_afternoon:
            return {"name": "Chiều ít mây", "icon": "🌤️", "period": "afternoon"}
        else:
            return {"name": "Sáng ít mây", "icon": "🌤️", "period": "morning"}

    # 2: Partly cloudy
    elif weather_code == 2:
        if is_night:
            return {"name": "Đêm có mây", "icon": "☁️", "period": "night"}
        elif is_afternoon:
            return {"name": "Chiều có mây", "icon": "⛅", "period": "afternoon"}
        elif is_sunset:
            return {"name": "Chiều tà mây", "icon": "🌥️", "period": "sunset"}
        else:
            return {"name": "Sáng có mây", "icon": "⛅", "period": "morning"}

    # 3: Overcast
    elif weather_code == 3:
        if is_night:
            return {"name": "Đêm âm u", "icon": "☁️", "period": "night"}
        else:
            return {"name": "Nhiều mây", "icon": "☁️", "period": "day"}

    # 45, 48: Fog
    elif weather_code in (45, 48):
        if is_night:
            return {"name": "Sương mù đêm", "icon": "🌫️", "period": "night"}
        elif is_early_morning or is_morning:
            return {"name": "Sương mù sớm", "icon": "🌫️", "period": "morning"}
        else:
            return {"name": "Có sương mù", "icon": "🌫️", "period": "day"}

    # 51, 53, 55: Drizzle
    elif weather_code in (51, 53, 55):
        if is_night:
            return {"name": "Mưa phùn đêm", "icon": "🌧️", "period": "night"}
        else:
            return {"name": "Mưa phùn", "icon": "🌦️", "period": "day"}

    # 61: Slight rain
    elif weather_code == 61:
        if is_night:
            return {"name": "Mưa rào nhẹ đêm", "icon": "🌧️", "period": "night"}
        elif is_afternoon:
            return {"name": "Mưa rào chiều", "icon": "🌦️", "period": "afternoon"}
        else:
            return {"name": "Mưa rào sáng", "icon": "🌦️", "period": "morning"}

    # 63, 65: Moderate / Heavy Rain
    elif weather_code in (63, 65):
        if is_night:
            return {"name": "Đêm có mưa to", "icon": "🌧️", "period": "night"}
        elif is_afternoon:
            return {"name": "Mưa to chiều", "icon": "🌧️", "period": "afternoon"}
        else:
            return {"name": "Mưa to sáng", "icon": "🌧️", "period": "morning"}

    # 71, 73, 75, 77: Snow
    elif weather_code in (71, 73, 75, 77, 85, 86):
        return {"name": "Có tuyết rơi", "icon": "🌨️", "period": "day"}

    # 80: Slight showers
    elif weather_code == 80:
        if is_night:
            return {"name": "Mưa rào đêm", "icon": "🌧️", "period": "night"}
        elif is_afternoon:
            return {"name": "Mưa rào chiều", "icon": "🌦️", "period": "afternoon"}
        else:
            return {"name": "Mưa rào sáng", "icon": "🌦️", "period": "morning"}

    # 81, 82: Moderate / Violent showers
    elif weather_code in (81, 82):
        if is_night:
            return {"name": "Mưa lớn đêm", "icon": "🌧️", "period": "night"}
        elif is_afternoon:
            return {"name": "Mưa lớn chiều", "icon": "🌧️", "period": "afternoon"}
        else:
            return {"name": "Mưa lớn sáng", "icon": "🌧️", "period": "morning"}

    # 95, 96, 99: Thunderstorm
    elif weather_code in (95, 96, 99):
        if is_night:
            return {"name": "Dông sét đêm", "icon": "⛈️", "period": "night"}
        elif is_afternoon:
            return {"name": "Dông sét chiều", "icon": "⛈️", "period": "afternoon"}
        else:
            return {"name": "Dông sét sáng", "icon": "⛈️", "period": "morning"}

    return {"name": "Trời quang", "icon": "☀️" if not is_night else "🌙", "period": "day" if not is_night else "night"}


def resolve_daily_forecast_meta(weather_code):
    """Mô tả dự báo tổng quát cho các ngày tiếp theo trong lịch"""
    if weather_code == 0:
        return {"name": "Nắng ráo", "icon": "☀️"}
    elif weather_code == 1:
        return {"name": "Trời ít mây", "icon": "🌤️"}
    elif weather_code == 2:
        return {"name": "Nắng xen mây", "icon": "⛅"}
    elif weather_code == 3:
        return {"name": "Nhiều mây", "icon": "☁️"}
    elif weather_code in (45, 48):
        return {"name": "Có sương mù", "icon": "🌫️"}
    elif weather_code in (51, 53, 55):
        return {"name": "Mưa phùn", "icon": "🌦️"}
    elif weather_code in (61, 63, 65, 80, 81, 82):
        return {"name": "Có mưa rào", "icon": "🌧️"}
    elif weather_code in (95, 96, 99):
        return {"name": "Có dông sét", "icon": "⛈️"}
    elif weather_code in (71, 73, 75, 77, 85, 86):
        return {"name": "Có tuyết", "icon": "❄️"}
    return {"name": "Trời đẹp", "icon": "🌤️"}


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
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,is_day&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto"
        req = urllib.request.Request(url, headers={"User-Agent": "WinterArc/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            current = data.get("current", {})
            daily = data.get("daily", {})
            
            temp = round(current.get("temperature_2m", 25))
            code = current.get("weather_code", 0)
            is_day = current.get("is_day", 1)
            meta = resolve_weather_meta(code, is_day=is_day)
            
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
            tomorrow_meta = resolve_daily_forecast_meta(tomorrow_code)
            tomorrow_max = round(daily_maxs[1]) if len(daily_maxs) > 1 else temp_max
            tomorrow_min = round(daily_mins[1]) if len(daily_mins) > 1 else temp_min
            tomorrow_rain = round(daily_rains[1]) if len(daily_rains) > 1 else 0
            
            # Multi-day forecast mapping by YYYY-MM-DD
            forecast_map = {}
            for i, d_str in enumerate(daily_times):
                d_code = daily_codes[i] if i < len(daily_codes) else 0
                d_meta = resolve_daily_forecast_meta(d_code)
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
                "period": meta.get("period", "day"),
                "is_day": is_day,
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
            "condition": "Trời ít mây",
            "icon": "🌤️",
            "rain_chance": 0,
            "weather_code": 1
        }
        hour_now = datetime.now().hour
        meta_fallback = resolve_weather_meta(0, is_day=1 if 6 <= hour_now < 18 else 0, hour=hour_now)
        return {
            "success": False,
            "city": city,
            "temperature": 26,
            "condition": meta_fallback["name"],
            "icon": meta_fallback["icon"],
            "period": meta_fallback["period"],
            "is_day": 1 if 6 <= hour_now < 18 else 0,
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


