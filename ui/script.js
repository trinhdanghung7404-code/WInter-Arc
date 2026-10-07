// ==============================================================================
// WINTER ARC APPLE WIDGETS - DESKTOP CONTROLLER
// Hoàn toàn linh hoạt từ data/protocols.json - Không Hardcode
// ==============================================================================

let currentTimerTaskId = 'english';
let currentTimerTargetMinutes = 120;
let timerSeconds = 120 * 60;
let taskTimerSeconds = {};
let timerAccumSeconds = 0;
let timerRunning = false;
let timerInterval = null;
let isAlwaysOnTop = true;
let isDraggingWindow = false;
let isCompactMode = false;
let inspectedDateStr = null;

const fallbackApi = {
  get_today: async () => ({
    date_str: (new Date()).toISOString().slice(0, 10),
    yesterday_str: "",
    weekday: "Today",
    day_num: 1,
    total_days: 90,
    tasks: [],
    timer_tasks: [],
    completed_count: 0,
    total_tasks: 0,
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
    alert("Please run manager.bat in the folder to manage protocols!");
    return true;
  },
  get_config: async () => ({ telegram: { bot_token: "", chat_id: "" } }),
  save_config: async (cfg) => true,
  send_test_telegram: async () => ({ success: false, message: "Please enter Bot Token first" }),
  get_weather: async (force) => ({
    success: true,
    city: "Hanoi",
    temperature: 28,
    condition: "Clear Sky",
    icon: "☀️",
    humidity: 45,
    wind_speed: 10,
    temp_max: 28,
    temp_min: 22,
    tomorrow: {
      date: (new Date(Date.now() + 86400000)).toISOString().slice(0, 10),
      temp_max: 29,
      temp_min: 20,
      avg_temp: 24,
      condition: "Mainly Clear",
      icon: "🌤️",
      rain_chance: 0,
      weather_code: 1
    }
  })
};

let lastWeatherData = null;
let weatherDisplayMode = 'auto'; // 'auto' (follows inspected date), 'today', 'tomorrow'

async function ensureApiReady(maxRetries = 25, delay = 80) {
  for (let i = 0; i < maxRetries; i++) {
    if (window.pywebview && window.pywebview.api) {
      return window.pywebview.api;
    }
    await new Promise(r => setTimeout(r, delay));
  }
  return null;
}

function getApi() {
  if (window.pywebview && window.pywebview.api) {
    return window.pywebview.api;
  }
  return fallbackApi;
}

function updateLiveClock() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  const ss = String(now.getSeconds()).padStart(2, '0');

  const hhEl = document.getElementById('clock-hh');
  const mmEl = document.getElementById('clock-mm');
  const ssEl = document.getElementById('clock-ss');
  const datePill = document.getElementById('clock-date-pill');

  if (hhEl) hhEl.innerText = hh;
  if (mmEl) mmEl.innerText = mm;
  if (ssEl) ssEl.innerText = `.${ss}`;

  if (datePill) {
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    datePill.innerText = `${days[now.getDay()]}, ${months[now.getMonth()]} ${String(now.getDate()).padStart(2, '0')}`;
  }
}

