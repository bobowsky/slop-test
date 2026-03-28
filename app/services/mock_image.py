"""Mock implementation of ImageTransformer.

Replaces: Image generation API call (e.g. DALL-E 3, Stable Diffusion XL)
Ignores:  Actual image content and transformation prompt
Returns:  A static placeholder URL (the same image used in the results dashboard HTML)
Expected real latency: 5-15 seconds
"""

from __future__ import annotations

from app.services.interfaces import ImageTransformer


class MockImageTransformer(ImageTransformer):
    PLACEHOLDER_URL = (
        "https://lh3.googleusercontent.com/aida-public/"
        "AB6AXuCYfAbQ2q7_JFRAkTSkRkjCfq-34Tl-xvLsia6xvbnPUmirnRC1T1bzZT7A3Yl5oRIU3aVCty_xj8eDGlNZ9klIrBvHsc4fjteXXl4_"
        "EzqgNhLpct9zs-cMgu-_qCFX4OpqywxEaCAj3UJPZ3-0aSY0lbEkZjev5Bow7VRgV26dQdfPJmCkkg9TZwUTzb_w507Tm6ga8OQhlY4R18_"
        "hAckLYKZFSwL3qOFLLMyYizwjqYx5OEJrVDH_v-pNvaUke7W2REWw-PaVKe4"
    )

    async def transform(self, image_path: str, prompt: str) -> str:
        return self.PLACEHOLDER_URL
