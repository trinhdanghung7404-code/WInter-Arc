// ==============================================================================
// WINTER ARC APPLE WIDGETS - DESKTOP CONTROLLER
// Hoàn toàn linh hoạt từ data/protocols.json - Không Hardcode
// ==============================================================================

let currentTimerTaskId = 'english';
let currentTimerTargetMinutes = 120;
let timerSeconds = 120 * 60;
let timerRunning = false;
let timerInterval = null;
let isAlwaysOnTop = true;
let isDraggingWindow = false;
let isCompactMode = false;

const fallbackApi = {
  get_today: async () => ({
    date_str: "2026-10-01",
    yesterday_str: "2026-09-30",
    weekday: "Thứ Năm",
    day_num: 1,
    total_days: 92,
    tasks: [
      { id: "pushups", name: "50 cái chống đẩy", icon: "💪", type: "todo", completed: false, time_desc: "Khởi động buổi sáng" },
      { id: "english", name: "Học Tiếng Anh", icon: "🇬🇧", type: "timer", target_minutes: 120, completed: false },
      { id: "project", name: "Làm Đồ Án", icon: "💻", type: "timer", target_minutes: 90, completed: false },
      { id: "nonut", name: "Kỷ luật No Nut (Hôm qua)", icon: "🚫", type: "retro", completed: false, time_desc: "Đánh giá 24h trọn vẹn hôm qua" },
      { id: "detox_mxh", name: "Không lướt đt trước khi ngủ", icon: "📵", type: "retro", completed: false, time_desc: "Đánh giá buổi tối hôm qua" }
    ],
    timer_tasks: [
      { id: "english", name: "Học Tiếng Anh", icon: "🇬🇧", target_minutes: 120, studied_minutes: 0, completed: false },
      { id: "project", name: "Làm Đồ Án", icon: "💻", target_minutes: 90, studied_minutes: 0, completed: false }
    ],
    completed_count: 0,
    total_tasks: 5,
    completion_rate: 0,
    nonut_streak: 0,
    winter_arc_streak: 0
  }),
  toggle_task: async (id) => fallbackApi.get_today(),
  add_focus_minutes: async (type, mins) => fallbackApi.get_today(),
  move_delta: async (dx, dy) => true,
  start_drag: async () => true,
  toggle_pin: async () => !isAlwaysOnTop,
  get_pin_status: async () => isAlwaysOnTop,
  set_compact_mode: async (compact) => compact,
  open_manager: async () => {
    alert("Vui lòng khởi động manager.bat trong thư mục để quản lý mục tiêu!");
    return true;
  },
  get_config: async () => ({ telegram: { bot_token: "", chat_id: "" } }),
  save_config: async (cfg) => true,
  send_test_telegram: async () => ({ success: false, message: "Hãy nhập Bot Token trước" })
};

function getApi() {
  if (window.pywebview && window.pywebview.api) {
    return window.pywebview.api;
  }
  return fallbackApi;
}

