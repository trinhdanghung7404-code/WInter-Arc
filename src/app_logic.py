import json
import os
from datetime import datetime, date, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
STORAGE_PATH = os.path.join(DATA_DIR, "storage.json")
PROTOCOLS_PATH = os.path.join(DATA_DIR, "protocols.json")

WEEKDAY_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

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

def load_protocols():
    """Đọc danh sách mục tiêu từ file protocols.json (hoàn toàn không hardcode)"""
    if not os.path.exists(PROTOCOLS_PATH):
        return []
    try:
        with open(PROTOCOLS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("protocols", [])
    except Exception as e:
        print(f"[Protocols Load Error]: {e}")
        return []

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
    protocols = load_protocols()
    # Tự động sinh ID nếu chưa có
    if not new_item.get("id"):
        new_item["id"] = "task_" + str(int(datetime.now().timestamp()))
    new_item.setdefault("active", True)
    protocols.append(new_item)
    save_protocols(protocols)
    return protocols

def delete_protocol(item_id):
    """Xóa mục tiêu theo ID khỏi file protocols.json"""
    protocols = load_protocols()
    protocols = [p for p in protocols if p.get("id") != item_id]
    save_protocols(protocols)
    return protocols

def update_protocol(item_id, updated_fields):
    """Cập nhật mục tiêu trong file protocols.json"""
    protocols = load_protocols()
    for p in protocols:
        if p.get("id") == item_id:
            p.update(updated_fields)
            break
    save_protocols(protocols)
    return protocols

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
    """Lấy danh sách nhiệm vụ hợp lệ cho một ngày cụ thể dựa trên protocols.json"""
    all_protocols = load_protocols()
    weekday = curr_date.weekday() # 0 = T2 ... 6 = CN

    tasks_for_day = []
    for p in all_protocols:
        if not p.get("active", True):
            continue
        days = p.get("days", [0, 1, 2, 3, 4, 5, 6])
        if weekday in days:
            tasks_for_day.append(p)

    return tasks_for_day

def get_today_data():
    today = date.today()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    weekday_idx = today.weekday()
    weekday_name = WEEKDAY_VI[weekday_idx]
    
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
        
        # Nếu là loại retro (xác nhận hôm qua): kiểm tra trạng thái trong bản ghi của ngày hôm qua
        if t_type == "retro":
            is_done = yesterday_record["tasks"].get(tid, False)
            eval_date_label = f"Hôm qua ({yesterday.strftime('%d/%m')})"
        else:
            is_done = day_record["tasks"].get(tid, False)
            eval_date_label = "Hôm nay"

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
            studied_mins = day_record.get("focus_times", {}).get(tid, 0)
            timer_tasks_result.append({
                "id": tid,
                "name": t.get("name", "Nhiệm vụ"),
                "icon": t.get("icon", "⏱️"),
                "target_minutes": t.get("target_minutes", 60),
                "studied_minutes": studied_mins,
                "completed": is_done
            })

    day_num, total_days = get_day_number(today)
    completion_rate = int((completed_count / len(task_defs)) * 100) if task_defs else 0

    nonut_streak = calculate_streak("nonut", history)
    streak_info = calculate_winter_arc_streak(history)
    winter_arc_streak = streak_info.get("streak", 0)
    level_info = calculate_level_info(day_num, total_days)

    storage["streaks"]["nonut"] = nonut_streak
    storage["streaks"]["winter_arc"] = winter_arc_streak
    save_storage(storage)

    english_mins = day_record.get("focus_times", {}).get("english", 0)
    project_mins = day_record.get("focus_times", {}).get("project", 0)

    return {
        "date_str": today_str,
        "yesterday_str": yesterday_str,
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
    """
    today = date.today()
    yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

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

    return get_today_data()

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
                "badge": "Chưa có chuỗi",
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
                    "badge": "Mất chuỗi (>3 ngày xám)",
                    "consecutive_grey": consecutive_grey,
                    "warning": True,
                    "warning_msg": "Bạn đã có hơn 3 ngày chuỗi xám liên tiếp. Chuỗi đã bị đặt lại về 0!"
                }
            streak += 1
        else:
            # status == 'lost' (< 50%): Chuỗi đứt tại đây
            break

        first_day = False
        curr -= timedelta(days=1)

    # Đánh giá loại chuỗi hiển thị
    streak_type = current_day_status or "fire"
    warning = (streak_type == "grey" and consecutive_grey >= 2)
    warning_msg = f"Cảnh báo: Bạn đang có {consecutive_grey}/3 ngày chuỗi xám liên tiếp. Nếu tiếp tục làm nửa vời, bạn sẽ mất chuỗi!" if warning else ""

    if streak_type == "fire":
        badge = f"🔥 {streak} ngày bất bại"
    elif streak_type == "grey":
        badge = f"⚪ {streak} ngày (Chuỗi xám {consecutive_grey}/3)"
    else:
        badge = f"{streak} ngày"

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
            "title": "Tân Binh (Khởi Động)",
            "badge": "🌱 LEVEL 1",
            "desc": "Giai đoạn 30 ngày đầu: Phá vỡ thói quen cũ và xây dựng nền tảng kỷ luật",
            "icon": "🌱"
        },
        2: {
            "title": "Chiến Binh (Kỷ Luật Thép)",
            "badge": "⚡ LEVEL 2",
            "desc": "Giai đoạn 30 ngày giữa: Định hình thói quen thép, tốc độ và sức bền",
            "icon": "⚡"
        },
        3: {
            "title": "Bậc Thầy (Bất Khả Chiến Bại)",
            "badge": "👑 LEVEL 3",
            "desc": "Giai đoạn 30 ngày cuối: Đạt trạng thái tối thượng, làm chủ bản thân hoàn toàn",
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