function renderWeatherDisplay(w, customMode = null) {
  if (!w) return;
  lastWeatherData = w;

  const iconEl = document.getElementById('top-weather-icon');
  const tempEl = document.getElementById('top-weather-temp');
  const cityEl = document.getElementById('top-weather-city');
  const condEl = document.getElementById('top-weather-cond');
  const blockEl = document.getElementById('top-weather-block');

  const todayStr = (new Date()).toISOString().slice(0, 10);
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().slice(0, 10);

  let mode = customMode || weatherDisplayMode;
  if (mode === 'auto') {
    if (inspectedDateStr && inspectedDateStr === tomorrowStr) {
      mode = 'tomorrow';
    } else if (inspectedDateStr && inspectedDateStr !== todayStr && w.forecast_map && w.forecast_map[inspectedDateStr]) {
      mode = 'custom_date';
    } else {
      mode = 'today';
    }
  }

  if (mode === 'tomorrow' && w.tomorrow) {
    const tm = w.tomorrow;
    if (iconEl) iconEl.innerText = tm.icon || '🌤️';
    if (tempEl) tempEl.innerText = `${tm.temp_max}°`;
    if (cityEl) {
      cityEl.innerText = 'TOMORROW';
      cityEl.style.background = 'rgba(255, 159, 10, 0.2)';
      cityEl.style.color = '#ff9f0a';
      cityEl.style.borderColor = 'rgba(255, 159, 10, 0.4)';
    }
    const rainStr = tm.rain_chance > 0 ? ` • 🌧️ ${tm.rain_chance}%` : '';
    if (condEl) condEl.innerText = `${tm.condition || 'Clear'}${rainStr}`;
    if (blockEl) {
      blockEl.title = `[TOMORROW ${tm.date} FORECAST] ${w.city || 'Hanoi'}: ${tm.condition || 'Mainly Clear'} (${tm.temp_max}° / ${tm.temp_min}°C)${rainStr} • Click to toggle Today/Tomorrow`;
    }
  } else if (mode === 'custom_date' && w.forecast_map && w.forecast_map[inspectedDateStr]) {
    const fd = w.forecast_map[inspectedDateStr];
    if (iconEl) iconEl.innerText = fd.icon || '☀️';
    if (tempEl) tempEl.innerText = `${fd.temp_max}°`;
    if (cityEl) {
      cityEl.innerText = inspectedDateStr.slice(5);
      cityEl.style.background = 'rgba(168, 85, 247, 0.2)';
      cityEl.style.color = '#c084fc';
      cityEl.style.borderColor = 'rgba(168, 85, 247, 0.4)';
    }
    const rainStr = fd.rain_chance > 0 ? ` • 🌧️ ${fd.rain_chance}%` : '';
    if (condEl) condEl.innerText = `${fd.condition || 'Forecast'}${rainStr}`;
    if (blockEl) {
      blockEl.title = `[${inspectedDateStr} FORECAST] ${w.city || 'Hanoi'}: ${fd.condition} (${fd.temp_max}° / ${fd.temp_min}°C)${rainStr}`;
    }
  } else {
    if (iconEl) iconEl.innerText = w.icon || '☀️';
    if (tempEl) tempEl.innerText = `${w.temperature !== undefined ? w.temperature : 28}°`;
    if (cityEl) {
      cityEl.innerText = (w.city || 'HANOI').toUpperCase();
      cityEl.style.background = 'rgba(56, 189, 248, 0.15)';
      cityEl.style.color = '#38bdf8';
      cityEl.style.borderColor = 'rgba(56, 189, 248, 0.25)';
    }
    if (condEl) condEl.innerText = w.condition || 'Clear Sky';
    if (blockEl) {
      const rangeStr = (w.temp_max !== undefined && w.temp_min !== undefined) ? ` (H:${w.temp_max}° L:${w.temp_min}°)` : '';
      const tmStr = w.tomorrow ? ` | Tomorrow: ${w.tomorrow.icon} ${w.tomorrow.temp_max}°/${w.tomorrow.temp_min}°` : '';
      blockEl.title = `[TODAY] ${w.city || 'Hanoi'}: ${w.condition || 'Clear Sky'} ${w.temperature}°C${rangeStr} • Humidity: ${w.humidity || 50}%${tmStr} • Click to toggle Tomorrow`;
    }
  }
}

async function loadWeather() {
  try {
    const api = getApi();
    if (api && api.get_weather) {
      const w = await api.get_weather();
      if (w) {
        renderWeatherDisplay(w);
      }
    }
  } catch (err) {
    console.warn("Weather fetch error:", err);
  }
}

