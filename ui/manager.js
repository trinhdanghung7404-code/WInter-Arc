// ==============================================================================
// WINTER ARC PROTOCOL MANAGER - JAVASCRIPT
// Giao tiếp trực tiếp với Backend Python qua window.pywebview.api
// Lưu trữ 100% vào data/protocols.json (KHÔNG HARDCODE)
// ==============================================================================

const fallbackProtocols = [
  { id: "pushups", name: "50 Pushups", icon: "💪", type: "todo", days: [0,1,2,3,4,5,6], time_desc: "Morning warmup", active: true },
  { id: "english", name: "English Study", icon: "🇬🇧", type: "timer", target_minutes: 120, days: [0,1,2,3,4,5,6], time_desc: "Target 120 mins", active: true },
  { id: "project", name: "Capstone Project", icon: "💻", type: "timer", target_minutes: 90, days: [1,3,5], time_desc: "Tue, Thu, Sat evenings", active: true },
  { id: "workout", name: "Workout 20:30 – 21:30", icon: "🏋️", type: "todo", days: [0,2,4,6], time_desc: "Mon, Wed, Fri, Sun evenings", active: true },
  { id: "nonut", name: "Discipline No Nut (Yesterday)", icon: "🚫", type: "retro", days: [0,1,2,3,4,5,6], time_desc: "Full 24h evaluation", active: true },
  { id: "detox_mxh", name: "No Screen Before Bed", icon: "📵", type: "retro", days: [0,1,2,3,4,5,6], time_desc: "Yesterday evening evaluation", active: true }
];

const DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function getApi() {
  if (window.pywebview && window.pywebview.api) {
    return window.pywebview.api;
  }
  return {
    get_protocols: async () => fallbackProtocols,
    add_protocol: async (item) => {
      fallbackProtocols.push(item);
      return fallbackProtocols;
    },
    delete_protocol: async (id) => {
      const idx = fallbackProtocols.findIndex(p => p.id === id);
      if (idx !== -1) fallbackProtocols.splice(idx, 1);
      return fallbackProtocols;
    },
    update_protocol: async (id, fields) => {
      const p = fallbackProtocols.find(x => x.id === id);
      if (p) Object.assign(p, fields);
      return fallbackProtocols;
    },
    get_config: async () => ({ telegram: { bot_token: "", chat_id: "" } }),
    save_config: async (cfg) => true
  };
}

// -----------------------------------------------------------------------------
// Format schedule days helper
// -----------------------------------------------------------------------------
function formatScheduleDays(days) {
  if (!days || days.length === 0) return "Not scheduled";
  if (days.length === 7) return "Everyday (Mon – Sun)";
  if (days.length === 5 && days.every(d => [0, 1, 2, 3, 4].includes(d))) return "Mon – Fri";
  return days.map(d => DAY_NAMES[d] || `D${d + 1}`).join(", ");
}

