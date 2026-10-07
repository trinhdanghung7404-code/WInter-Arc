// ==============================================================================
// WINTER ARC PROTOCOL MANAGER - JAVASCRIPT
// Giao tiếp trực tiếp với Backend Python qua window.pywebview.api
// Lưu trữ 100% vào data/protocols.json (KHÔNG HARDCODE)
// ==============================================================================

// Danh sách mục tiêu hoàn toàn đọc từ backend data/protocols.json (KHÔNG HARDCODE)
const fallbackProtocols = [];

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June", 
  "July", "August", "September", "October", "November", "December"
];

// App State
let editingProtocolId = null;
let allLoadedProtocols = [];

function formatYMD(d) {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Form Calendar Sheet State (Single Date Selection Only)
let formCalendarDate = new Date();
let formSelectedDate = formatYMD(new Date());

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
  return {
    get_protocols: async () => [],
    add_protocol: async (item) => [],
    delete_protocol: async (id) => [],
    update_protocol: async (id, fields) => [],
    get_config: async () => ({ telegram: { bot_token: "", chat_id: "" }, weather: { city: "Hanoi", latitude: 21.0245, longitude: 105.8412 } }),
    save_config: async (cfg) => true,
    get_weather: async (force) => ({ success: true, city: "Hanoi", temperature: 28, condition: "Clear Sky", icon: "☀️", humidity: 45, wind_speed: 10 }),
    search_city: async (q) => [],
    set_weather_location: async (c, lat, lon) => ({ success: true, city: c, temperature: 28, condition: "Clear Sky", icon: "☀️" })
  };
}

// -----------------------------------------------------------------------------
// Format schedule helpers
// -----------------------------------------------------------------------------
function formatScheduleDays(days) {
  if (!days || days.length === 0) return "Not scheduled";
  if (days.length === 7) return "Repeat Everyday";
  if (days.length === 5 && days.every(d => [0, 1, 2, 3, 4].includes(d))) return "Mon – Fri";
  if (days.length === 2 && days.includes(5) && days.includes(6)) return "Weekends (Sat – Sun)";
  return days.map(d => DAY_NAMES[d] || `D${d + 1}`).join(", ");
}

function formatProtocolSchedule(item) {
  const schedType = item.schedule_type || (item.specific_dates && item.specific_dates.length && (!item.days || !item.days.length) ? 'dates' : 'weekly');
  const dates = item.specific_dates || [];
  
  if (schedType === 'dates') {
    if (!dates.length) return "No dates set";
    if (dates.length === 1) return `Single Date: ${dates[0]}`;
    return `Dates (${dates.length} days)`;
  }
  
  if (schedType === 'both') {
    const weeklyStr = formatScheduleDays(item.days);
    const dateCount = dates.length;
    return `${weeklyStr} + ${dateCount} specific date${dateCount > 1 ? 's' : ''}`;
  }
  
  return "Repeat Everyday";
}