function formatTime(totalSec) {
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

async function loadData() {
  try {
    let api = getApi();
    if (!window.pywebview || !window.pywebview.api) {
      const realApi = await ensureApiReady(25, 80);
      if (realApi) api = realApi;
    }
    const data = inspectedDateStr 
      ? (api.get_day_data ? await api.get_day_data(inspectedDateStr) : await api.get_today(inspectedDateStr))
      : await api.get_today();
    renderToday(data);
  } catch (err) {
    console.error("Error loading today data:", err);
  }
}

function renderToday(data) {
  if (!data) return;

  // 1. Calendar Widget
  let now = new Date();
  if (data.date_str) {
    const parts = data.date_str.split('-').map(Number);
    if (parts.length === 3) {
      now = new Date(parts[0], parts[1] - 1, parts[2]);
    }
  }
  const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
  const daysOfWeek = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  
  document.getElementById('cal-weekday').innerText = data.weekday || daysOfWeek[now.getDay()];
  document.getElementById('cal-month').innerText = months[now.getMonth()];
  document.getElementById('cal-day-num').innerText = String(now.getDate()).padStart(2, '0');

  // Update Title and Today button
  const todayIso = (new Date()).toISOString().slice(0, 10);
  const isInspectingOther = inspectedDateStr && inspectedDateStr !== todayIso;
  const titleText = document.getElementById("protocol-title-text");
  const btnTodayReset = document.getElementById("btn-widget-today-reset");
  if (titleText) {
    if (isInspectingOther) {
      titleText.innerText = `${(data.weekday || '').toUpperCase().slice(0, 3)} ${String(now.getDate()).padStart(2, '0')} ${months[now.getMonth()]}`;
    } else {
      titleText.innerText = "TODAY'S PROTOCOLS";
    }
  }
  if (btnTodayReset) {
    btnTodayReset.classList.toggle("hidden", !isInspectingOther);
  }

  const lvl = data.level_info || {};
  const stk = data.streak_info || {};
  const lvlBadge = lvl.icon ? `${lvl.icon} LV.${lvl.level || 1}` : `LV.${lvl.level || 1}`;

  document.getElementById('cal-target-sub').innerText = `${lvlBadge} • Day ${data.day_num || 1}/${data.total_days || 90}`;
  
  const streakBadge = document.getElementById('cal-streak-badge');
  if (streakBadge) {
    if (stk.type === 'grey') {
      streakBadge.innerText = `⚪ ${stk.streak || 0}d (${stk.consecutive_grey}/3)`;
      streakBadge.style.color = '#a1a1aa';
      streakBadge.title = `Grey streak: ${stk.consecutive_grey}/3 days of partial completion (50-99%). Streak will reset if > 3 consecutive days!`;
    } else if (stk.streak > 0) {
      streakBadge.innerText = `🔥 ${stk.streak}d`;
      streakBadge.style.color = '#ff9f0a';
      streakBadge.title = `Flame streak: ${stk.streak} consecutive days at 100% completion!`;
    } else {
      streakBadge.innerText = `0d`;
      streakBadge.style.color = 'var(--text-muted)';
      streakBadge.title = `No streak yet. Complete at least 50% of today's protocols to ignite your streak!`;
    }
  }


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
      box.title = `${t.name} (${t.completed ? 'Completed' : 'Pending'})`;
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

  // 3. Dynamic Focus Timer Tabs
  renderTimerTabs(data.timer_tasks || []);

  // 4. Protocol Widget
  const statEl = document.getElementById('protocol-stat');
  if (statEl) {
    statEl.innerText = `${data.completed_count || 0}/${data.total_tasks || 0} (${data.completion_rate || 0}%)`;
  }

  // Update compact bar summary (clean text, no redundant emoji)
  const compactStatus = document.getElementById('compact-status-text');
  if (compactStatus) {
    compactStatus.innerText = `${data.completed_count || 0}/${data.total_tasks || 0} (${data.completion_rate || 0}%)`;
  }

  // Render Protocol Checklist
  const container = document.getElementById('protocol-list');
  container.innerHTML = '';

  if (tasksList.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 12px 5px; color: #64748b; font-size: 0.65rem;">
        No protocols scheduled for this date.
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

  // Default Fallback: Clean Target SVG
  return `
    <div class="task-badge badge-target" title="${escapeHtml(task.name || 'Protocol')}">
      <svg viewBox="0 0 24 24" width="${iconSize}" height="${iconSize}" fill="none" stroke="currentColor" stroke-width="2.2">
        <circle cx="12" cy="12" r="10"/>
        <circle cx="12" cy="12" r="6"/>
        <circle cx="12" cy="12" r="2"/>
      </svg>
    </div>
  `;
}


  const isFutureDate = Boolean(data.is_future || (data.date_str && data.date_str > todayIso));

  tasksList.forEach(task => {
    const row = document.createElement('div');
    const isDone = !isFutureDate && task.completed;
    row.className = `task-row ${isDone ? 'done' : ''} ${isFutureDate ? 'future-disabled' : ''}`;
    
    if (isFutureDate) {
      row.title = "Upcoming protocol (cannot be checked off until this date arrives)";
      row.onclick = (e) => {
        e.stopPropagation();
      };
    } else {
      row.onclick = async (e) => {
        e.stopPropagation();
        const api = getApi();
        const updated = await api.toggle_task(task.id, inspectedDateStr || null);
        renderToday(updated);
      };
    }

    let tagHtml = '';
    if (isFutureDate) {
      if (task.type === 'retro') {
        tagHtml = `<span class="tag-upcoming">Retro</span>`;
      } else if (task.type === 'timer') {
        tagHtml = `<span class="tag-timer">${task.target_minutes || 60}m</span>`;
      }
    } else {
      if (task.type === 'retro') {
        tagHtml = `<span class="tag-retro">Yesterday</span>`;
      } else if (task.type === 'timer') {
        tagHtml = `<span class="tag-timer">${task.target_minutes || 60}m</span>`;
      }
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
  const cardTimer = document.getElementById('card-focus-timer') || document.querySelector('.card-timer');
  const tabsContainer = document.getElementById('timer-tabs-container');

  if (!timerTasks || timerTasks.length === 0) {
    // Ẩn Focus Timer khi ngày không có protocol dạng timer nào
    if (cardTimer) {
      cardTimer.style.display = 'none';
    }
    if (timerRunning) {
      pauseTimer();
    }
    return;
  }

  // Hiển thị lại Focus Timer khi có protocol timer
  if (cardTimer) {
    cardTimer.style.display = '';
  }

  if (!tabsContainer) return;

  // Ensure active task exists
  const activeTask = timerTasks.find(t => t.id === currentTimerTaskId) || timerTasks[0];
  currentTimerTaskId = activeTask.id;
  currentTimerTargetMinutes = activeTask.target_minutes || 60;

  // If this task has not been initialized in taskTimerSeconds, initialize it
  if (taskTimerSeconds[currentTimerTaskId] === undefined) {
    taskTimerSeconds[currentTimerTaskId] = currentTimerTargetMinutes * 60;
  }
  timerSeconds = taskTimerSeconds[currentTimerTaskId];
  updateTimerDisplay();

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
      if (currentTimerTaskId === t.id) return; // already active

      // Save current task remaining seconds
      taskTimerSeconds[currentTimerTaskId] = timerSeconds;

      // If timer was running, pause it when switching tasks
      if (timerRunning) {
        pauseTimer();
      }

      document.querySelectorAll('.t-tab').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentTimerTaskId = t.id;
      currentTimerTargetMinutes = t.target_minutes || 60;

      // Restore or initialize remaining seconds for the new task
      if (taskTimerSeconds[currentTimerTaskId] === undefined) {
        taskTimerSeconds[currentTimerTaskId] = currentTimerTargetMinutes * 60;
      }
      timerSeconds = taskTimerSeconds[currentTimerTaskId];
      updateTimerDisplay();

      const studied = t.studied_minutes || 0;
      const accumEl = document.getElementById('timer-accum');
      if (accumEl) accumEl.innerText = `${studied}/${currentTimerTargetMinutes}m`;
    };

    tabsContainer.appendChild(btn);
  });

  // Update accumulated focus time label
  const studied = activeTask.studied_minutes || 0;
  const accumEl = document.getElementById('timer-accum');
  if (accumEl) accumEl.innerText = `${studied}/${currentTimerTargetMinutes}m`;
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
  if (timerRunning) return;
  timerRunning = true;
  const playBtn = document.getElementById('btn-timer-play');
  if (playBtn) {
    playBtn.innerText = '❚❚';
    playBtn.classList.add('running');
  }

  timerInterval = setInterval(async () => {
    if (timerSeconds > 0) {
      timerSeconds--;
      taskTimerSeconds[currentTimerTaskId] = timerSeconds;
      timerAccumSeconds++;
      updateTimerDisplay();

      if (timerAccumSeconds >= 60) {
        timerAccumSeconds = 0;
        const api = getApi();
        const updated = await api.add_focus_minutes(currentTimerTaskId, 1);
        renderToday(updated);
      }
    } else {
      pauseTimer();
      alert(`Focus session for ${currentTimerTaskId} completed! Great job!`);
      taskTimerSeconds[currentTimerTaskId] = currentTimerTargetMinutes * 60;
      timerSeconds = currentTimerTargetMinutes * 60;
      updateTimerDisplay();
      loadData();
    }
  }, 1000);
}

function pauseTimer() {
  timerRunning = false;
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
  taskTimerSeconds[currentTimerTaskId] = timerSeconds;
  const playBtn = document.getElementById('btn-timer-play');
  if (playBtn) {
    playBtn.innerText = '▶';
    playBtn.classList.remove('running');
  }
}

function resetTimer() {
  pauseTimer();
  taskTimerSeconds[currentTimerTaskId] = currentTimerTargetMinutes * 60;
  timerSeconds = currentTimerTargetMinutes * 60;
  timerAccumSeconds = 0;
  updateTimerDisplay();
}

async function applyCompactMode(compact) {
  isCompactMode = !!compact;
  localStorage.setItem('winter_arc_compact', isCompactMode ? 'true' : 'false');

  const compactBar = document.getElementById('protocol-compact-bar');
  const expandedCard = document.getElementById('protocol-expanded-card');
  const toggleBtn = document.getElementById('btn-toggle-expand-top');

  const cardTimer = document.getElementById('card-focus-timer') || document.querySelector('.card-timer');
  const isTimerHidden = cardTimer && cardTimer.style.display === 'none';
  const topBtns = document.getElementById('timer-top-btns');

  if (isCompactMode) {
    if (compactBar) compactBar.classList.remove('hidden');
    if (expandedCard) expandedCard.classList.add('hidden');
    if (isTimerHidden && topBtns && compactBar && !compactBar.contains(topBtns)) {
      compactBar.appendChild(topBtns);
    }
    if (toggleBtn) {
      toggleBtn.innerText = '↕';
      toggleBtn.title = 'Expand checklist';
      toggleBtn.classList.remove('active');
    }
  } else {
    if (compactBar) compactBar.classList.add('hidden');
    if (expandedCard) expandedCard.classList.remove('hidden');
    if (isTimerHidden && topBtns) {
      const protocolHeadRight = document.querySelector('.protocol-head-right');
      const collapseBtn = document.getElementById('btn-collapse-protocol');
      if (protocolHeadRight && !protocolHeadRight.contains(topBtns)) {
        if (collapseBtn) protocolHeadRight.insertBefore(topBtns, collapseBtn);
        else protocolHeadRight.appendChild(topBtns);
      }
    }
    if (toggleBtn) {
      toggleBtn.innerText = '▲';
      toggleBtn.title = 'Collapse checklist';
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
  updateLiveClock();
  setInterval(updateLiveClock, 1000);
  loadData();
  loadWeather();
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
      pinBtn.setAttribute('title', 'Always on top (Click to unpin)');
    } else {
      pinBtn.classList.remove('active');
      pinBtn.setAttribute('title', 'Unpinned (Click to keep on top)');
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
      console.warn("Pin status sync error:", e);
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
        console.error("Toggle pin error:", err);
      }
    };
  }

  window.addEventListener('pywebviewready', () => {
    syncPinStatus();
    loadData();
    loadWeather();
    const savedCompact = localStorage.getItem('winter_arc_compact') === 'true';
    applyCompactMode(savedCompact);
  });

  // Open Dedicated Protocol Manager
  const openManagerAction = async () => {
    try {
      const api = getApi();
      if (api.open_manager) {
        await api.open_manager();
      } else {
        alert("Please run manager.bat in the folder to open Protocol Manager!");
      }
    } catch (e) {
      console.error("Open manager error:", e);
    }
  };

  // Header button on Protocol Card
  const btnOpenManager = document.getElementById('btn-open-manager');
  if (btnOpenManager) btnOpenManager.onclick = openManagerAction;

  // Gear button on Timer Header
  const btnOpenManagerTop = document.getElementById('btn-open-manager-top');
  if (btnOpenManagerTop) btnOpenManagerTop.onclick = openManagerAction;

  // Bottom button on Protocol Checklist
  const btnOpenManagerBottom = document.getElementById('btn-open-manager-bottom');
  if (btnOpenManagerBottom) btnOpenManagerBottom.onclick = openManagerAction;

  // Minimize to tray
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

  // Settings Modal (Telegram)
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
      alert("Telegram settings saved!");
    };
  }

  // Ping iPhone Test
  const btnTgPing = document.getElementById('btn-tg-ping');
  if (btnTgPing) {
    btnTgPing.onclick = async () => {
      const api = getApi();
      const res = await api.send_test_telegram();
      if (res && res.success) {
        alert("Test notification sent successfully!");
      } else {
        alert(`Notification: ${res ? res.message : 'Please enter Bot Token first'}`);
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

  // Day Navigation on Desktop Widget (Chuyển ngày xem danh sách nhiệm vụ các ngày khác)
  const btnPrevDay = document.getElementById("btn-widget-prev-day");
  const btnNextDay = document.getElementById("btn-widget-next-day");
  const btnTodayResetEl = document.getElementById("btn-widget-today-reset");

  function changeWidgetDay(delta) {
    let base = new Date();
    if (inspectedDateStr) {
      const p = inspectedDateStr.split('-').map(Number);
      base = new Date(p[0], p[1] - 1, p[2]);
    }
    base.setDate(base.getDate() + delta);
    const y = base.getFullYear();
    const m = String(base.getMonth() + 1).padStart(2, '0');
    const d = String(base.getDate()).padStart(2, '0');
    const newStr = `${y}-${m}-${d}`;
    const todayStr = (new Date()).toISOString().slice(0, 10);
    inspectedDateStr = (newStr === todayStr) ? null : newStr;
    loadData();
    if (lastWeatherData) {
      renderWeatherDisplay(lastWeatherData);
    }
  }

  if (btnPrevDay) btnPrevDay.addEventListener("click", () => changeWidgetDay(-1));
  if (btnNextDay) btnNextDay.addEventListener("click", () => changeWidgetDay(1));
  if (btnTodayResetEl) btnTodayResetEl.addEventListener("click", () => {
    inspectedDateStr = null;
    loadData();
    if (lastWeatherData) {
      renderWeatherDisplay(lastWeatherData);
    }
  });

  // Toggle Today / Tomorrow Forecast on Weather Block Click
  const weatherBlock = document.getElementById('top-weather-block');
  if (weatherBlock) {
    weatherBlock.addEventListener('click', () => {
      weatherDisplayMode = (weatherDisplayMode === 'tomorrow') ? 'today' : 'tomorrow';
      if (lastWeatherData) {
        renderWeatherDisplay(lastWeatherData, weatherDisplayMode);
      }
    });
  }

  // Tự động đồng bộ mỗi 3.5 giây khi không chạy timer để cập nhật thay đổi từ manager.html
  setInterval(() => {
    if (!timerRunning) {
      loadData();
    }
  }, 3500);

  // Tự động cập nhật nhiệt độ thời tiết mỗi 10 phút
  setInterval(loadWeather, 10 * 60 * 1000);

  // Tự động tải lại khi cửa sổ được focus
  window.addEventListener('focus', () => {
    loadData();
    loadWeather();
  });
});
