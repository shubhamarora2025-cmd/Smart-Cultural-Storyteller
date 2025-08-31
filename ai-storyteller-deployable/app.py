import os
import io
import time
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List

import streamlit as st
from dotenv import load_dotenv
from storyteller.story_engine import StoryEngine, StoryConfig, Choice
from storyteller.image_engine import ImageEngine
from storyteller.tts_engine import TTSEngine
from storyteller.utils import ensure_dir, save_text_file, zip_folder

APP_TITLE = "🎭 AI Storyteller — Interactive, Illustrated & Narrated"

def _load_env():
    load_dotenv(override=True)
    # Streamlit Cloud sometimes ignores .env; manual load helps locally too.

def sidebar_controls() -> Dict[str, Any]:
    st.sidebar.header("⚙️ Configuration")
    st.sidebar.caption("Provide keys or use Mock Mode to try without APIs.")

    mock_mode = st.sidebar.toggle("Mock Mode (no API required)", value=True)
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    openai_model = st.sidebar.text_input("OpenAI Text Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    openai_image_model = st.sidebar.text_input("OpenAI Image Model", value=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1"))
    tts_voice = st.sidebar.text_input("OpenAI TTS Voice", value=os.getenv("OPENAI_TTS_VOICE", "alloy"))

    st.sidebar.divider()
    use_images = st.sidebar.toggle("Generate scene images", value=False)
    use_tts = st.sidebar.toggle("Narrate scenes (TTS)", value=False)
    local_tts = st.sidebar.toggle("Use local TTS (pyttsx3)", value=True)

    st.sidebar.divider()
    st.sidebar.write("### Export")
    export_folder = st.sidebar.text_input("Export folder", value="exports")
    ensure_dir(export_folder)

    return dict(
        mock_mode=mock_mode,
        openai_key=openai_key,
        openai_model=openai_model,
        openai_image_model=openai_image_model,
        tts_voice=tts_voice,
        use_images=use_images,
        use_tts=use_tts,
        local_tts=local_tts,
        export_folder=export_folder,
    )

def story_setup_ui() -> StoryConfig:
    st.subheader("📚 Story Setup")
    col1, col2, col3 = st.columns(3)
    with col1:
        genre = st.selectbox("Genre", ["Fantasy", "Sci-Fi", "Mystery", "Adventure", "Fairy Tale", "Horror"])
    with col2:
        age = st.selectbox("Target Age", ["Kids (6-9)", "Pre-teens (10-12)", "Teens (13-17)", "Adults"])
    with col3:
        tone = st.selectbox("Tone", ["Whimsical", "Epic", "Cozy", "Humorous", "Dark"])

    reading_level = st.slider("Reading Level (simpler → complex)", 1, 5, 3)
    main_char = st.text_input("Main Character", value="Asha")
    setting = st.text_input("Setting", value="a seaside town in monsoon")
    theme = st.text_input("Theme / Moral (optional)", value="Friendship and courage")

    return StoryConfig(
        genre=genre,
        target_age=age,
        tone=tone,
        reading_level=reading_level,
        main_character=main_char,
        setting=setting,
        theme=theme.strip() or None,
    )

def render_scene(engine: StoryEngine, image_engine: Optional[ImageEngine], tts_engine: Optional[TTSEngine], cfg: Dict[str, Any]):
    st.divider()
    st.subheader(f"🎬 Scene {engine.state.scene_number}")
    st.write(engine.state.last_scene_text)

    if cfg["use_images"] and image_engine:
        with st.spinner("Generating illustration..."):
            img = image_engine.generate_image(engine.state.last_scene_image_prompt, seed=engine.state.scene_number)
        if img:
            st.image(img, caption="AI Illustration", use_column_width=True)

    if cfg["use_tts"] and tts_engine:
        with st.spinner("Narrating scene..."):
            audio_path = tts_engine.narrate(engine.state.last_scene_text, scene_no=engine.state.scene_number, out_dir=cfg["export_folder"])
        if audio_path:
            st.audio(audio_path)

    if engine.state.choices:
        st.write("#### Choose what happens next:")
        cols = st.columns(len(engine.state.choices))
        chosen_idx = None
        for i, ch in enumerate(engine.state.choices):
            with cols[i]:
                if st.button(ch.label, key=f"choice_{engine.state.scene_number}_{i}"):
                    chosen_idx = i
        if chosen_idx is not None:
            engine.advance(chosen_idx)

def export_ui(engine: StoryEngine, export_folder: str):
    st.divider()
    st.subheader("📦 Export Your Story")
    transcript_path = os.path.join(export_folder, "story.txt")
    save_text_file(transcript_path, engine.full_transcript())

    with open(transcript_path, "rb") as f:
        st.download_button("Download story.txt", f, file_name="story.txt")

    # Zip the entire export folder (text + audio/images if any)
    zip_bytes = io.BytesIO()
    zip_folder(export_folder, zip_bytes)
    st.download_button("Download exports.zip", zip_bytes.getvalue(), file_name="exports.zip")

def main():
    st.set_page_config(page_title="AI Storyteller", page_icon="🎭", layout="wide")
    _load_env()
    st.title(APP_TITLE)
    st.caption("Build interactive stories with images and narration.")

    cfg = sidebar_controls()
    story_cfg = story_setup_ui()

    # Initialize engines
    story_engine = StoryEngine(
        provider="openai" if (not cfg["mock_mode"] and cfg["openai_key"]) else "mock",
        openai_api_key=cfg["openai_key"],
        openai_model=cfg["openai_model"],
        config=story_cfg,
    )

    image_engine = None
    if cfg["use_images"]:
        image_engine = ImageEngine(
            provider="openai" if (not cfg["mock_mode"] and cfg["openai_key"]) else "mock",
            openai_api_key=cfg["openai_key"],
            openai_image_model=cfg["openai_image_model"],
        )

    tts_engine = None
    if cfg["use_tts"]:
        tts_engine = TTSEngine(
            provider=("local" if cfg["local_tts"] else ("openai" if (not cfg["mock_mode"] and cfg["openai_key"]) else "mock")),
            openai_api_key=cfg["openai_key"],
            openai_tts_voice=cfg["tts_voice"],
        )

    # Session state for continuity
    if "engine" not in st.session_state:
        st.session_state.engine = story_engine
        st.session_state.engine.start_story()
    else:
        # keep latest config's model/provider for continuity if user toggles
        st.session_state.engine.merge_from(story_engine)

    render_scene(st.session_state.engine, image_engine, tts_engine, cfg)

    # End / export
    if st.session_state.engine.is_finished():
        st.success("The story has concluded. Great journey!")
        export_ui(st.session_state.engine, cfg["export_folder"])

if __name__ == "__main__":
    main()
