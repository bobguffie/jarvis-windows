<div align="center">

# 🤖 J.A.R.V.I.S — Linux AI Assistant

**Version 2.0 (GPU & Workspace Edition)**

<p><strong>A voice-enabled Linux desktop assistant powered by Gemini Live API or local LM Studio</strong></p>

<p align="center">
  <img src="Icon/jarvis.png" alt="JARVIS Logo" width="120"/>
</p>

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=white)
![Gemini](https://img.shields.io/badge/Powered%20by-Gemini%202.5%20Flash-orange?style=for-the-badge&logo=google&logoColor=white)
![TTS](https://img.shields.io/badge/TTS-Piper%20Voice-00cc66?style=for-the-badge&logo=voice&logoColor=white)
![GPU](https://img.shields.io/badge/GPU-CUDA%20Accelerated-76B900?style=for-the-badge&logo=nvidia&logoColor=white)
![Version](https://img.shields.io/badge/Version-2.0-ff6600?style=for-the-badge)

</div>

---

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [Features](#-features)
- [Linux Port Overview](#-linux-port-overview)
- [What's New in This Fork](#-whats-new-in-this-fork)
- [Architecture](#-architecture)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Supported Commands](#-supported-commands)
- [Local Mode (LM Studio)](#-local-mode-lm-studio)
- [Project Structure](#-project-structure)
- [Security](#-security)
- [Contributing](#-contributing)

---

## 🎯 About the Project

JARVIS is a real-time voice AI assistant developed for the **Linux desktop environment**. It is built on the Google Gemini 2.5 Flash Live API and can operate in both **cloud (Gemini)** and **fully offline local (LM Studio)** modes.

It communicates with the user via voice, processes voice commands in real time, and executes real actions on Linux through 16+ integrated tools — including Bash shell integration, Piper TTS voice output, application launching via `xdg-open`, screen capture with `scrot`, and media control via `playerctl`.

> **Project lineage:** [bnsware/jarvis-windows](https://github.com/bnsware/jarvis-windows) (Turkish original) → [bobguffie/jarvis-windows-english](https://github.com/bobguffie/jarvis-windows-english) (English translation) → **jarvis-linux-english** (Linux port)

---

## ✨ Features

### Voice and Speech
- 🎙️ **Real-time audio streaming** — 16 kHz input via PyAudio
- 🔊 **Natural voice responses** — Gemini Native Audio or local **Piper TTS** (ultra-fast, offline, natural voices ~15MB)
- ✍️ **Text mode** — Written command support alongside voice
- 🧠 **Real-time STT** — Cloud (Gemini) or local (**Faster-Whisper** tiny model — < 150MB RAM)
- 🔇 **Pause / Resume** — Instant pause without dropping the session

### System Integration
- 🖥️ **Application management** — Open any Linux application by voice (mapped to `xdg-open` or desktop binaries)
- 📊 **System info** — CPU, RAM, disk, battery, network (via `psutil` + `nmcli`)
- 💻 **Bash shell** — Run terminal commands via voice with built-in safety filtering
- 👁️ **Screen analysis** — Capture and analyze the desktop with AI (X11 via `scrot` + Gemini/LM Studio Vision)

### Productivity
- 📅 **Calendar** — Local JSON calendar; read, add, and delete events
- ⏰ **Reminders** — Local JSON storage; create and list reminders
- 🧠 **Persistent memory** — Save and delete user-specific information in JSON

### Communication and Media
- 💬 **WhatsApp** — Compose and auto-send messages via WhatsApp Web
- 🌦️ **Weather** — Real-time weather summary (OpenWeatherMap)
- 🎵 **Media playback** — Native media controls via `playerctl` (play/pause/next/previous/volume), YouTube, Spotify, and Apple Music Web
- 🌐 **Browser control** — Open URLs, Google search, play YouTube videos
- 📈 **YouTube Analytics** — Channel statistics and video performance reports

### Dual Backend Support
- ☁️ **Gemini mode** — Google Gemini 2.5 Flash Live API (cloud, real-time streaming)
- 🏠 **Local mode** — Fully offline operation with LM Studio (OpenAI-compatible); Faster-Whisper or Google STT

---

## 🐧 Linux Port Overview

This repository is a complete port of the original Windows JARVIS to Linux. Every Windows-specific module was replaced with a Linux-native equivalent:

| Windows Component | Linux Replacement |
|---|---|
| `pywin32` (Windows API) | Removed — pure Python |
| `pyttsx3` / SAPI TTS | **Piper TTS** — subprocess + `aplay` |
| PowerShell (`shell.py`) | **Bash** (`/bin/bash`) with safety filtering |
| `.exe` app launching | `xdg-open` + app-name mapping dictionary |
| `win32com` Outlook integration | Stripped — local JSON fallback only |
| `WinMM` audio (`playsound`) | **playsound** (cross-platform) |
| Windows screen capture | **scrot** (X11) / grim+slurp (Wayland) |
| `selenium` WhatsApp automation | **WhatsApp Web** via `xdg-open` |
| `setup.bat` / `start.bat` | **setup.sh** / **start.sh** |
| `os.startfile()` | `subprocess.Popen(["/usr/bin/xdg-open", path])` |
| Media keys (WinMM) | **playerctl** (MPRIS-compatible players) |

---

## ✨ What's New in This Fork

### 🇬🇧 Full UK English Translation
The entire user interface has been translated from Turkish to UK English — all labels, status messages, tooltips, and settings text are now in clear English.

### 🎨 Custom UI Colour Picker
You can now change the primary accent colour of the interface directly from the settings panel:
- Click the **"Primary Colour"** button in the Settings panel
- Pick any colour from the system colour picker
- The UI instantly updates — rings, text, buttons, and accents all reflect your chosen colour
- Your preference is saved and restored the next time you launch JARVIS

### 🐧 Full Linux Port
All Windows-specific modules have been replaced with Linux-native alternatives (see table above). The assistant feels identical — same UI, same voice interaction, same capabilities — but runs entirely on Linux.

### 🖥️ Other Improvements
- All action modules (weather, browser, media, etc.) have been reviewed for English consistency
- Cleaned up Turkish comments and variable names throughout the codebase
- Added `translate_ui.py` helper script for future translation maintenance

---

## 🚀 Version 2.0 Features

This branch introduces major new capabilities over the original v1 Linux port:

### 🎮 NVIDIA GPU Acceleration
- Built-in local neural voice synthesis using **Piper TTS** powered by **CUDA cores** on NVIDIA GPUs
- Automatic hardware detection: runs `nvidia-smi` on startup — if an NVIDIA GPU is found and Piper has CUDA support, `--use-cuda` is appended to the inference flags
- **Seamless CPU fallback**: if no GPU is detected or CUDA libraries are unavailable, the engine falls back to standard CPU execution with zero configuration changes
- Sentence splitting with per-sentence WAV rendering via `--output_file`, eliminating audio crackles caused by raw PCM streaming conflicts between STT and TTS

### 📊 Dynamic Workspace Card
- **Live Contextual Media Tracker**: automatically detects and displays currently playing media from any MPRIS-compatible player (VLC, Spotify, Chrome, Brave, etc.) using `playerctl` system bus scanning — no window focus required
- **Shared To-Do List** with smart path detection: defaults to `memory/todo.txt` (local, inside the repo) — works instantly on any machine. If a network-mounted share is detected at `/media/medion/Jarvis-shared/todo.txt`, it uses that instead for multi-machine access
- **Smart Auto-Switching**: when the workspace is in "media" mode and all media players remain idle/stopped for 10+ seconds, the card automatically reverts to the to-do list view
- **Active Playback Priority**: if any player is "Playing" or "Paused", the idle timer resets — no unwanted tab switching while you're paused mid-video
- **Custom path**: to point the to-do list at your own network share, open `actions/workspace.py` and change the `_NETWORK_TODO` variable at the top of the file

### 🌤️ Hyper-Local Weather
- Switched to the **Open-Meteo API** using high-resolution Met Office models for Grantham, UK
- Support for current conditions, tomorrow's forecast, and **10-day weather outlook**
- Each sentence is split into separate bullet points for clean card rendering

### 🎤 New Voice Commands

```
"Switch workspace to media player"    → Shows now-playing media tracker
"Switch workspace to checklist"      → Shows shared network to-do list
"Refresh workspace"                   → Force-refreshes workspace card data immediately
"Give me the 10-day weather outlook"  → Extended weather forecast
"What's playing?"                     → Shows currently playing media on the workspace card
"Show my to-do list"                  → Switches workspace to checklist view
```

---

## 🏗️ Architecture

```
jarvis/
├── main.py                  ← Gemini Live session manager (JarvisLive)
├── ui.py                    ← Tkinter-based desktop UI (JarvisUI)
├── app_config.py            ← Configuration read/write
├── setup.sh                 ← Linux setup script
├── start.sh                 ← Linux launch script
├── core/
│   ├── lmstudio_runtime.py  ← Local mode engine (JarvisLocal)
│   └── prompt.txt           ← AI system prompt
├── actions/                 ← Tool modules (Linux-native)
│   └── ...
├── memory/                  ← Persistent memory (JSON)
├── config/                  ← API keys (gitignored)
├── piper/                   ← Piper TTS binary + voice model (gitignored)
└── SFX/                     ← Sound effects
```

### Data Flow — Gemini Mode

```
Microphone → PyAudio → Gemini Live API
                             ↓
                      Tool Call Detection
                             ↓
                      actions/* modules (Linux)
                             ↓
                      Result → Gemini → Audio Output → Speaker
                                                   ↓
                                            Piper TTS (fallback)
```

### Data Flow — Local Mode

```
Microphone → Faster-Whisper/Google STT → Text
                                              ↓
                                       LM Studio API
                                              ↓
                                      Tool Call Detection
                                              ↓
                                      actions/* modules (Linux)
                                              ↓
                                      Text → Piper TTS → Speaker
```

---

## 📦 Requirements

| Requirement | Details |
|-------------|---------|
| **Python** | 3.10 or higher |
| **Operating System** | Linux (Ubuntu / Debian / Fedora / Arch / etc.) |
| **Display Server** | X11 supported natively; Wayland with limited screen capture |
| **Audio** | ALSA-compatible sound card (built-in on most systems) |
| **Gemini API Key** | Free from [Google AI Studio](https://aistudio.google.com/apikey) |
| **Microphone** | Any USB or built-in microphone |
| **YouTube API** | Optional — for channel statistics |
| **LM Studio** | Optional — for local offline mode |
| **`playerctl`** | Optional — for media playback control |

### Python Dependencies

```
google-genai
SpeechRecognition
pyaudio
psutil
Pillow
requests
pyautogui
faster-whisper
playsound
openai
```

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/bobguffie/jarvis-linux-english.git
cd jarvis-linux-english
```

### 2. Automatic Setup (Recommended)

```bash
chmod +x setup.sh
./setup.sh
```

This script performs the following steps in order:
- Installs Linux system dependencies (`python3-pip`, `python3-venv`, `portaudio19-dev`, `scrot`, `alsa-utils`, `playerctl`)
- Creates a `venv` virtual environment
- Installs packages from `requirements.txt`
- Creates `config/api_keys.json` from the template

### 3. Manual Setup

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt update && sudo apt install -y python3-pip python3-venv portaudio19-dev scrot alsa-utils playerctl

# On Fedora:
# sudo dnf install python3-pip python3-virtualenv portaudio-devel scrot alsa-utils playerctl

# On Arch:
# sudo pacman -S python-pip python-virtualenv portaudio scrot alsa-utils playerctl

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp config/api_keys.example.json config/api_keys.json
```

---

## ⚙️ Configuration

Edit the `config/api_keys.json` file:

```json
{
  "gemini_api_key": "AIza...",
  "voice": "Charon",
  "youtube_api_key": "",
  "youtube_channel_handle": "@yourchannel",
  "backend": "gemini",
  "lmstudio_base_url": "http://127.0.0.1:1234/v1",
  "lmstudio_model": "local-model",
  "lmstudio_api_key": "lm-studio",
  "stt_engine": "whisper",
  "stt_language": "en-US"
}
```

| Field | Description | Required |
|-------|-------------|----------|
| `gemini_api_key` | Google Gemini API key | Yes in Gemini mode |
| `voice` | Voice tone: `Charon`, `Aoede`, `Fenrir`, `Kore`, `Puck` | No |
| `youtube_api_key` | YouTube Data API v3 key | For channel reports |
| `youtube_channel_handle` | Handle in `@yourchannel` format | For channel reports |
| `backend` | `gemini` or `lmstudio` | No (default: gemini) |
| `lmstudio_base_url` | LM Studio server address | Yes in local mode |
| `lmstudio_model` | Local model name to use | Yes in local mode |
| `stt_engine` | `whisper` or `google` | In local mode |
| `stt_language` | STT language code | In local mode |

---

## 🎮 Usage

### Quick Launch

```bash
./start.sh
```

### Manual Launch

```bash
source venv/bin/activate
python3 main.py
```

### Desktop Launcher

A `.desktop` file is included (`JARVIS.desktop`). To install it system-wide:

```bash
mkdir -p ~/.local/share/applications
cp JARVIS.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

Then JARVIS will appear in your application menu.

### Interface

When JARVIS opens, a modern desktop window appears:

- **Status indicator** — `LISTENING`, `THINKING`, `SPEAKING`, `ERROR`
- **Log panel** — Real-time conversation stream
- **Text box** — Enter written commands alongside voice
- **Pause button** — Silences the assistant without dropping the session
- **Side panel** — CPU, RAM, battery, weather, health, and calendar widgets

---

## 🗣️ Supported Commands

### System and Applications

```
"Open VS Code"
"Launch Spotify"
"Open terminal"
"What's the battery status?"
"How much RAM is being used?"
"What time is it?"
"List files in this directory"
```

### Calendar

```
"What's on my calendar today?"
"What's my schedule tomorrow?"
"What's my next meeting?"
"What's on my calendar for the next 30 days?"
"Add a dentist appointment tomorrow at 2 PM"
"Add a meeting Monday from 10:00 to 11:00"
"Delete the meeting from my calendar"
```

### Reminders

```
"What are my reminders for today?"
"Show my upcoming reminders"
"Remind me about the dentist tomorrow morning at 9"
"Remind me to buy milk this evening"
```

### Weather and Browser

```
"What's the weather in New York?"
"Search Google for learn Python"
"Open The Weeknd Blinding Lights on YouTube"
"Open github.com"
```

### Media

```
"Play The Weeknd Blinding Lights on Spotify"
"Pause the music"
"Next track"
"Open Adele Hello on Apple Music"
"Play lofi beats on YouTube"
```

### WhatsApp

```
"Send a goodnight message to Mom on WhatsApp"
"Prepare a WhatsApp message to John: let's meet tomorrow"
```

### Screen Analysis

```
"What's on the screen?"
"Read this error"
"Analyze this window"
"What does it say here?"
```

### YouTube Analytics

```
"How are my YouTube stats?"
"Analyze my recent videos"
"Summarize my channel growth"
```

### Memory

```
"My name is Alex"
"My project is a Python application"
"Remove the Claude limit note from your memory"
"Forget this"
```

### Health Tracking

```
"Log 500ml of water"
"I walked 3000 steps today"
"Log 8 hours of sleep"
"My weight is 72.5 kg"
"Add medication Aspirin 100mg daily"
"What's my health summary?"
```

---

## 🏠 Local Mode (LM Studio)

To run entirely locally without an internet connection:

**1. Download LM Studio and load a model:**
Download from [lmstudio.ai](https://lmstudio.ai), select a model, and start the server.

**2. Update `config/api_keys.json`:**
```json
{
  "backend": "lmstudio",
  "lmstudio_base_url": "http://127.0.0.1:1234/v1",
  "lmstudio_model": "lmstudio-community/mistral-7b-instruct",
  "stt_engine": "whisper"
}
```

**3. For screen analysis, add a vision model:**
```json
{
  "lmstudio_vision_model": "xtuner/llava-llama-3-8b-v1_1-gguf"
}
```

**What changes in local mode:**
- Audio input → Faster-Whisper (local) or Google STT
- Audio output → Piper TTS (local, natural, offline)
- AI engine → LM Studio OpenAI-compatible API
- All tools work the same way

---

## 📁 Project Structure

```
jarvis/
├── main.py                  ← Entry point and Gemini Live engine
├── ui.py                    ← Desktop UI (Tkinter)
├── app_config.py            ← Configuration manager
├── requirements.txt         ← Python dependencies
├── setup.sh                 ← Linux setup script (replaces setup.bat)
├── start.sh                 ← Linux launch script (replaces start.bat)
├── JARVIS.desktop           ← Desktop launcher for application menu
├── pyrightconfig.json       ← Type checking configuration
├── .gitignore
├── Fonts/                   ← UI fonts (Grift family)
├── Icon/                    ← Application icon
│   ├── jarvis.png           ← Main logo
│   ├── jarvis.jpeg          ← Banner image
│   ├── youtube.png
│   ├── youtube-logo.png
│   ├── instagram.png
│   └── instagram-logo.png
├── SFX/                     ← Sound effects (Done, Error, HUD, Start, Think)
├── core/
│   ├── lmstudio_runtime.py  ← Local AI engine (Linux-adapted)
│   └── prompt.txt           ← System prompt
├── actions/
│   ├── __init__.py
│   ├── browser.py           ← Web browser control
│   ├── calendar.py          ← Calendar operations (local JSON, Outlook removed)
│   ├── health.py            ← Health tracking (water, steps, sleep, weight, meds)
│   ├── media.py             ← Music/video playback + playerctl integration
│   ├── open_app.py          ← Linux application launcher (xdg-open)
│   ├── reminders.py         ← Reminder operations (local JSON, Outlook removed)
│   ├── screen_vision.py     ← Screenshot + Vision AI (scrot on X11)
│   ├── shell.py             ← Bash shell integration (replaces PowerShell)
│   ├── sys_info.py          ← System info (psutil + nmcli)
│   ├── tts.py               ← Piper TTS (replaces Windows SAPI)
│   ├── weather.py           ← Weather (OpenWeatherMap)
│   ├── whatsapp.py          ← WhatsApp Web messaging
│   └── youtube_stats.py     ← YouTube Data API
├── memory/
│   ├── __init__.py
│   ├── memory_manager.py    ← JSON memory manager
│   ├── memory.example.json  ← Memory template
│   ├── phone_book.example.json ← Phone book template
│   └── health.json          ← Health tracking data (gitignored)
├── config/
│   ├── api_keys.json        ← API keys (gitignored)
│   └── api_keys.example.json ← Template
└── piper/                   ← Piper TTS binary + voice model (gitignored)
```

---

## 🔒 Security

- `config/api_keys.json`, `credentials.json`, `token.json`, and `memory/health.json` are added to `.gitignore` — your API keys, auth tokens, and personal data will **not** be included in the repository.
- `memory/memory.json` and `phone_book.json` are also excluded from publishing.
- Only `*.example.json` templates are included in the repository.
- The `piper/` directory (TTS binary + voice models) is gitignored — download via `setup.sh`.

---

## 🤝 Contributing

1. Fork this repository
2. Create a new branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -m "New feature: description"`
4. Push your branch: `git push origin feature/new-feature`
5. Open a Pull Request

---

## 📸 Screenshots

<p align="center">
  <img src="Icon/jarvis.jpeg" alt="JARVIS UI" width="600"/>
</p>

---

<div align="center">
<p>Originally developed by <a href="https://github.com/bnsware">bnsware</a> and <a href="https://www.instagram.com/alppunlu">alppunlu</a></p>
<p>🐧 Linux port by <a href="https://github.com/bobguffie">Bob McGuffie</a></p>
</div>