function formatTime(totalSec) {
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

async function loadData() {
  try {
    const api = getApi();
    const data = await api.get_today();
    renderToday(data);
  } catch (err) {
    console.error("Error loading today data:", err);
  }
}

function renderToday(data) {
  if (!data) return;

  // 1. Calendar Widget
  document.getElementById('cal-weekday').innerText = data.weekday || "Thứ Hai";
  document.getElementById('cal-month').innerText = "TH 10";
  document.getElementById('cal-day-num').innerText = String(data.day_num || 1).padStart(2, '0');
  document.getElementById('cal-target-sub').innerText = `Ngày ${data.day_num || 1}/${data.total_days || 92}`;
  document.getElementById('cal-streak-badge').innerText = `🔥 ${data.nonut_streak || 0}d`;

function getRingSvg(id) {
  const tid = (id || '').toLowerCase();
  if (tid.includes('pushup') || tid.includes('chong_day')) {
    return `<svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>`;
  }
  if (tid.includes('english') || tid.includes('tieng_anh')) {
    return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>`;
  }
  if (tid.includes('sleep') || tid.includes('ngu') || tid.includes('detox')) {
    return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>`;
  }
  if (tid.includes('workout') || tid.includes('gym') || tid.includes('the_duc')) {
    return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6.5 6.5 11 11"/><path d="m21 21-1-1a2 2 0 0 0-2.83 0l-1.17 1.17a2 2 0 0 0 0 2.83l1 1a2 2 0 0 0 2.83 0l1.17-1.17a2 2 0 0 0 0-2.83Z"/><path d="m3 3 1 1a2 2 0 0 0 2.83 0l1.17-1.17a2 2 0 0 0 0-2.83l-1-1a2 2 0 0 0-2.83 0L3 1.17a2 2 0 0 0 0 2.83Z"/><path d="m18 15 1.41-1.41a2 2 0 0 0 0-2.83L13.24 4.59a2 2 0 0 0-2.83 0L9 6"/><path d="m6 9-1.41 1.41a2 2 0 0 0 0 2.83l6.17 6.17a2 2 0 0 0 2.83 0L15 18"/></svg>`;
  }
  if (tid.includes('nonut') || tid.includes('no_nut') || tid.includes('fire') || tid.includes('flame')) {
    return `<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>`;
  }
  return `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>`;
}

  // 2. Activity Rings (Cập nhật chuẩn xác theo 4 trụ cột thói quen)
  const rings = [
    { boxId: 'ring-box-pushups', fillId: 'ring-pushups', key: 'pushup' },
    { boxId: 'ring-box-english', fillId: 'ring-english', key: 'english' },
    { boxId: 'ring-box-sleep',   fillId: 'ring-sleep',   key: 'sleep' },
    { boxId: 'ring-box-nonut',   fillId: 'ring-nonut',   key: 'nonut' }
  ];

  const tasksList = data.tasks || [];
  rings.forEach((r, idx) => {
    const box = document.getElementById(r.boxId);
    const fill = document.getElementById(r.fillId);
    let t = tasksList.find(x => (x.id || '').toLowerCase().includes(r.key));
    if (!t) t = tasksList[idx];

    if (t && box && fill) {
      box.style.display = 'flex';
      box.title = `${t.name} (${t.completed ? 'Hoàn thành' : 'Chưa xong'})`;
      const iconSpan = box.querySelector('.ring-icon');
      if (iconSpan) iconSpan.innerHTML = getRingSvg(t.id);

      let percent = t.completed ? 100 : 0;
      if (t.type === 'timer' && data.timer_tasks) {
        const timerItem = data.timer_tasks.find(x => x.id === t.id);
        if (timerItem) {
          const target = timerItem.target_minutes || 60;
          const studied = timerItem.studied_minutes || 0;
          percent = Math.min(100, Math.round((studied / target) * 100));
        }
      }
      fill.setAttribute('stroke-dasharray', `${percent}, 100`);
    } else if (box) {
      const fillEl = document.getElementById(r.fillId);
      if (fillEl) fillEl.setAttribute('stroke-dasharray', '0, 100');
    }
  });

  // 3. Dynamic Focus Timer Tabs (Sinh tự động từ timer_tasks trong protocols.json)
  renderTimerTabs(data.timer_tasks || []);

  // 4. Protocol Widget
  const statEl = document.getElementById('protocol-stat');
  if (statEl) {
    statEl.innerText = `${data.completed_count || 0}/${data.total_tasks || 0} (${data.completion_rate || 0}%)`;
  }

  // Cập nhật thanh tóm tắt khi ở chế độ Rút Gọn (Compact)
  const compactStatus = document.getElementById('compact-status-text');
  if (compactStatus) {
    compactStatus.innerText = `🎯 ${data.completed_count || 0}/${data.total_tasks || 0} (${data.completion_rate || 0}%)`;
  }

  // Render Protocol Checklist
  const container = document.getElementById('protocol-list');
  container.innerHTML = '';

  if (tasksList.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 12px 5px; color: #64748b; font-size: 0.65rem;">
        Chưa có nhiệm vụ hôm nay.
      </div>
    `;
    return;
  }

// Render Apple-Grade Squircle Task Icon Badge (100% Modern SVG Squircle System)
function renderTaskBadge(task) {
  const icon = (task.icon || '').trim();
  const id = (task.id || '').toLowerCase();
  const name = (task.name || '').toLowerCase();
  const iconSize = 13;

  // 1. Blue Lightning Bolt (Sức mạnh / Chống đẩy)
  if (icon === '💪' || icon === '⚡' || id.includes('pushup') || id.includes('chong_day') || name.includes('chống đẩy')) {
    return `
      <div class="task-badge badge-blue" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="currentColor">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </div>
    `;
  }

  // 2. Purple Book (Tiếng Anh / Học tập)
  if (icon === '🇬🇧' || icon === '📚' || id.includes('english') || id.includes('tieng_anh') || name.includes('tiếng anh')) {
    return `
      <div class="task-badge badge-purple" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
      </div>
    `;
  }

  // 3. Green Laptop (Làm Đồ Án / Code / Laptop)
  if (icon === '💻' || icon === '🖥️' || id.includes('project') || id.includes('do_an') || id.includes('code') || name.includes('đồ án')) {
    return `
      <div class="task-badge badge-green" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect width="18" height="12" x="3" y="4" rx="2"/>
          <line x1="2" x2="22" y1="20" y2="20"/>
        </svg>
      </div>
    `;
  }

  // 4. Orange Dumbbell (Gym / Thể thao / Thể dục)
  if (icon.includes('🏋') || id.includes('workout') || id.includes('gym') || id.includes('the_duc') || name.includes('thể dục')) {
    return `
      <div class="task-badge badge-orange" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="m6.5 6.5 11 11"/>
          <path d="m21 21-1-1a2 2 0 0 0-2.83 0l-1.17 1.17a2 2 0 0 0 0 2.83l1 1a2 2 0 0 0 2.83 0l1.17-1.17a2 2 0 0 0 0-2.83Z"/>
          <path d="m3 3 1 1a2 2 0 0 0 2.83 0l1.17-1.17a2 2 0 0 0 0-2.83l-1-1a2 2 0 0 0-2.83 0L3 1.17a2 2 0 0 0 0 2.83Z"/>
          <path d="m18 15 1.41-1.41a2 2 0 0 0 0-2.83L13.24 4.59a2 2 0 0 0-2.83 0L9 6"/>
          <path d="m6 9-1.41 1.41a2 2 0 0 0 0 2.83l6.17 6.17a2 2 0 0 0 2.83 0L15 18"/>
        </svg>
      </div>
    `;
  }

  // 5. Indigo Open Book (Đọc sách)
  if (icon === '📖' || id.includes('read') || id.includes('doc') || name.includes('đọc')) {
    return `
      <div class="task-badge badge-indigo" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 7v14"/>
          <path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>
        </svg>
      </div>
    `;
  }

  // 6. Cyan Water Droplet (Uống nước)
  if (icon === '💧' || id.includes('water') || id.includes('nuoc') || name.includes('nước')) {
    return `
      <div class="task-badge badge-cyan" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>
        </svg>
      </div>
    `;
  }

  // 7. Red Flame (Kỷ luật / No Nut)
  if (icon === '🔥' || icon === '🚫' || id.includes('nonut') || id.includes('no_nut') || name.includes('no nut')) {
    return `
      <div class="task-badge badge-red" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="currentColor">
          <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>
        </svg>
      </div>
    `;
  }

  // 8. Slate Phone-Off (Detox MXH)
  if (icon === '📵' || id.includes('detox') || id.includes('phone') || name.includes('điện thoại')) {
    return `
      <div class="task-badge badge-slate" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect width="14" height="20" x="5" y="2" rx="2" ry="2"/>
          <path d="m2 2 20 20"/>
          <line x1="12" x2="12.01" y1="18" y2="18"/>
        </svg>
      </div>
    `;
  }

  // 9. Teal Meditation (Thiền)
  if (icon === '🧘' || id.includes('thien') || id.includes('meditat') || name.includes('thiền')) {
    return `
      <div class="task-badge badge-teal" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="4" r="1"/>
          <path d="M6 8h12l-2 8H8z"/>
          <path d="M6 8 4 18"/>
          <path d="m18 8 2 10"/>
        </svg>
      </div>
    `;
  }

  // 10. Amber Runner (Chạy bộ / Cardio)
  if (icon === '🏃' || id.includes('run') || id.includes('chay') || name.includes('chạy')) {
    return `
      <div class="task-badge badge-amber" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="13" cy="4" r="1"/>
          <path d="M6 8.8 10 8l2 4 2-3 2 1.8"/>
          <path d="m10 16 1.5-4L14 14l2-2.5"/>
          <path d="m6 20 2-4"/>
          <path d="m18 20-2-5.5"/>
        </svg>
      </div>
    `;
  }

  // 11. Violet Crescent (Giấc ngủ)
  if (icon === '🌙' || icon === '💤' || id.includes('sleep') || id.includes('ngu') || name.includes('ngủ')) {
    return `
      <div class="task-badge badge-violet" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
        </svg>
      </div>
    `;
  }

  // 12. Rose Boxing Glove (Boxing / Đấm bốc)
  if (icon === '🥊' || id.includes('box') || id.includes('dam') || name.includes('boxing')) {
    return `
      <div class="task-badge badge-rose" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"/>
          <path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"/>
          <path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"/>
          <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8H8a8 8 0 0 1-8-8v-5a1 1 0 0 1 1-1 2 2 0 0 1 2 2v2.5"/>
        </svg>
      </div>
    `;
  }

  // 13. Lime Leaf (Ăn uống lành mạnh / Salad)
  if (icon === '🥗' || icon === '🌿' || id.includes('diet') || id.includes('salad') || name.includes('ăn')) {
    return `
      <div class="task-badge badge-lime" title="${escapeHtml(task.name)}">
        <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z"/>
          <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
        </svg>
      </div>
    `;
  }

  // Default Fallback: Clean Target SVG (TUYỆT ĐỐI KHÔNG HIỆN EMOJI)
  return `
    <div class="task-badge badge-target" title="${escapeHtml(task.name || 'Mục tiêu')}">
      <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2">
        <circle cx="12" cy="12" r="10"/>
        <circle cx="12" cy="12" r="6"/>
        <circle cx="12" cy="12" r="2"/>
      </svg>
    </div>
  `;
}


  tasksList.forEach(task => {
    const row = document.createElement('div');
    row.className = `task-row ${task.completed ? 'done' : ''}`;
    
    row.onclick = async (e) => {
      e.stopPropagation();
      const api = getApi();
      const updated = await api.toggle_task(task.id);
      renderToday(updated);
    };

    let tagHtml = '';
    if (task.type === 'retro') {
      tagHtml = `<span class="tag-retro">Hôm qua</span>`;
    } else if (task.type === 'timer') {
      tagHtml = `<span class="tag-timer">${task.target_minutes || 60}p</span>`;
    }

    row.innerHTML = `
      <div class="task-left-wrap">
        ${renderTaskBadge(task)}
        <span class="t-title">${escapeHtml(task.name)}${tagHtml}</span>
      </div>
      <div class="t-check-circle">
        <span class="t-check-mark">✓</span>
      </div>
    `;
    container.appendChild(row);
  });
}

// -----------------------------------------------------------------------------
// Render Dynamic Timer Tabs
// -----------------------------------------------------------------------------
function renderTimerTabs(timerTasks) {
  const tabsContainer = document.getElementById('timer-tabs-container');
  if (!tabsContainer) return;

  if (timerTasks.length === 0) {
    tabsContainer.innerHTML = `<button class="t-tab active" data-id="focus" data-mins="25"><span class="tab-indicator dot-cyan"></span><span>Pomodoro</span></button>`;
    if (!timerRunning) {
      currentTimerTaskId = 'focus';
      currentTimerTargetMinutes = 25;
      document.getElementById('timer-accum').innerText = `Mục tiêu: 25p`;
    }
    return;
  }

  // Đảm bảo task hiện tại hợp lệ
  const activeExists = timerTasks.some(t => t.id === currentTimerTaskId);
  if (!activeExists) {
    currentTimerTaskId = timerTasks[0].id;
    currentTimerTargetMinutes = timerTasks[0].target_minutes || 60;
    if (!timerRunning) {
      timerSeconds = currentTimerTargetMinutes * 60;
      updateTimerDisplay();
    }
  }

  // Render tab buttons
  tabsContainer.innerHTML = '';
  timerTasks.forEach(t => {
    const btn = document.createElement('button');
    btn.className = `t-tab ${t.id === currentTimerTaskId ? 'active' : ''}`;
    btn.dataset.id = t.id;
    btn.dataset.mins = t.target_minutes || 60;

    let dotClass = 'dot-cyan';
    if (t.id.includes('project')) dotClass = 'dot-purple';
    else if (t.id.includes('workout')) dotClass = 'dot-orange';

    btn.innerHTML = `<span class="tab-indicator ${dotClass}"></span><span>${escapeHtml(t.name)}</span>`;

    btn.onclick = () => {
      document.querySelectorAll('.t-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentTimerTaskId = t.id;
      currentTimerTargetMinutes = t.target_minutes || 60;

      if (!timerRunning) {
        timerSeconds = currentTimerTargetMinutes * 60;
        updateTimerDisplay();
      }
      const studied = t.studied_minutes || 0;
      const accumEl = document.getElementById('timer-accum');
      if (accumEl) accumEl.innerText = `${studied}/${currentTimerTargetMinutes}p`;
    };

    tabsContainer.appendChild(btn);
  });

  // Cập nhật nhãn thời gian đã học
  const activeTask = timerTasks.find(t => t.id === currentTimerTaskId);
  if (activeTask) {
    const studied = activeTask.studied_minutes || 0;
    const accumEl = document.getElementById('timer-accum');
    if (accumEl) accumEl.innerText = `${studied}/${activeTask.target_minutes || 60}p`;
  }
}

function updateTimerDisplay() {
  const m = Math.floor(timerSeconds / 60);
  const s = timerSeconds % 60;
  document.getElementById('timer-min').innerText = String(m).padStart(2, '0');
  document.getElementById('timer-sec').innerText = String(s).padStart(2, '0');
}

function toggleTimer() {
  if (timerRunning) {
    pauseTimer();
  } else {
    startTimer();
  }
}

function startTimer() {
  timerRunning = true;
  const playBtn = document.getElementById('btn-timer-play');
  playBtn.innerText = '❚❚';
  playBtn.classList.add('running');

  let secondsElapsed = 0;

  timerInterval = setInterval(async () => {
    if (timerSeconds > 0) {
      timerSeconds--;
      secondsElapsed++;
      updateTimerDisplay();

      if (secondsElapsed >= 60) {
        secondsElapsed = 0;
        const api = getApi();
        const updated = await api.add_focus_minutes(currentTimerTaskId, 1);
        renderToday(updated);
      }
    } else {
      pauseTimer();
      alert(`🎉 Chúc mừng! Bạn đã hoàn thành phiên tập trung!`);
      loadData();
    }
  }, 1000);
}

function pauseTimer() {
  timerRunning = false;
  clearInterval(timerInterval);
  const playBtn = document.getElementById('btn-timer-play');
  playBtn.innerText = '▶';
  playBtn.classList.remove('running');
}

function resetTimer() {
  pauseTimer();
  timerSeconds = currentTimerTargetMinutes * 60;
  updateTimerDisplay();
}

async function applyCompactMode(compact) {
  isCompactMode = !!compact;
  localStorage.setItem('winter_arc_compact', isCompactMode ? 'true' : 'false');

  const compactBar = document.getElementById('protocol-compact-bar');
  const expandedCard = document.getElementById('protocol-expanded-card');
  const toggleBtn = document.getElementById('btn-toggle-expand-top');

  if (isCompactMode) {
    if (compactBar) compactBar.classList.remove('hidden');
    if (expandedCard) expandedCard.classList.add('hidden');
    if (toggleBtn) {
      toggleBtn.innerText = '↕';
      toggleBtn.title = 'Mở rộng checklist';
      toggleBtn.classList.remove('active');
    }
  } else {
    if (compactBar) compactBar.classList.add('hidden');
    if (expandedCard) expandedCard.classList.remove('hidden');
    if (toggleBtn) {
      toggleBtn.innerText = '▲';
      toggleBtn.title = 'Thu gọn checklist';
      toggleBtn.classList.add('active');
    }
  }

  try {
    const api = getApi();
    if (api && api.set_compact_mode) {
      await api.set_compact_mode(isCompactMode);
    }
  } catch (err) {
    console.error("set_compact_mode error:", err);
  }
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}

// -----------------------------------------------------------------------------
// Document Ready Setup
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  loadData();
  updateTimerDisplay();

  // Khởi tạo chế độ Thu gọn / Mở rộng (Compact / Extend)
  const savedCompact = localStorage.getItem('winter_arc_compact') === 'true';
  applyCompactMode(savedCompact);

  // Nút chuyển đổi chế độ trên Timer Header
  const btnToggleExpandTop = document.getElementById('btn-toggle-expand-top');
  if (btnToggleExpandTop) {
    btnToggleExpandTop.onclick = () => applyCompactMode(!isCompactMode);
  }

  // Nút thu gọn trên Card Protocol
  const btnCollapse = document.getElementById('btn-collapse-protocol');
  if (btnCollapse) {
    btnCollapse.onclick = () => applyCompactMode(true);
  }

  // Nút mở rộng trên thanh Compact
  const compactBar = document.getElementById('protocol-compact-bar');
  if (compactBar) {
    compactBar.onclick = () => applyCompactMode(false);
  }
  const btnExpand = document.getElementById('btn-expand-protocol');
  if (btnExpand) {
    btnExpand.onclick = (e) => {
      e.stopPropagation();
      applyCompactMode(false);
    };
  }

  // Timer controls
  document.getElementById('btn-timer-play').onclick = toggleTimer;
  document.getElementById('btn-timer-reset').onclick = resetTimer;

  // Quản lý Ghim Cửa Sổ (Always-on-Top Pin)
  const pinBtn = document.getElementById('btn-pin');

  function updatePinUi(pinned) {
    isAlwaysOnTop = !!pinned;
    if (!pinBtn) return;
    if (isAlwaysOnTop) {
      pinBtn.classList.add('active');
      pinBtn.setAttribute('title', 'Đang ghim trên cùng (Bấm để bỏ ghim)');
    } else {
      pinBtn.classList.remove('active');
      pinBtn.setAttribute('title', 'Chưa ghim (Bấm để ghim lên trên cùng)');
    }
  }

  async function syncPinStatus() {
    try {
      const api = getApi();
      if (api && api.get_pin_status) {
        const pinned = await api.get_pin_status();
        updatePinUi(pinned);
      }
    } catch (e) {
      console.warn("Lỗi kiểm tra trạng thái ghim:", e);
    }
  }
  syncPinStatus();

  if (pinBtn) {
    pinBtn.onclick = async (e) => {
      e.stopPropagation();
      try {
        const api = getApi();
        if (api && api.toggle_pin) {
          const newStatus = await api.toggle_pin();
          updatePinUi(newStatus);
        } else {
          updatePinUi(!isAlwaysOnTop);
        }
      } catch (err) {
        console.error("Lỗi toggle ghim:", err);
      }
    };
  }

  window.addEventListener('pywebviewready', () => {
    syncPinStatus();
    loadData();
    const savedCompact = localStorage.getItem('winter_arc_compact') === 'true';
    applyCompactMode(savedCompact);
  });

  // Mở Màn Hình Quản Lý Mục Tiêu (Dedicated Protocol Manager)
  const openManagerAction = async () => {
    try {
      const api = getApi();
      if (api.open_manager) {
        await api.open_manager();
      } else {
        alert("Khởi động file manager.bat trong thư mục để mở màn hình quản lý!");
      }
    } catch (e) {
      console.error("Open manager error:", e);
    }
  };

  // Nút trên Header của Card Protocol
  const btnOpenManager = document.getElementById('btn-open-manager');
  if (btnOpenManager) btnOpenManager.onclick = openManagerAction;

  // Nút bánh răng trên Timer Header
  const btnOpenManagerTop = document.getElementById('btn-open-manager-top');
  if (btnOpenManagerTop) btnOpenManagerTop.onclick = openManagerAction;

  // Nút to ở đáy Protocol Checklist
  const btnOpenManagerBottom = document.getElementById('btn-open-manager-bottom');
  if (btnOpenManagerBottom) btnOpenManagerBottom.onclick = openManagerAction;

  // Nút thu gọn xuống khay hệ thống (Tray)
  const btnHideTray = document.getElementById('btn-hide-tray');
  if (btnHideTray) {
    btnHideTray.onclick = async (e) => {
      e.stopPropagation();
      try {
        const api = getApi();
        if (api && api.hide_window) {
          await api.hide_window();
        }
      } catch (err) {
        console.error("Hide to tray error:", err);
      }
    };
  }

  // Settings Modal (Telegram iPhone)
  const modal = document.getElementById('settings-modal');
  const btnSettings = document.getElementById('btn-settings');
  if (btnSettings && modal) {
    btnSettings.onclick = async () => {
      const api = getApi();
      const cfg = await api.get_config();
      document.getElementById('input-token').value = cfg.telegram?.bot_token || '';
      document.getElementById('input-chat').value = cfg.telegram?.chat_id || '';
      modal.classList.remove('hidden');
    };
  }

  const btnCloseModal = document.getElementById('btn-close-modal');
  if (btnCloseModal && modal) {
    btnCloseModal.onclick = () => modal.classList.add('hidden');
  }

  const btnSaveCfg = document.getElementById('btn-save-cfg');
  if (btnSaveCfg && modal) {
    btnSaveCfg.onclick = async () => {
      const api = getApi();
      const cfg = await api.get_config();
      cfg.telegram = {
        bot_token: document.getElementById('input-token').value.trim(),
        chat_id: document.getElementById('input-chat').value.trim()
      };
      await api.save_config(cfg);
      modal.classList.add('hidden');
      alert("Đã lưu cài đặt Telegram!");
    };
  }

  // Ping iPhone Test
  const btnTgPing = document.getElementById('btn-tg-ping');
  if (btnTgPing) {
    btnTgPing.onclick = async () => {
      const api = getApi();
      const res = await api.send_test_telegram();
      if (res && res.success) {
        alert("✅ Đã bắn thông báo sang iPhone thành công!");
      } else {
        alert(`⚠️ Thông báo: ${res ? res.message : 'Hãy nhập Bot Token trước nhé!'}`);
      }
    };
  }

  // Di chuyển cửa sổ Native Windows (Zero Lag, Zero Deadlock, 0ms latency)
  const dragHandle = document.getElementById('drag-handle');
  if (dragHandle) {
    dragHandle.addEventListener('mousedown', (e) => {
      // Không kéo khi bấm vào các thành phần tương tác
      if (e.target.closest('button, input, .t-check-circle, .task-row, .modal-backdrop, .btn-manage-pill, .btn-manage-full, .t-tab, .t-check-mark')) {
        return;
      }
      if (e.button === 0) { // Chuột trái
        const api = getApi();
        if (api && api.start_drag) {
          api.start_drag();
        }
      }
    });
  }

  // Tự động đồng bộ mỗi 3.5 giây khi không chạy timer để cập nhật thay đổi từ manager.html
  setInterval(() => {
    if (!timerRunning) {
      loadData();
    }
  }, 3500);

  // Tự động tải lại khi cửa sổ được focus
  window.addEventListener('focus', loadData);
});