// -----------------------------------------------------------------------------
// Load & Render Protocols List (100% Clean Minimalist — No Emojis/Icons)
// -----------------------------------------------------------------------------
async function loadProtocols() {
  const container = document.getElementById("protocols-list-container");
  const badge = document.getElementById("active-count-badge");
  const titleEl = document.getElementById("list-section-title");
  const hintEl = document.getElementById("section-hint-text");
  
  try {
    let api = getApi();
    if (!window.pywebview || !window.pywebview.api) {
      const realApi = await ensureApiReady(25, 80);
      if (realApi) api = realApi;
    }
    const protocols = await api.get_protocols();
    allLoadedProtocols = protocols || [];

    // Filter by selected calendar date (and daily recurring tasks)
    let displayProtocols = allLoadedProtocols;
    if (formSelectedDate) {
      displayProtocols = allLoadedProtocols.filter(p => {
        if (p.active === false) return false;
        // Everyday
        if (p.schedule_type === "weekly" || (p.days && p.days.length === 7)) return true;
        // Specific dates
        if (p.schedule_type === "dates" && p.specific_dates) {
          return p.specific_dates.includes(formSelectedDate);
        }
        if (p.schedule_type === "both") {
          return (p.specific_dates && p.specific_dates.includes(formSelectedDate)) || (p.days && p.days.length === 7);
        }
        return false;
      });
    }

    if (titleEl) titleEl.innerText = "ACTIVE PROTOCOLS";
    if (hintEl) hintEl.innerText = `Scheduled for ${formSelectedDate}. Click calendar to inspect other dates.`;
    
    if (!displayProtocols || displayProtocols.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 30px; color: var(--text-muted); font-size: 0.8rem;">
          No protocols scheduled for ${formSelectedDate}.
        </div>
      `;
      badge.innerText = "0 items";
      return;
    }

    badge.innerText = `${displayProtocols.length} item${displayProtocols.length > 1 ? 's' : ''}`;
    container.innerHTML = "";

    displayProtocols.forEach((item) => {
      const card = document.createElement("div");
      const isEditing = (editingProtocolId === item.id);
      card.className = `protocol-item-card ${item.active === false ? 'inactive' : ''} ${isEditing ? 'editing' : ''}`;
      card.dataset.id = item.id;
      
      let typeLabel = "To-Do";
      let typeClass = "todo";

      if (item.type === "timer") {
        typeLabel = `Focus ${item.target_minutes || 60}m`;
        typeClass = "timer";
      } else if (item.type === "retro") {
        typeLabel = "Retro";
        typeClass = "retro";
      }

      const scheduleStr = formatProtocolSchedule(item);
      const remindTag = item.remind_time 
        ? `<span class="item-remind-tag" title="Telegram reminder at ${escapeHtml(item.remind_time)}">
            <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px; margin-right: 2px;">
              <circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 16 14"></polyline>
            </svg>${escapeHtml(item.remind_time)}</span>` 
        : '';

      const showTimeDesc = item.time_desc && item.time_desc.trim().toLowerCase() !== "daily" && item.time_desc.trim() !== "";

      card.innerHTML = `
        <div class="item-left">
          <div class="item-info">
            <div class="item-name">${escapeHtml(item.name)}</div>
            <div class="item-tags">
              <span class="tag-badge ${typeClass}">${typeLabel}</span>
              ${remindTag}
              <span class="item-schedule">${scheduleStr}${showTimeDesc ? ' • ' + escapeHtml(item.time_desc) : ''}</span>
            </div>
          </div>
        </div>
        <div class="item-actions">
          <button class="btn-edit" title="Edit schedule and details" data-id="${item.id}">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 20h9"></path>
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
            </svg>
          </button>
          <button class="btn-del" title="Delete protocol" data-id="${item.id}">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      `;

      // Handle Edit Click
      const editBtn = card.querySelector(".btn-edit");
      editBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        startEditProtocol(item.id);
      });

      // Clicking card body also edits
      card.addEventListener("click", () => {
        startEditProtocol(item.id);
      });

      // Handle delete
      const delBtn = card.querySelector(".btn-del");
      delBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        if (confirm(`Are you sure you want to delete protocol: "${item.name}"?`)) {
          if (editingProtocolId === item.id) cancelEditMode();
          const api = getApi();
          await api.delete_protocol(item.id);
          showToast(`Deleted "${item.name}"`);
          loadProtocols();
        }
      });

      container.appendChild(card);
    });

  } catch (err) {
    console.error("Load protocols error:", err);
    container.innerHTML = `<div style="color: var(--apple-red); font-size: 0.75rem;">Error loading data: ${err.message}</div>`;
  }
}

// -----------------------------------------------------------------------------
// Form Calendar Sheet (Tờ lịch chọn ngày duy nhất trong Form bên phải)
// -----------------------------------------------------------------------------
function getTomorrowDate() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d;
}

function getTomorrowStr() {
  return formatYMD(getTomorrowDate());
}

function selectInitialFormDate() {
  const today = new Date();
  formSelectedDate = formatYMD(today);
  const [y, m] = formSelectedDate.split("-").map(Number);
  formCalendarDate = new Date(y, m - 1, 1);
}

function initFormCalendarSheet() {
  selectInitialFormDate();

  // Navigation
  const btnPrev = document.getElementById("btn-form-cal-prev");
  const btnNext = document.getElementById("btn-form-cal-next");
  if (btnPrev) {
    btnPrev.addEventListener("click", () => {
      formCalendarDate.setMonth(formCalendarDate.getMonth() - 1);
      renderFormCalendarSheet();
    });
  }
  if (btnNext) {
    btnNext.addEventListener("click", () => {
      formCalendarDate.setMonth(formCalendarDate.getMonth() + 1);
      renderFormCalendarSheet();
    });
  }

  // Jump to Today
  const btnToday = document.getElementById("btn-form-cal-today");
  if (btnToday) {
    btnToday.addEventListener("click", () => {
      const today = new Date();
      formSelectedDate = formatYMD(today);
      formCalendarDate = new Date(today.getFullYear(), today.getMonth(), 1);
      renderFormCalendarSheet();
      if (currentListFilter === "selected") {
        loadProtocols();
      }
    });
  }

  // Jump to Tomorrow
  const btnTomorrow = document.getElementById("btn-form-cal-tomorrow");
  if (btnTomorrow) {
    btnTomorrow.addEventListener("click", () => {
      const tomorrow = getTomorrowDate();
      formSelectedDate = formatYMD(tomorrow);
      formCalendarDate = new Date(tomorrow.getFullYear(), tomorrow.getMonth(), 1);
      renderFormCalendarSheet();
      if (currentListFilter === "selected") {
        loadProtocols();
      }
    });
  }

  renderFormCalendarSheet();
}

function renderFormCalendarSheet() {
  const monthTitle = document.getElementById("form-cal-month-title");
  const grid = document.getElementById("form-cal-grid");
  const countBadge = document.getElementById("form-cal-selected-count");

  if (!grid || !monthTitle) return;

  const year = formCalendarDate.getFullYear();
  const month = formCalendarDate.getMonth();
  monthTitle.innerText = `${MONTH_NAMES[month]} ${year}`;

  grid.innerHTML = "";

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0).getDate();
  const todayStr = formatYMD(new Date());

  // Đảm bảo không chọn ngày quá khứ
  if (!formSelectedDate || formSelectedDate < todayStr) {
    formSelectedDate = todayStr;
  }

  let startWeekday = firstDay.getDay() - 1;
  if (startWeekday === -1) startWeekday = 6; // 0=Mon .. 6=Sun

  // Previous month trailing cells
  const prevMonthLastDay = new Date(year, month, 0).getDate();
  for (let i = startWeekday - 1; i >= 0; i--) {
    const dNum = prevMonthLastDay - i;
    const cell = document.createElement("div");
    cell.className = "form-cal-cell other-month";
    cell.innerText = dNum;
    grid.appendChild(cell);
  }

  // Days of current month - Single date selection (Disable ngày quá khứ < todayStr, cho phép todayStr và tương lai)
  for (let d = 1; d <= lastDay; d++) {
    const curDate = new Date(year, month, d);
    const dateStr = formatYMD(curDate);
    const cell = document.createElement("div");
    cell.className = "form-cal-cell";
    cell.innerText = d;

    if (dateStr === todayStr) cell.classList.add("today");

    const isPast = dateStr < todayStr;
    if (isPast) {
      cell.classList.add("disabled");
      cell.setAttribute("title", "Past date (Cannot schedule)");
    } else {
      if (dateStr === formSelectedDate) cell.classList.add("selected");
      if (dateStr === todayStr) {
        cell.setAttribute("title", "Today (Scheduled time must be >= 2 hours from now)");
      }

      cell.addEventListener("click", () => {
        formSelectedDate = dateStr;
        renderFormCalendarSheet();
        if (currentListFilter === "selected") {
          loadProtocols();
        }
      });
    }

    grid.appendChild(cell);
  }

  // Fill remaining slots
  const currentCells = grid.children.length;
  const targetCells = currentCells > 35 ? 42 : 35;
  let nextDay = 1;
  for (let i = currentCells; i < targetCells; i++) {
    const cell = document.createElement("div");
    cell.className = "form-cal-cell other-month";
    cell.innerText = nextDay++;
    grid.appendChild(cell);
  }

  // Update selected date badge (e.g. Thu, 01 Oct 2026)
  if (countBadge && formSelectedDate) {
    const [y, m, d] = formSelectedDate.split('-').map(Number);
    const dt = new Date(y, m - 1, d);
    let w = dt.getDay() - 1;
    if (w === -1) w = 6;
    const isToday = (formSelectedDate === todayStr);
    countBadge.innerText = `${DAY_NAMES[w]}, ${d} ${MONTH_NAMES[m - 1]} ${y}${isToday ? ' (Today)' : ''}`;
  }
}

// -----------------------------------------------------------------------------
// Edit Protocol & Form State Handlers
// -----------------------------------------------------------------------------
function startEditProtocol(protoId) {
  const p = allLoadedProtocols.find(x => x.id === protoId);
  if (!p) return;

  editingProtocolId = protoId;

  // Visual highlight in list
  document.querySelectorAll(".protocol-item-card").forEach(c => c.classList.remove("editing"));
  const currentCard = document.querySelector(`.protocol-item-card[data-id="${protoId}"]`);
  if (currentCard) currentCard.classList.add("editing");

  // Form title and notice bar
  const formHeading = document.getElementById("form-heading");
  const cancelBtn = document.getElementById("btn-cancel-edit");
  const noticeBar = document.getElementById("edit-notice-bar");
  const noticeName = document.getElementById("editing-proto-name");
  const submitText = document.getElementById("btn-submit-text");
  const editIdInput = document.getElementById("editing-protocol-id");

  if (formHeading) formHeading.innerText = "EDIT PROTOCOL";
  if (cancelBtn) cancelBtn.classList.remove("hidden");
  if (noticeBar) noticeBar.classList.remove("hidden");
  if (noticeName) noticeName.innerText = p.name;
  if (submitText) submitText.innerText = "UPDATE PROTOCOL";
  if (editIdInput) editIdInput.value = p.id;

  // Fill Inputs
  document.getElementById("input-name").value = p.name || "";
  document.getElementById("input-time-desc").value = p.time_desc || "";
  const remindInput = document.getElementById("input-remind-time");
  if (remindInput) {
    remindInput.value = p.remind_time || "";
    document.querySelectorAll(".btn-time-preset").forEach(b => {
      b.classList.toggle("active", b.dataset.time === (p.remind_time || ""));
    });
  }

  // Type
  const targetType = p.type || "todo";
  const typeCards = document.querySelectorAll(".type-card");
  typeCards.forEach(c => {
    const radio = c.querySelector('input[type="radio"]');
    if (radio) {
      if (radio.value === targetType) {
        c.classList.add("active");
        radio.checked = true;
      } else {
        c.classList.remove("active");
      }
    }
  });
  const fieldTargetMinutes = document.getElementById("field-target-minutes");
  if (fieldTargetMinutes) {
    if (targetType === "timer") {
      fieldTargetMinutes.classList.remove("hidden");
      document.getElementById("input-minutes").value = p.target_minutes || 60;
    } else {
      fieldTargetMinutes.classList.add("hidden");
    }
  }

  // Populate Schedule Date (Chỉ chọn 1 ngày duy nhất)
  const repeatCheck = document.getElementById("input-repeat-daily");
  const isEveryday = (p.schedule_type === 'weekly') || (p.days && p.days.length === 7);
  if (repeatCheck) repeatCheck.checked = isEveryday;

  if (p.specific_dates && p.specific_dates.length > 0) {
    formSelectedDate = p.specific_dates[0];
  } else {
    formSelectedDate = getTomorrowStr();
  }

  const [sy, sm] = formSelectedDate.split("-").map(Number);
  formCalendarDate = new Date(sy, sm - 1, 1);
  renderFormCalendarSheet();

  // Scroll to form smoothly
  document.querySelector(".form-section")?.scrollIntoView({ behavior: "smooth" });
  document.getElementById("input-name")?.focus();
}

function cancelEditMode() {
  editingProtocolId = null;

  document.querySelectorAll(".protocol-item-card").forEach(c => c.classList.remove("editing"));

  const formHeading = document.getElementById("form-heading");
  const cancelBtn = document.getElementById("btn-cancel-edit");
  const noticeBar = document.getElementById("edit-notice-bar");
  const submitText = document.getElementById("btn-submit-text");
  const editIdInput = document.getElementById("editing-protocol-id");

  if (formHeading) formHeading.innerText = "NEW PROTOCOL";
  if (cancelBtn) cancelBtn.classList.add("hidden");
  if (noticeBar) noticeBar.classList.add("hidden");
  if (submitText) submitText.innerText = "SAVE PROTOCOL";
  if (editIdInput) editIdInput.value = "";

  // Reset inputs
  document.getElementById("input-name").value = "";
  document.getElementById("input-time-desc").value = "";
  const remindInput = document.getElementById("input-remind-time");
  if (remindInput) remindInput.value = "";
  document.querySelectorAll(".btn-time-preset").forEach(b => b.classList.remove("active"));

  // Reset repeat daily
  const repeatCheck = document.getElementById("input-repeat-daily");
  if (repeatCheck) repeatCheck.checked = false;

  // Reset type to todo
  document.querySelectorAll(".type-card").forEach((c, idx) => {
    c.classList.toggle("active", idx === 0);
    const radio = c.querySelector('input[type="radio"]');
    if (radio) radio.checked = (idx === 0);
  });
  document.getElementById("field-target-minutes")?.classList.add("hidden");

  // Reset calendar selection to inspected date
  selectInitialFormDate();
  renderFormCalendarSheet();
}

// -----------------------------------------------------------------------------
// Load Telegram & AI Config
// -----------------------------------------------------------------------------
async function loadTelegramConfig() {
  try {
    let api = getApi();
    if (!window.pywebview || !window.pywebview.api) {
      const realApi = await ensureApiReady(25, 80);
      if (realApi) api = realApi;
    }
    const cfg = await api.get_config();
    const tg = cfg.telegram || {};
    const ai = cfg.ai || {};
    document.getElementById("tg-token-input").value = tg.bot_token || "";
    document.getElementById("tg-chat-input").value = tg.chat_id || "";
    const aiInput = document.getElementById("ai-token-input");
    if (aiInput) aiInput.value = ai.api_key || "";

    const activePersona = ai.persona || "david_goggins";
    const customPrompt = ai.custom_prompt || "";
    const promptInput = document.getElementById("ai-custom-prompt-input");
    if (promptInput) promptInput.value = customPrompt;

    const briefingsCheck = document.getElementById("ai-daily-briefings-check");
    if (briefingsCheck) briefingsCheck.checked = (ai.use_ai_daily_briefings !== false);

    const personaChips = document.querySelectorAll(".btn-persona-chip");
    personaChips.forEach(chip => {
      chip.classList.toggle("active", chip.dataset.persona === activePersona);
    });
  } catch (e) {
    console.error("Load TG/AI config error:", e);
  }
}

async function saveTelegramConfig() {
  try {
    const api = getApi();
    const cfg = await api.get_config();
    const curTg = cfg.telegram || {};
    const inputToken = document.getElementById("tg-token-input").value.trim();
    const inputChat = document.getElementById("tg-chat-input").value.trim();
    const inputAi = (document.getElementById("ai-token-input")?.value || "").trim();

    const activeChip = document.querySelector(".btn-persona-chip.active");
    const selectedPersona = activeChip ? activeChip.dataset.persona : "david_goggins";
    const customPrompt = (document.getElementById("ai-custom-prompt-input")?.value || "").trim();
    const useAiBriefings = document.getElementById("ai-daily-briefings-check")?.checked ?? true;

    cfg.telegram = {
      bot_token: inputToken || curTg.bot_token || "",
      chat_id: inputChat || curTg.chat_id || ""
    };
    cfg.ai = {
      api_key: inputAi || (cfg.ai?.api_key || ""),
      provider: (inputAi || cfg.ai?.api_key || "").startsWith("sk-") ? "openai" : "gemini",
      persona: selectedPersona,
      custom_prompt: customPrompt,
      use_ai_daily_briefings: useAiBriefings
    };
    await api.save_config(cfg);
    showToast("AI Coach & Telegram settings saved!");
  } catch (e) {
    alert("Error saving settings: " + e.message);
  }
}

function setupAiPersonaControls() {
  const personaChips = document.querySelectorAll(".btn-persona-chip");
  const promptInput = document.getElementById("ai-custom-prompt-input");

  personaChips.forEach(chip => {
    chip.addEventListener("click", () => {
      personaChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      const defaultPrompt = chip.dataset.prompt || "";
      if (promptInput) {
        promptInput.value = defaultPrompt;
      }
    });
  });
}

// -----------------------------------------------------------------------------
// Weather & Location Configuration
// -----------------------------------------------------------------------------
async function loadWeatherConfig() {
  try {
    const api = getApi();
    const cfg = await api.get_config();
    const weatherCfg = cfg.weather || {};
    const cityInput = document.getElementById("input-weather-city");
    const currentCity = weatherCfg.city || "Hanoi";
    if (cityInput) cityInput.value = currentCity;

    // Highlight active preset chip if matches
    const chips = document.querySelectorAll(".btn-city-chip");
    chips.forEach(chip => {
      chip.classList.toggle("active", chip.dataset.city.toLowerCase() === currentCity.toLowerCase());
    });

    if (api.get_weather) {
      const w = await api.get_weather();
      updateWeatherPreviewUi(w);
    }
  } catch (err) {
    console.error("Load weather config error:", err);
  }
}

function updateWeatherPreviewUi(w) {
  if (!w) return;
  const iconEl = document.getElementById("weather-preview-icon");
  const tempEl = document.getElementById("weather-preview-temp");
  const descEl = document.getElementById("weather-preview-desc");
  if (iconEl) iconEl.innerText = w.icon || "☀️";
  if (tempEl) tempEl.innerText = `${w.temperature !== undefined ? w.temperature : 28}°C`;
  const tmStr = w.tomorrow ? ` | Tomorrow: ${w.tomorrow.icon} ${w.tomorrow.temp_max}°/${w.tomorrow.temp_min}°` : '';
  if (descEl) descEl.innerText = `${w.condition || "Clear Sky"} • ${w.city || "Hanoi"}${tmStr}`;
}

async function saveWeatherLocation(cityName, lat, lon) {
  const saveBtn = document.getElementById("btn-save-weather");
  try {
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerText = "Saving...";
    }
    const api = getApi();
    if (api.set_weather_location) {
      const res = await api.set_weather_location(cityName, lat, lon);
      updateWeatherPreviewUi(res);
      showToast(`Weather location set to "${cityName}"!`);
    }
  } catch (err) {
    alert("Error updating weather location: " + err.message);
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerText = "Save Location";
    }
  }
}

function setupWeatherControls() {
  const saveBtn = document.getElementById("btn-save-weather");
  const refreshBtn = document.getElementById("btn-refresh-weather");
  const cityInput = document.getElementById("input-weather-city");
  const chips = document.querySelectorAll(".btn-city-chip");

  if (saveBtn && cityInput) {
    saveBtn.addEventListener("click", () => {
      const city = cityInput.value.trim();
      if (!city) {
        alert("Please enter a city name!");
        return;
      }
      saveWeatherLocation(city);
    });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", async () => {
      refreshBtn.innerText = "Loading...";
      const api = getApi();
      if (api.get_weather) {
        const w = await api.get_weather(true);
        updateWeatherPreviewUi(w);
        showToast("Weather updated!");
      }
      refreshBtn.innerText = "Refresh";
    });
  }

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      chips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      const city = chip.dataset.city;
      const lat = parseFloat(chip.dataset.lat);
      const lon = parseFloat(chip.dataset.lon);
      if (cityInput) cityInput.value = city;
      saveWeatherLocation(city, lat, lon);
    });
  });
}

// -----------------------------------------------------------------------------
// Form Handling & Setup
// -----------------------------------------------------------------------------
function setupForm() {
  const typeCards = document.querySelectorAll(".type-card");
  const fieldTargetMinutes = document.getElementById("field-target-minutes");


  // Cancel Edit button
  const cancelBtn = document.getElementById("btn-cancel-edit");
  if (cancelBtn) {
    cancelBtn.addEventListener("click", cancelEditMode);
  }

  // Init Form's Embedded Calendar Sheet
  initFormCalendarSheet();

  // Type Selector
  typeCards.forEach(card => {
    card.addEventListener("click", () => {
      typeCards.forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      const radio = card.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
        if (radio.value === "timer") {
          fieldTargetMinutes?.classList.remove("hidden");
        } else {
          fieldTargetMinutes?.classList.add("hidden");
        }
      }
    });
  });

  // Minutes presets
  document.querySelectorAll(".btn-preset").forEach(btn => {
    btn.addEventListener("click", () => {
      const min = btn.dataset.min;
      if (min) {
        document.getElementById("input-minutes").value = min;
      }
    });
  });

  // Telegram Remind Time Presets
  const remindTimeInput = document.getElementById("input-remind-time");
  const timePresets = document.querySelectorAll(".btn-time-preset");

  timePresets.forEach(presetBtn => {
    presetBtn.addEventListener("click", () => {
      const t = presetBtn.dataset.time || "";
      if (remindTimeInput) {
        remindTimeInput.value = t;
      }
      timePresets.forEach(b => b.classList.remove("active"));
      if (t) presetBtn.classList.add("active");
    });
  });

  if (remindTimeInput) {
    remindTimeInput.addEventListener("input", () => {
      timePresets.forEach(b => {
        b.classList.toggle("active", b.dataset.time === remindTimeInput.value && b.dataset.time !== "");
      });
    });
  }

  // Add / Update Protocol Submit
  const addBtn = document.getElementById("btn-add-protocol");
  addBtn.addEventListener("click", async () => {
    const name = document.getElementById("input-name").value.trim();
    if (!name) {
      alert("Please enter a protocol name!");
      document.getElementById("input-name").focus();
      return;
    }

    const repeatDaily = document.getElementById("input-repeat-daily")?.checked || false;
    const todayStr = formatYMD(new Date());

    if (!repeatDaily && (!formSelectedDate || formSelectedDate < todayStr)) {
      alert("Cannot schedule for past dates! Please select today or a future date.");
      return;
    }

    const remindTime = remindTimeInput ? remindTimeInput.value.trim() : "";

    // 2-Hour Buffer Validation for Today
    if (!repeatDaily && formSelectedDate === todayStr) {
      const now = new Date();
      now.setHours(now.getHours() + 2);
      const minHH = String(now.getHours()).padStart(2, '0');
      const minMM = String(now.getMinutes()).padStart(2, '0');
      const minTimeStr = `${minHH}:${minMM}`;

      if (!remindTime || remindTime < minTimeStr) {
        alert(`When scheduling for today (${todayStr}), the reminder/scheduled time must be at least 2 hours in advance (>= ${minTimeStr}). Currently: "${remindTime || 'Not set'}".`);
        remindTimeInput?.focus();
        return;
      }
    }

    // Type
    let selectedType = "todo";
    const checkedRadio = document.querySelector('input[name="protocol-type"]:checked');
    if (checkedRadio) selectedType = checkedRadio.value;

    // Target minutes if timer
    const targetMinutes = selectedType === "timer" 
      ? parseInt(document.getElementById("input-minutes").value, 10) || 60 
      : null;

    // Calculate days or specific dates from form calendar
    let computedDays = [];
    let computedSpecificDates = [];
    let computedScheduleType = "dates";

    if (repeatDaily) {
      computedScheduleType = "weekly";
      computedDays = [0, 1, 2, 3, 4, 5, 6];
      computedSpecificDates = [];
    } else {
      computedScheduleType = "dates";
      computedDays = [];
      computedSpecificDates = [formSelectedDate];
    }

    const timeDesc = document.getElementById("input-time-desc").value.trim();

    const protocolData = {
      name: name,
      icon: "",
      type: selectedType,
      schedule_type: computedScheduleType,
      days: computedDays,
      specific_dates: computedSpecificDates,
      time_desc: timeDesc || (selectedType === "retro" ? "Full 24h evaluation" : ""),
      active: true
    };

    if (remindTime) {
      protocolData.remind_time = remindTime;
    } else {
      protocolData.remind_time = "";
    }

    if (selectedType === "timer") {
      protocolData.target_minutes = targetMinutes;
    }

    try {
      addBtn.disabled = true;
      addBtn.innerText = editingProtocolId ? "Updating..." : "Saving...";
      
      const api = getApi();
      if (editingProtocolId) {
        await api.update_protocol(editingProtocolId, protocolData);
        showToast(`Protocol "${name}" updated successfully!`);
        cancelEditMode();
      } else {
        const cleanId = name.toLowerCase()
          .replace(/[^a-z0-9]/g, "_")
          .slice(0, 15) + "_" + Math.floor(Date.now() / 1000).toString().slice(-4);
        protocolData.id = cleanId;
        await api.add_protocol(protocolData);
        showToast(`Protocol "${name}" saved!`);
        cancelEditMode();
      }

      await loadProtocols();

    } catch (err) {
      alert("Error saving protocol: " + err.message);
    } finally {
      addBtn.disabled = false;
      addBtn.innerHTML = `<span>${editingProtocolId ? 'UPDATE PROTOCOL' : 'SAVE PROTOCOL'}</span>`;
    }
  });

  // Refresh button
  document.getElementById("btn-refresh").addEventListener("click", () => {
    loadProtocols();
    loadTelegramConfig();
    loadWeatherConfig();
    showToast("Protocols & Weather refreshed");
  });

  // Save Telegram & AI
  document.getElementById("btn-save-tg").addEventListener("click", saveTelegramConfig);

  // Setup Weather & AI Persona Controls
  setupWeatherControls();
  setupAiPersonaControls();

  // Test Telegram Ping
  const pingBtn = document.getElementById("btn-tg-ping-mgr");
  if (pingBtn) {
    pingBtn.addEventListener("click", async () => {
      const api = getApi();
      if (api.send_test_telegram) {
        pingBtn.innerText = "Sending...";
        const res = await api.send_test_telegram();
        pingBtn.innerText = "Test Ping";
        if (res && res.success) {
          showToast("Test notification sent successfully!");
        } else {
          alert(`Notification: ${res ? res.message : 'Please enter Bot Token first'}`);
        }
      }
    });
  }

  // Test AI Coach
  const testAiBtn = document.getElementById("btn-test-ai");
  if (testAiBtn) {
    testAiBtn.addEventListener("click", async () => {
      const api = getApi();
      if (api.test_ai_coach) {
        testAiBtn.innerText = "Analyzing...";
        const customPrompt = (document.getElementById("ai-custom-prompt-input")?.value || "").trim();
        // Save settings so active persona and prompt are up to date
        await saveTelegramConfig();
        const res = await api.test_ai_coach(customPrompt);
        testAiBtn.innerText = "Test AI Coach";
        if (res && res.success) {
          showToast("AI Coach active!");
          const cleanText = (res.message || '').replace(/<[^>]+>/g, '');
          alert(`🛡️ AI Coach Response:\n\n"${cleanText}"\n\n(A test message was broadcasted to your Telegram!)`);
        } else {
          alert(`⚠️ AI Coach: ${res ? res.message : 'Please enter a valid Gemini API Key'}`);
        }
      } else {
        alert("AI Coach feature is ready! Save your API key and restart app.");
      }
    });
  }
}

// -----------------------------------------------------------------------------
// Utilities
// -----------------------------------------------------------------------------
function showToast(msg) {
  let toast = document.getElementById("manager-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "manager-toast";
    toast.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      background: rgba(14, 165, 233, 0.95);
      color: #fff;
      padding: 10px 18px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      box-shadow: 0 8px 25px rgba(0,0,0,0.5);
      backdrop-filter: blur(10px);
      z-index: 99999;
      transition: all 0.3s ease;
      opacity: 0;
      transform: translateY(10px);
    `;
    document.body.appendChild(toast);
  }

  toast.innerText = msg;
  toast.style.opacity = "1";
  toast.style.transform = "translateY(0)";

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
  }, 2500);
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}

// -----------------------------------------------------------------------------
// Init
// -----------------------------------------------------------------------------
window.addEventListener("pywebviewready", () => {
  loadProtocols();
  loadTelegramConfig();
  loadWeatherConfig();
});

document.addEventListener("DOMContentLoaded", () => {
  setupForm();
  loadProtocols();
  loadTelegramConfig();
  loadWeatherConfig();
});