// -----------------------------------------------------------------------------
// Apple Squircle Badge — 100% Modern SVG Squircle System (No raw emojis)
// -----------------------------------------------------------------------------
function renderManagerBadge(item) {
  const icon = (item.icon || '').trim();
  const id = (item.id || '').toLowerCase();
  const name = (item.name || '').toLowerCase();

  // 1. Blue Lightning Bolt (Sức mạnh / Chống đẩy)
  if (icon === '💪' || icon === '⚡' || id.includes('pushup') || id.includes('chong_day') || name.includes('chống đẩy')) {
    return `<div class="mgr-badge badge-blue" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
      </svg></div>`;
  }

  // 2. Purple Book (Tiếng Anh / Học tập)
  if (icon === '🇬🇧' || icon === '📚' || id.includes('english') || id.includes('tieng_anh') || name.includes('tiếng anh')) {
    return `<div class="mgr-badge badge-purple" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
      </svg></div>`;
  }

  // 3. Green Laptop (Làm Đồ Án / Code / Laptop)
  if (icon === '💻' || icon === '🖥️' || id.includes('project') || id.includes('do_an') || id.includes('code') || name.includes('đồ án')) {
    return `<div class="mgr-badge badge-green" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <rect width="18" height="12" x="3" y="4" rx="2"/>
        <line x1="2" x2="22" y1="20" y2="20"/>
      </svg></div>`;
  }

  // 4. Orange Dumbbell (Gym / Thể thao / Thể dục)
  if (icon.includes('🏋') || id.includes('workout') || id.includes('gym') || id.includes('the_duc') || name.includes('thể dục')) {
    return `<div class="mgr-badge badge-orange" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m6.5 6.5 11 11"/>
        <path d="m21 21-1-1a2 2 0 0 0-2.83 0l-1.17 1.17a2 2 0 0 0 0 2.83l1 1a2 2 0 0 0 2.83 0l1.17-1.17a2 2 0 0 0 0-2.83Z"/>
        <path d="m3 3 1 1a2 2 0 0 0 2.83 0l1.17-1.17a2 2 0 0 0 0-2.83l-1-1a2 2 0 0 0-2.83 0L3 1.17a2 2 0 0 0 0 2.83Z"/>
        <path d="m18 15 1.41-1.41a2 2 0 0 0 0-2.83L13.24 4.59a2 2 0 0 0-2.83 0L9 6"/>
        <path d="m6 9-1.41 1.41a2 2 0 0 0 0 2.83l6.17 6.17a2 2 0 0 0 2.83 0L15 18"/>
      </svg></div>`;
  }

  // 5. Indigo Open Book (Đọc sách)
  if (icon === '📖' || id.includes('read') || id.includes('doc') || name.includes('đọc')) {
    return `<div class="mgr-badge badge-indigo" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 7v14"/>
        <path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>
      </svg></div>`;
  }

  // 6. Cyan Water Droplet (Uống nước)
  if (icon === '💧' || id.includes('water') || id.includes('nuoc') || name.includes('nước')) {
    return `<div class="mgr-badge badge-cyan" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>
      </svg></div>`;
  }

  // 7. Red Flame (Kỷ luật / No Nut)
  if (icon === '🔥' || icon === '🚫' || id.includes('nonut') || id.includes('no_nut') || name.includes('no nut')) {
    return `<div class="mgr-badge badge-red" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor">
        <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>
      </svg></div>`;
  }

  // 8. Slate Phone-Off (Detox MXH)
  if (icon === '📵' || id.includes('detox') || id.includes('phone') || name.includes('điện thoại')) {
    return `<div class="mgr-badge badge-slate" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <rect width="14" height="20" x="5" y="2" rx="2" ry="2"/>
        <path d="m2 2 20 20"/>
        <line x1="12" x2="12.01" y1="18" y2="18"/>
      </svg></div>`;
  }

  // 9. Teal Meditation (Thiền)
  if (icon === '🧘' || id.includes('thien') || id.includes('meditat') || name.includes('thiền')) {
    return `<div class="mgr-badge badge-teal" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="4" r="1"/>
        <path d="M6 8h12l-2 8H8z"/>
        <path d="M6 8 4 18"/>
        <path d="m18 8 2 10"/>
      </svg></div>`;
  }

  // 10. Amber Runner (Chạy bộ / Cardio)
  if (icon === '🏃' || id.includes('run') || id.includes('chay') || name.includes('chạy')) {
    return `<div class="mgr-badge badge-amber" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="13" cy="4" r="1"/>
        <path d="M6 8.8 10 8l2 4 2-3 2 1.8"/>
        <path d="m10 16 1.5-4L14 14l2-2.5"/>
        <path d="m6 20 2-4"/>
        <path d="m18 20-2-5.5"/>
      </svg></div>`;
  }

  // 11. Violet Crescent (Giấc ngủ)
  if (icon === '🌙' || icon === '💤' || id.includes('sleep') || id.includes('ngu') || name.includes('ngủ')) {
    return `<div class="mgr-badge badge-violet" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
      </svg></div>`;
  }

  // 12. Rose Boxing Glove (Boxing / Đấm bốc)
  if (icon === '🥊' || id.includes('box') || id.includes('dam') || name.includes('boxing')) {
    return `<div class="mgr-badge badge-rose" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"/>
        <path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"/>
        <path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"/>
        <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8H8a8 8 0 0 1-8-8v-5a1 1 0 0 1 1-1 2 2 0 0 1 2 2v2.5"/>
      </svg></div>`;
  }

  // 13. Lime Leaf (Ăn uống lành mạnh / Salad)
  if (icon === '🥗' || icon === '🌿' || id.includes('diet') || id.includes('salad') || name.includes('ăn')) {
    return `<div class="mgr-badge badge-lime" title="${escapeHtml(item.name)}">
      <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z"/>
        <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
      </svg></div>`;
  }

  // Default Fallback: Clean Target SVG (No raw emojis)
  return `<div class="mgr-badge badge-target" title="${escapeHtml(item.name || 'Protocol')}">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2">
      <circle cx="12" cy="12" r="10"/>
      <circle cx="12" cy="12" r="6"/>
      <circle cx="12" cy="12" r="2"/>
    </svg></div>`;
}


