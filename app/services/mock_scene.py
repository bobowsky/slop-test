"""Mock implementation of SceneAnalyzer.

Replaces: Multimodal vision API call (e.g. Gemini 1.5 Pro, GPT-4o Vision)
Ignores:  Actual image content -- always returns the same canned objects
Returns:  3 detected objects matching the Alchemist's Study scenario
Expected real latency: 2-5 seconds
"""

from __future__ import annotations

from app.models.schemas import SceneAnalysis
from app.services.interfaces import SceneAnalyzer


class MockSceneAnalyzer(SceneAnalyzer):
    async def analyze(self, image_path: str) -> SceneAnalysis:
        return SceneAnalysis(
            detected_objects=["coffee mug", "TV remote", "bookshelf"],
            mood="cozy domestic",
            puzzle_anchors=["coffee mug", "TV remote", "bookshelf"],
        )
