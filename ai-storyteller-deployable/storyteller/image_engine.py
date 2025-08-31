from __future__ import annotations
import io
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import textwrap

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

class ImageEngine:
    def __init__(self, provider: str, openai_api_key: Optional[str], openai_image_model: str):
        self.provider = provider  # "openai" or "mock"
        self.model = openai_image_model
        self._client = None
        if provider == "openai" and openai_api_key and OpenAI:
            self._client = OpenAI(api_key=openai_api_key)

    def generate_image(self, prompt: str, seed: int = 0) -> Optional[Image.Image]:
        if self.provider == "mock" or self._client is None:
            return self._placeholder(prompt)
        # OpenAI Images API (base64 png response)
        resp = self._client.images.generate(
            model=self.model,
            prompt=prompt,
            size="1024x1024",
            n=1,
        )
        b64 = resp.data[0].b64_json
        import base64
        img_bytes = base64.b64decode(b64)
        return Image.open(io.BytesIO(img_bytes))

    def _placeholder(self, prompt: str) -> Image.Image:
        # Simple generated placeholder with wrapped prompt text
        W, H = 1024, 576
        img = Image.new("RGB", (W, H), (240, 240, 240))
        draw = ImageDraw.Draw(img)
        title = "Illustration Preview"
        draw.text((24, 24), title, fill=(0, 0, 0))
        wrapped = textwrap.fill(prompt[:200], width=48)
        draw.text((24, 72), wrapped, fill=(20, 20, 20))
        return img