// -----------------------------------------------------------------------------
// Load & Render Protocols List
// -----------------------------------------------------------------------------
async function loadProtocols() {
  const container = document.getElementById("protocols-list-container");
  const badge = document.getElementById("active-count-badge");
  
  try {
    const api = getApi();
    const protocols = await api.get_protocols();
    
    if (!protocols || protocols.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 30px; color: var(--text-muted); font-size: 0.8rem;">
          No active protocols yet. Add your first protocol on the right!
        </div>
      `;
      badge.innerText = "0 items";
      return;
    }

    badge.innerText = `${protocols.length} item${protocols.length > 1 ? 's' : ''}`;
    container.innerHTML = "";

    protocols.forEach((item) => {
      const card = document.createElement("div");
      card.className = `protocol-item-card ${item.active === false ? 'inactive' : ''}`;
      
      let typeLabel = "To-Do";
      let typeClass = "todo";

      if (item.type === "timer") {
        typeLabel = `Timer ${item.target_minutes || 60}m`;
        typeClass = "timer";
      } else if (item.type === "retro") {
        typeLabel = "Yesterday Retro";
        typeClass = "retro";
      }

      const scheduleStr = formatScheduleDays(item.days);
      const remindTag = item.remind_time 
        ? `<span class="item-remind-tag" title="Telegram reminder at ${escapeHtml(item.remind_time)}">
            <svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -1px; margin-right: 2px;">
              <circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>
            </svg>${escapeHtml(item.remind_time)}</span>` 
        : '';

      card.innerHTML = `
        <div class="item-left">
          ${renderManagerBadge(item)}
          <div class="item-info">
            <div class="item-name">${escapeHtml(item.name)}</div>
            <div class="item-tags">
              <span class="tag-badge ${typeClass}">${typeLabel}</span>
              ${remindTag}
              <span class="item-schedule">${scheduleStr}${item.time_desc ? ' • ' + escapeHtml(item.time_desc) : ''}</span>
            </div>
          </div>
        </div>
        <div class="item-actions">
          <button class="btn-del" title="Delete protocol" data-id="${item.id}">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      `;

      // Handle delete
      const delBtn = card.querySelector(".btn-del");
      delBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        if (confirm(`Are you sure you want to delete protocol: "${item.name}"?`)) {
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
// Load Telegram & AI Config
// -----------------------------------------------------------------------------
async function loadTelegramConfig() {
  try {
    const api = getApi();
    const cfg = await api.get_config();
    const tg = cfg.telegram || {};
    const ai = cfg.ai || {};
    document.getElementById("tg-token-input").value = tg.bot_token || "";
    document.getElementById("tg-chat-input").value = tg.chat_id || "";
    const aiInput = document.getElementById("ai-token-input");
    if (aiInput) aiInput.value = ai.api_key || "";
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

    cfg.telegram = {
      bot_token: inputToken || curTg.bot_token || "",
      chat_id: inputChat || curTg.chat_id || ""
    };
    cfg.ai = {
      api_key: inputAi || (cfg.ai?.api_key || ""),
      provider: (inputAi || cfg.ai?.api_key || "").startsWith("sk-") ? "openai" : "gemini"
    };
    await api.save_config(cfg);
    showToast("Settings saved successfully!");
  } catch (e) {
    alert("Error saving settings: " + e.message);
  }
}

// -----------------------------------------------------------------------------
// Form Handling & Type Switching
// -----------------------------------------------------------------------------
function setupForm() {
  const typeCards = document.querySelectorAll(".type-card");
  const fieldTargetMinutes = document.getElementById("field-target-minutes");
  const iconInput = document.getElementById("input-icon");

  // Type Selector
  typeCards.forEach(card => {
    card.addEventListener("click", () => {
      typeCards.forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      const radio = card.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
        if (radio.value === "timer") {
          fieldTargetMinutes.classList.remove("hidden");
        } else {
          fieldTargetMinutes.classList.add("hidden");
        }
      }
    });
  });

  // Quick Icon Picker — SVG Squircle System (reads data-emoji attr)
  const emojiOpts = document.querySelectorAll(".emoji-opt");
  emojiOpts.forEach(opt => {
    opt.addEventListener("click", () => {
      const val = opt.dataset.emoji || opt.innerText.trim();
      iconInput.value = val;
      // Visual highlight: mark selected
      emojiOpts.forEach(o => o.classList.remove("selected"));
      opt.classList.add("selected");
    });
  });
  // Auto-select first icon on load
  if (emojiOpts.length > 0) emojiOpts[0].classList.add("selected");

  // Minutes presets
  document.querySelectorAll(".btn-preset").forEach(btn => {
    btn.addEventListener("click", () => {
      const min = btn.dataset.min;
      if (min) {
        document.getElementById("input-minutes").value = min;
      }
    });
  });

  // Schedule Presets
  const schedulePresets = document.querySelectorAll(".btn-schedule-preset");
  const dayChecks = document.querySelectorAll(".day-check");

  schedulePresets.forEach(presetBtn => {
    presetBtn.addEventListener("click", () => {
      schedulePresets.forEach(p => p.classList.remove("active"));
      presetBtn.classList.add("active");

      const preset = presetBtn.dataset.preset;
      let activeDays = [0, 1, 2, 3, 4, 5, 6];

      if (preset === "all") {
        activeDays = [0, 1, 2, 3, 4, 5, 6];
      } else if (preset === "t357") {
        activeDays = [1, 3, 5]; // T3, T5, T7
      } else if (preset === "t246cn") {
        activeDays = [0, 2, 4, 6]; // T2, T4, T6, CN
      } else if (preset === "weekdays") {
        activeDays = [0, 1, 2, 3, 4]; // T2 - T6
      }

      dayChecks.forEach(ch => {
        const val = parseInt(ch.value, 10);
        ch.checked = activeDays.includes(val);
      });
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

  // Add Protocol Submit
  const addBtn = document.getElementById("btn-add-protocol");
  addBtn.addEventListener("click", async () => {
    const name = document.getElementById("input-name").value.trim();
    if (!name) {
      alert("Please enter a protocol name!");
      document.getElementById("input-name").focus();
      return;
    }

    const icon = document.getElementById("input-icon").value.trim() || "🎯";
    
    // Type
    let selectedType = "todo";
    const checkedRadio = document.querySelector('input[name="protocol-type"]:checked');
    if (checkedRadio) selectedType = checkedRadio.value;

    // Target minutes if timer
    const targetMinutes = selectedType === "timer" 
      ? parseInt(document.getElementById("input-minutes").value, 10) || 60 
      : null;

    // Days
    const selectedDays = [];
    document.querySelectorAll(".day-check:checked").forEach(ch => {
      selectedDays.push(parseInt(ch.value, 10));
    });

    if (selectedDays.length === 0) {
      alert("Please select at least 1 day of the week!");
      return;
    }

    const timeDesc = document.getElementById("input-time-desc").value.trim();
    const remindTime = remindTimeInput ? remindTimeInput.value.trim() : "";

    // Generate unique ID based on name and timestamp
    const cleanId = name.toLowerCase()
      .replace(/[^a-z0-9]/g, "_")
      .slice(0, 15) + "_" + Math.floor(Date.now() / 1000).toString().slice(-4);

    const newProtocol = {
      id: cleanId,
      name: name,
      icon: icon,
      type: selectedType,
      days: selectedDays,
      time_desc: timeDesc || (selectedType === "retro" ? "Full 24h evaluation" : "Daily"),
      active: true
    };

    if (remindTime) {
      newProtocol.remind_time = remindTime;
    }

    if (selectedType === "timer") {
      newProtocol.target_minutes = targetMinutes;
    }

    try {
      addBtn.disabled = true;
      addBtn.innerText = "Saving...";
      
      const api = getApi();
      await api.add_protocol(newProtocol);

      showToast(`Protocol "${name}" saved!`);

      // Reset form
      document.getElementById("input-name").value = "";
      document.getElementById("input-time-desc").value = "";
      if (remindTimeInput) remindTimeInput.value = "";
      timePresets.forEach(b => b.classList.remove("active"));

      // Reset icon picker: select first badge
      const allOpts = document.querySelectorAll(".emoji-opt");
      allOpts.forEach(o => o.classList.remove("selected"));
      if (allOpts.length > 0) {
        allOpts[0].classList.add("selected");
        document.getElementById("input-icon").value = allOpts[0].dataset.emoji || "💪";
      }

      await loadProtocols();

    } catch (err) {
      alert("Error adding protocol: " + err.message);
    } finally {
      addBtn.disabled = false;
      addBtn.innerHTML = `<span>SAVE PROTOCOL</span>`;
    }
  });

  // Refresh button
  document.getElementById("btn-refresh").addEventListener("click", () => {
    loadProtocols();
    loadTelegramConfig();
    showToast("Protocols refreshed");
  });

  // Save Telegram
  document.getElementById("btn-save-tg").addEventListener("click", saveTelegramConfig);

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
        const res = await api.test_ai_coach();
        testAiBtn.innerText = "Test AI Coach";
        if (res && res.success) {
          showToast("AI Coach active!");
          alert(`🛡️ AI Coach Test Quote:\n\n"${res.message}"\n\n(A test message was broadcasted to your Telegram!)`);
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
document.addEventListener("DOMContentLoaded", () => {
  setupForm();
  loadProtocols();
  loadTelegramConfig();
});
