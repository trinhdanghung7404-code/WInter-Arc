# ❄️ Winter Arc Command Center (WACC)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D6.svg)](https://www.microsoft.com/windows/)
[![UI](https://img.shields.io/badge/UI-Apple%20Glassmorphism%20Squircle-000000.svg)](ui/)
[![Telegram](https://img.shields.io/badge/Telegram-2--Way%20Bot%20Sync-2CA5E0.svg)](https://telegram.org/)
[![AI Coach](https://img.shields.io/badge/AI%20Coach-Gemini%20%2F%20GPT--4o-8E75B2.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **The ultimate 90-Day Discipline Command Center** — Inspired by Apple's Glassmorphism UI & the Winter Arc Challenge.
> Features a sleek desktop floating widget, dynamic protocol management, real-time weather & clock, AI Discipline Coach (David Goggins / Stoic persona), and seamless 2-way Telegram synchronization with interactive check-in buttons.

---

## 🌟 Key Features

### 🖥️ 1. Apple-Grade Glassmorphism Desktop Widget
* **Digital Timer-Style Clock & Weather Bar**: Live digital clock (`HH:MM.SS`), current temperature, city tag, and forecast toggle powered by Open-Meteo API (100% free, 0 API key required).
* **Activity Progress Rings**: Dynamic SVG rings tracking your core daily pillars.
* **Apple Squircle Protocol Checklist**: Clean checklist with custom category icon badges (Pushups, Reading, English, Coding, Gym, Meditation, No Nut, Screen Detox, etc.).
* **Integrated Focus Pomodoro Timer**: Auto-detects timed tasks (English, Deep Work) and automatically minimizes when not needed.
* **Compact / Always-on-Top Mode**: Pin widget to your desktop with native Win32 smooth drag (`WM_NCLBUTTONDOWN`) with zero lag.

### ⚙️ 2. Dynamic Protocol Manager
* **Zero Hardcoding**: Add, edit, or remove any protocol with custom schedules (Daily, specific days of week, or calendar dates).
* **3 Protocol Architectures**:
  * `✅ To-Do`: Daily habits completed anytime (e.g., 50 Pushups, Gym, Reading).
  * `⏱️ Focus Timer`: Timed sessions with custom target minutes (e.g., 60m English, 120m Coding).
  * `🌅 Yesterday Retro`: 24h evaluation habits evaluated the morning after (e.g., No Nut, Screen Detox, Sleep before 23:30).
* **Anti-Cheating & History Preservation**:
  * **Future Dates Locked**: Future days are strictly read-only (`completed: false`, uncheckable).
  * **2-Hour Advance Buffer**: Today's scheduled reminders require setting at least 2 hours in advance.
  * **Safe Soft Delete**: Deleting a protocol removes it from today and future dates while **preserving 100% of past historical completion records**.

### 📱 3. 2-Way Telegram Bot Sync & AI Coach
* **Interactive Check-in Buttons**: Bot sends reminders and reports with inline buttons (`⬜` / `✅`). Tapping a button instantly marks the task completed and syncs with your desktop widget!
* **Natural Language Telegram Commands**:
  * `/time 7:30 am Sunday Buy books` $\rightarrow$ Schedules protocol for Sunday 07:30.
  * `/remind 07:30 50 Push up` $\rightarrow$ Sets a 07:30 reminder.
  * `/note Buy vitamins and milk` $\rightarrow$ Saves memo directly to today's notes.
  * `/notes` $\rightarrow$ View today's saved memos.
  * `/today` $\rightarrow$ Open today's interactive check-in buttons.
  * `/status` $\rightarrow$ View level, streaks, and progress report.
  * `/weekly` & `/monthly` $\rightarrow$ AI-generated performance breakdown.
* **AI Discipline Coach**: Powered by Google Gemini / OpenAI with customizable personas (*David Goggins, Stoic Philosopher, Drill Sergeant, Supportive Brother, or Custom Persona*).

---

## 🚀 Quick Start & Installation

### Prerequisites
* Windows 10 or 11 (64-bit recommended)
* Python 3.10 or higher ([Download Python](https://www.python.org/downloads/))

### Step 1: Clone the Repository
```bash
git clone https://github.com/trinhdanghung7404-code/WInter-Arc.git
cd "Winter Arc"
```

### Step 2: Create Virtual Environment & Install Dependencies
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Settings (Optional but Recommended)
Copy the example config:
```bash
copy data\config.example.json data\config.json
```
Edit `data/config.json` (or configure easily via the in-app **Protocol Manager** UI):
```json
{
  "user_name": "Winter Arc Warrior",
  "start_date": "2026-10-01",
  "telegram": {
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "chat_id": "YOUR_TELEGRAM_CHAT_ID"
  },
  "ai": {
    "api_key": "YOUR_GEMINI_OR_OPENAI_KEY",
    "provider": "gemini",
    "persona": "david_goggins"
  },
  "weather": {
    "city": "Hanoi",
    "latitude": 21.0245,
    "longitude": 105.8412
  }
}
```

### Step 4: Launch Winter Arc
Double-click `start.bat` or run:
```bash
start.bat
```
*To run completely in the background without any console window, double-click **`start_silent.vbs`**.*

---

## 📱 Telegram Bot Setup Guide

1. Open Telegram, search for **`@BotFather`**, and send `/newbot`.
2. Follow instructions to name your bot and obtain your **Bot Token** (e.g. `123456789:ABCDefGh...`).
3. Open **Protocol Manager** (`manager.bat` or click `⚙️` on the widget):
   * Paste your **Bot Token** in the *Telegram & AI Coach* section.
   * Click **Save AI & Telegram**.
4. Open your bot on Telegram and send **`/start`**.
5. You're connected! The bot will now sync checklists, send daily briefings at 07:00, evening progress reports, and remind you of scheduled protocols.

---

## ⌨️ Telegram Commands Cheat Sheet

| Command | Description | Example |
| :--- | :--- | :--- |
| `/today` | Show today's interactive check-in buttons | `/today` |
| `/time <args>` | Schedule a protocol with date & time | `/time 7:30 am Sunday Read book` |
| `/remind <args>` | Set a quick reminder | `/remind 07:30 50 Push up` |
| `/note <text>` | Save a memo for today | `/note Drink 2L water` |
| `/notes` | View all saved memos for today | `/notes` |
| `/del <name>` | Delete a protocol from future schedule | `/del Push up` |
| `/status` | View level, streaks, and completion rate | `/status` |
| `/weekly` | AI 7-day performance evaluation | `/weekly` |
| `/monthly` | AI 30-day phase milestone review | `/monthly` |
| `/help` | Display command guide and examples | `/help` |

---

## 📁 Project Structure

```
Winter-Arc/
├── main.py                   # Desktop Widget window runner & Win32 API bridge
├── manager_app.py            # Protocol Manager desktop app runner
├── server.py                 # Optional Flask Cloud Webhook / Server (Render deployable)
├── start.bat                 # 1-Click launcher with auto-environment detection
├── start_silent.vbs          # Silent background launcher (zero console window)
├── stop.bat                  # 1-Click graceful background process killer
├── manager.bat               # 1-Click Protocol Manager launcher
├── set_wallpaper.py          # 4K Winter Arc wallpaper setter
├── requirements.txt          # Python dependency specifications
├── Procfile                  # Cloud deployment configuration
├── app_icon.ico              # Titanium Apple-style application icon
├── winter_arc_wallpaper.jpg  # 4K Aurora Mountain wallpaper asset
│
├── src/                      # Backend Logic & Core Services
│   ├── app_logic.py          # Protocols, streaks, calendar, & Open-Meteo weather logic
│   ├── bot_service.py        # Telegram Bot polling, commands, & inline buttons
│   ├── ai_service.py         # AI Discipline Coach (Gemini / OpenAI personas)
│   ├── scheduler_service.py  # Background reminder and daily cron scheduler
│   └── cloud_sync.py         # 2-way cloud synchronization helper
│
├── ui/                       # Frontend Glassmorphism UI
│   ├── index.html            # Desktop Widget interface
│   ├── style.css             # Apple Glassmorphism & Squircle design system
│   ├── script.js             # Widget interactivity, live clock, & weather display
│   ├── manager.html          # Protocol Manager settings & scheduler UI
│   └── manager.js            # Manager state handler, icon presets, & validation
│
└── data/                     # Local Storage Data
    ├── config.example.json   # Template configuration file
    ├── protocols.json        # User protocols definition
    └── storage.json          # Daily task records, focus minutes, and streaks
```

---

## 🛡️ Security & Privacy

* **100% Local Execution**: All daily records, protocols, notes, and streak calculations are stored locally in `data/` on your computer.
* **No Telemetry / Data Sharing**: Your personal notes, goals, and API keys remain strictly on your machine.
* **Zero Secrets in Git**: `data/config.json` containing your personal tokens is ignored by git (`.gitignore`). Always use `config.example.json` when distributing.

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use, modify, and customize for your own Winter Arc journey!

**Stay hard. Execute every protocol. Conquer your Winter Arc.** ❄️🔥
