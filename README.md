# Caio.ai 🦁
> **Intelligence. Autonomy. Connection.**

Caio is a state-of-the-art Personal AI Agent designed to run locally or on a VPS. Unlike standard chatbots, Caio has "eyes" (computer vision), "hands" (file system control), and access to the real-time web. He is built with a unique "Soul Core" that prioritizes radical honesty, user autonomy, and proactive assistance.

![Status](https://img.shields.io/badge/Status-v2.0--Elite-blue) ![Python](https://img.shields.io/badge/Python-3.10+-yellow) ![License](https://img.shields.io/badge/License-MIT-green)

---

## ⚡ Quick Start (One-Liner Install)

The easiest way to install or update Caio. This command will:
1. Clone/Update the repository
2. Create a virtual environment
3. Install all dependencies
4. Launch the configuration wizard

### 🐧 Linux / macOS / VPS
```bash
bash <(curl -sSL https://raw.githubusercontent.com/gleisson-santos/Caio.ai/main/install.sh)
```

---

## ✨ Key Capabilities (v2.0 Elite)

### 🧠 **Proactive Intelligence & Multi-Intent**
Caio now understands complex, multi-step commands and acts proatively:
- **Multi-Intent Processing:** Say *"Schedule a meeting tomorrow at 10am and remind me in 1 minute"* and Caio will do both simultaneously.
- **Proactive Alerts:** Caio monitors your Google Calendar and sends a Telegram alert **15 minutes before** any event starts.
- **Smart Scheduler:** Robust reminder system with natural language processing.

### 📁 **Google Drive & Document Processing**
Caio now has full access to your cloud and documents:
- **Google Drive Integration:** Upload files, create folders, and get shareable links directly via Telegram.
- **Document Analysis:** Caio can read and summarize **PDF, Word (DOCX), and Excel (XLSX)** files.
- **File Management:** Move, copy, and organize files locally and in the cloud.

### 🌍 **Brave Search & Web Access**
- **Brave Search API:** High-precision web searches for real-time news and data.
- **Web Synthesis:** Analyzes multiple sources to provide a single, coherent answer.

### 👁️ **Vision (Multimodal)**
Send any photo to Caio on Telegram. He uses **Google Gemini Vision** to analyze screenshots, documents, and objects.

### 💬 **Telegram Friendly**
- **Clean Formatting:** All messages are optimized for Telegram (Markdown), using clear bolding and readable dates.
- **Proactive Personality:** A warm, sagacious, and helpful digital entity.

---

## 🏗️ Architecture

- **Core:** Python `asyncio` with a multi-intent pipeline.
- **Brain:** **LLaMA 3.3 (via Groq)** for reasoning and **Gemini 1.5** for vision.
- **Skills:** Modular system including `GoogleDriveSkill`, `BraveSearchSkill`, and `DocumentProcessorSkill`.

---

## 🤝 Contributing

Caio is designed to be extensible. To add a new skill:
1. Create a class in `core/skills/`.
2. Register it in `main.py`.
3. Add the intent to `agent.py`.

---
*Built with ❤️ by Gleisson Santos.*
