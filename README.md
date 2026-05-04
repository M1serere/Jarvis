Полностью рабочая, но достаточно кривая версия.
По итогам тестирования друзьями выявлено большое количество недочётов и багов. Вследствие чего будет создана новая версия с нуля и учтены все замечания, а так же она будет существенно улучшена.
На данный момент эта версия будет висеть тут, так как некоторые наработки будут использоваться в новой версии. Позже будет удалена за ненадобностью.
# 🤖 JARVIS — AI Voice Assistant for Desktop Automation

> A modular, production-style voice assistant inspired by JARVIS, capable of understanding speech, executing system-level actions, and evolving through memory and tools.

---

## 🚀 Live Features

* 🎤 Push-to-talk voice interaction
* 🧠 Natural language understanding via LLM
* 🔊 Text-to-speech responses
* 🧰 Tool-based action system (extensible)
* 🌐 Web browsing & real-time data (weather, news)
* 📁 File system management (safe sandboxed access)
* 🎵 Media control (music, volume, playback)
* 🧠 Persistent memory (short-term + long-term)
* 🔐 Permission & confirmation system
* 📊 Structured logging with auto-cleanup

---

## 🧱 Architecture Overview

```bash
jarvis/
│
├── core/              # orchestration & pipelines
├── brain/             # LLM interaction layer
├── voice/             # STT / TTS / microphone
├── tools/             # all executable actions
├── memory/            # assistant memory
├── safety/            # permissions & confirmations
├── ui/                # UI / states
├── config/            # configuration
├── logs/              # system logs
│
├── main.py
└── requirements.txt
```

---

## 🧠 System Design

The assistant operates through a structured pipeline:

```
User Input (Voice/Text)
    ↓
Speech-to-Text (optional)
    ↓
Core Orchestrator
    ↓
LLM (Brain)
    ↓
Tool Selection (JSON)
    ↓
Safety Layer (permissions)
    ↓
Execution
    ↓
Response (Text + Voice)
```

---

## 🛠 Tool System (Core Concept)

Each capability is implemented as an independent tool:

```python
class Tool:
    name = "open_browser"
    description = "Opens a browser"

    def run(self, args):
        pass
```

The LLM decides actions:

```json
{
  "action": "open_browser",
  "args": {"url": "https://google.com"}
}
```

This design makes the system:

* scalable
* testable
* easy to extend

---

## 🔐 Safety System

All actions are categorized:

* `safe` — executed immediately
* `confirm` — requires user approval
* `dangerous` — restricted actions

Example:

```
Are you sure you want to delete this file?
```

---

## 🧠 Memory System

Three-layer memory architecture:

* **Short-term** — recent conversation
* **Long-term** — stored user facts
* **Working memory** — current task context

---

## 📊 Logging

Tracks:

* user input
* parsed intent
* selected tool
* execution result

Includes:

* file-based logs
* automatic weekly cleanup of expired logs (~6 months retention)

---

# 🗺 Development Roadmap (Implemented)

## 🚀 Week 1 — Core & Text Assistant

* Built orchestration layer
* Implemented `handle_user_input`
* Integrated LLM
* Added CLI interface

**Result:** structured text-based assistant

---

## 🛠 Week 2 — Tool System

* Created base `Tool` class
* Implemented tool registry
* Enabled LLM tool calling via JSON
* Added:

  * browser open
  * Google search

**Result:** assistant performs real actions

---

## 📁 Week 3 — File System

* Implemented:

  * create_file
  * open_file
  * edit_file
* Added sandbox restrictions
* Added logging for file actions

**Result:** safe file manipulation

---

## 🌐 Week 4 — Internet Integration

* Implemented:

  * browser_search
  * open_url
  * get_weather
  * get_programming_news

**Result:** real-time external data access

---

## 🔊 Week 5 — Voice Pipeline

* Push-to-talk hotkey
* Speech-to-text
* Text-to-speech
* End-to-end voice flow

**Result:** fully voice-enabled assistant

---

## 🧠 Week 6 — Memory

* Persistent user memory
* Fact storage & retrieval

**Result:** personalized assistant

---

## 🎵 Week 7 — System Control

* Media control:

  * play / pause / next
* System control:

  * open_app
  * close_app
  * volume_control

**Result:** OS-level interaction

---


## 🔐 Week 8 — Safety & UX

* Permission system
* Confirmation prompts
* UI states:

  * listening
  * thinking
  * executing
* Logging system + cleanup

**Result:** production-style system

---

## ⚡ Future Improvements

* Wake word ("Jarvis")
* Plugin system
* Telegram / Discord integration
* Smart home control
* Mobile version
* Automation workflows

---

## 🧑‍💻 Installation

```bash
pip install -r requirements.txt
python main.py
```

## 🪟 Build EXE + Installer

For Windows packaging:

```powershell
.\build_exe.ps1
```

What the script does:

* generates installer/exe icons from `j_logo.png`
* builds `dist\Jarvis\Jarvis.exe` via PyInstaller
* builds `JarvisSetup.exe` in the project root via Inno Setup 6

Notes:

* for installed builds, app data is stored in `%LOCALAPPDATA%\Jarvis`
* `Inno Setup 6` must be installed for installer generation

---

## 💬 Example

```
User: Open YouTube
Jarvis: Opening YouTube

User: Create file notes.txt
Jarvis: Done

User: Play music
Jarvis: Where should I play it — YouTube or Yandex Music?
```

---

## 🏆 Why This Project Matters

This is not a simple script — it is a **modular AI system** demonstrating:

* system design
* LLM integration
* tool-based architectures
* safety engineering
* voice interfaces

Suitable for:

* portfolio projects
* AI engineering roles
* system design demonstrations

---

## 📜 License

MIT License
