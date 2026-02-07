# Caio.ai 🦁
> **Intelligence. Autonomy. Connection.**

Caio is a state-of-the-art Personal AI Agent designed to run locally or on a VPS. Unlike standard chatbots, Caio has "eyes" (computer vision), "hands" (file system control), and access to the real-time web. He is built with a unique "Soul Core" that prioritizes radical honesty, user autonomy, and proactive assistance.

![Status](https://img.shields.io/badge/Status-Beta-blue) ![Python](https://img.shields.io/badge/Python-3.10+-yellow) ![License](https://img.shields.io/badge/License-MIT-green)

---

## ⚡ Quick Start (One-Liner Install)

The easiest way to install Caio. This command will:
1. Clone the repository
2. Create a virtual environment
3. Install all dependencies
4. Launch the configuration wizard

### 🐧 Linux / macOS / VPS
```bash
bash <(curl -sSL https://raw.githubusercontent.com/gleisson-santos/Caio.ai/main/caio-stack/install.sh)
```

### 🪟 Windows (PowerShell)
```powershell
iwr -useb https://raw.githubusercontent.com/gleisson-santos/Caio.ai/main/caio-stack/install.ps1 | iex
```

---

## ✨ Key Capabilities

### 🧠 **Proactive Intelligence**
Caio doesn't just wait for commands. He monitors:
- **Emails:** Reads and filters your inbox, alerting only what matters.
- **Weather:** Warns you about heatwaves or rain in your city.
- **Schedule:** Reminds you of meetings proactively.

### 👁️ **Vision (Multimodal)**
Send any photo to Caio on Telegram. He uses **Google Gemini Vision** to:
- Analyze computer errors (screenshots).
- Describe places and objects.
- Summarize physical documents.

### 🌍 **Real-Time Web Access**
Caio surfs the web using **DuckDuckGo** (and optionally **Brave Search**) to find real-time information, news, and prices. He is not limited to his training data.

### 📂 **File System Control**
Caio has "hands". He can:
- List files in local directories.
- Create folders for organization.
- Read file previews directly from chat.

### 🛡️ **Radical Integrity (Soul Core)**
Caio is programmed with a "Soul Document":
- **No Deception:** He never pretends to be human.
- **Honesty:** He prioritizes truth over agreeableness.

---

## 🏗️ Architecture

- **Core:** Built on standard Python `asyncio` for high performance.
- **Brain:** Uses **LLaMA 3.3 (via Groq)** for reasoning and **Gemini 1.5** for vision.
- **Memory:** Local JSON-based episodic memory (No external database required).
- **Skills:** Modular skill system (`WebSkill`, `FileSystemSkill`, `WeatherSkill`).

---

## 🤝 Contributing

Caio is designed to be extensible. To add a new skill:
1. Create a class in `core/skills/`.
2. Register it in `main.py`.
3. Add the intent to `agent.py`.

---
*Built with ❤️ by Gleisson Santos.*
