# AI Storyteller – Full Interactive Prototype

A full-featured **interactive storytelling** app built with **Streamlit**. It supports:
- Branching, choice-driven stories
- Long context with memory
- Optional **image generation** per scene (OpenAI Images)
- Optional **text-to-speech narration** (local `pyttsx3`, or OpenAI TTS)
- Export: download the story transcript and audio files
- "Mock mode" to play without any API key (generates placeholder text/images)

## ✨ Demo Features
- Choose **genre**, **target age**, **tone**, and **reading level**.
- Make choices each scene; the plot adapts.
- Generate a scene illustration (optional).
- Listen to narration (optional).
- Save & export your story.

## 🚀 Quick Start

### 1) Create a virtual env (recommended)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2) Install requirements
```bash
pip install -r requirements.txt
```

### 3) Set environment (optional)
Copy `.env.example` to `.env` and fill your keys:
```bash
cp .env.example .env
# then edit .env
```

Supported providers:
- **OpenAI**: for text (gpt-4o-mini or similar), images, and TTS.

### 4) Run the app
```bash
streamlit run app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

## 🔐 API Keys
You can either:
- Put keys in **.env**, or
- Enter keys in the **sidebar** at runtime.

## 🧩 Providers & Modes
- **OpenAI Mode**: text + image + TTS if keys are present.
- **Local TTS**: `pyttsx3` works without internet (quality varies per OS).
- **Mock Mode**: No keys? No problem—use the toggle to see how the app flows.

## 📂 Export
- Download the story as a `.txt` file.
- Scene audio files as `.mp3` (when using OpenAI TTS) or `.wav` (with pyttsx3).
- All saved in the `exports/` folder and also available as a zip via the UI.

## ⚠️ Notes
- Image generation and cloud TTS incur costs on your account. Use carefully.
- `pyttsx3` voice support varies by platform; if it fails, switch to OpenAI TTS.

## 📜 License
MIT
