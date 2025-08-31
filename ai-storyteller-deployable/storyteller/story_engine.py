from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import random
import textwrap
from pathlib import Path

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from .utils import clamp_sentences, safe_truncate

@dataclass
class StoryConfig:
    genre: str
    target_age: str
    tone: str
    reading_level: int
    main_character: str
    setting: str
    theme: Optional[str] = None

@dataclass
class Choice:
    label: str
    summary: str

@dataclass
class StoryState:
    scene_number: int = 0
    history: List[str] = field(default_factory=list)
    last_scene_text: str = ""
    last_scene_image_prompt: str = ""
    choices: List[Choice] = field(default_factory=list)
    finished: bool = False

class StoryEngine:
    def __init__(self, provider: str, openai_api_key: Optional[str], openai_model: str, config: StoryConfig):
        self.provider = provider  # "openai" or "mock"
        self.api_key = openai_api_key
        self.model = openai_model
        self.config = config
        self.state = StoryState()

        self._client = None
        if self.provider == "openai" and self.api_key and OpenAI:
            self._client = OpenAI(api_key=self.api_key)

    def merge_from(self, other: "StoryEngine"):
        # preserve state but allow hot-swap provider/model
        self.provider = other.provider or self.provider
        self.api_key = other.api_key or self.api_key
        self.model = other.model or self.model
        if other._client:
            self._client = other._client
        self.config = other.config

    def is_finished(self) -> bool:
        return self.state.finished

    def start_story(self):
        self.state.scene_number = 1
        opener = self._gen_scene(opening=True)
        self._update_state_from_scene(opener)

    def advance(self, choice_index: int):
        if 0 <= choice_index < len(self.state.choices):
            chosen = self.state.choices[choice_index]
            scene = self._gen_scene(choice_summary=chosen.summary)
            self._update_state_from_scene(scene)

    def full_transcript(self) -> str:
        return "\n\n".join(self.state.history + [self.state.last_scene_text])

    # --------- Internal ----------

    def _update_state_from_scene(self, scene: Dict[str, Any]):
        text = scene.get("text", "")
        img_prompt = scene.get("image_prompt", "")
        choices = scene.get("choices", [])
        finished = scene.get("finished", False)

        if self.state.last_scene_text:
            self.state.history.append(self.state.last_scene_text)
        self.state.last_scene_text = text
        self.state.last_scene_image_prompt = img_prompt
        self.state.choices = [Choice(**c) for c in choices]
        self.state.finished = finished

        if not finished:
            self.state.scene_number += 1

    def _gen_scene(self, opening: bool=False, choice_summary: Optional[str]=None) -> Dict[str, Any]:
        # Mock provider: simple, deterministic(ish) output for demo use
        if self.provider == "mock" or self._client is None:
            return self._mock_scene(opening, choice_summary)

        # OpenAI provider
        sys_prompt = self._system_prompt()
        user_prompt = self._user_prompt(opening, choice_summary)

        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.9,
        )
        content = resp.choices[0].message.content

        # Simple parsing convention
        text, image_prompt, choices, finished = self._parse_model_output(content)
        return dict(text=text, image_prompt=image_prompt, choices=choices, finished=finished)

    def _system_prompt(self) -> str:
        age_note = f"Target age: {self.config.target_age}. Reading level {self.config.reading_level}/5."
        theme = f" Theme: {self.config.theme}." if self.config.theme else ""
        return (
            "You are a master interactive storyteller. "
            f"Genre: {self.config.genre}. Tone: {self.config.tone}. {age_note}"
            f" The main character is {self.config.main_character} in {self.config.setting}.{theme} "
            "Write vivid, concise scenes (120–220 words). "
            "End each scene with 2–3 numbered choices the reader can pick. "
            "Return output in this format:\n"
            "<SCENE>\n...text...\n</SCENE>\n"
            "<IMAGE_PROMPT>...one-line visual prompt...</IMAGE_PROMPT>\n"
            "<CHOICES>\n1) label — summary\n2) label — summary\n</CHOICES>\n"
            "<FINISHED>true|false</FINISHED>"
        )

    def _user_prompt(self, opening: bool, choice_summary: Optional[str]) -> str:
        history = "\n".join(self.state.history[-3:])  # keep last 3 scenes
        prefix = "Opening scene." if opening else f"Continue based on choice: {choice_summary}."
        return f"{prefix}\n\nRecent scenes:\n{history}\n"

    def _parse_model_output(self, txt: str):
        # Very lightweight parsing with defaults
        def extract(tag):
            start = txt.find(f"<{tag}>")
            end = txt.find(f"</{tag}>")
            if start == -1 or end == -1:
                return ""
            return txt[start+len(tag)+2:end].strip()

        scene_text = extract("SCENE") or txt.strip()
        image_prompt = extract("IMAGE_PROMPT") or f"Illustration of {self.config.main_character} in {self.config.setting}."
        choices_block = extract("CHOICES")
        finished_raw = extract("FINISHED").lower()
        finished = "true" in finished_raw

        choices = []
        if choices_block:
            for line in choices_block.splitlines():
                line = line.strip()
                if not line:
                    continue
                if ") " in line and "—" in line:
                    # "1) Explore the cave — explore_cave"
                    try:
                        after_num = line.split(") ", 1)[1]
                    except Exception:
                        after_num = line
                    label, summary = after_num.split("—", 1)
                    choices.append({"label": label.strip(), "summary": summary.strip()})
        if not choices and not finished:
            choices = [
                {"label":"Go left","summary":"left_path"},
                {"label":"Go right","summary":"right_path"},
            ]
        return scene_text, image_prompt, choices, finished

    # ---------- Mock generator ----------
    def _mock_scene(self, opening: bool, choice_summary: Optional[str]) -> Dict[str, Any]:
        rnd = random.Random(42 + self.state.scene_number)  # stable variance
        if opening:
            text = (
                f"{self.config.main_character} lived in {self.config.setting}, dreaming of {self.config.genre.lower()} adventures. "
                f"One stormy evening, a {self.config.tone.lower()} whisper slipped through the window, carrying a map inked with moonlight. "
                f"Following the map would mean trading comfort for mystery—and perhaps discovering a truth about {self.config.theme or 'destiny'}."
                "\n\nWhat will {name} do next?".replace("{name}", self.config.main_character)
            )
            img = f"{self.config.main_character} holding a glowing map in {self.config.setting}, stylized, cinematic lighting"
            choices = [
                {"label":"Study the map closely","summary":"inspect_map"},
                {"label":"Sneak out into the rain","summary":"venture_out"},
                {"label":"Ask a friend for help","summary":"seek_friend"},
            ]
        else:
            text = (
                f"Choosing to {choice_summary.replace('_',' ')}, "
                f"{self.config.main_character} stepped forward. The night smelled of salt and possibility. "
                "A stray cat traced circles around their ankles as lanterns flickered awake across the harbor. "
                "Somewhere, a door creaked—the map responded with a pulse of cool light."
            )
            img = f"{self.config.main_character} in the rain near the harbor; lanterns and reflections; moody; {choice_summary}"
            # End after 5 scenes
            finish_now = self.state.scene_number >= 5
            choices = [] if finish_now else [
                {"label":"Follow the pulsing glow","summary":"follow_glow"},
                {"label":"Enter the creaking door","summary":"enter_door"},
            ]
            if finish_now:
                text += "\n\nAt last, the journey's first chapter closed—with courage awakened."
                return {"text": text, "image_prompt": img, "choices": [], "finished": True}

        return {"text": text, "image_prompt": img, "choices": choices, "finished": False}
