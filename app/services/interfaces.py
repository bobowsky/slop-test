from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.schemas import HintResponse, ScenarioResponse, SceneAnalysis


class SceneAnalyzer(ABC):
    """Analyzes an uploaded image to extract objects, mood, and puzzle anchors.

    Real implementation: calls a multimodal vision model (e.g. Gemini, GPT-4o)
    to identify 3-5 objects, infer scene mood, and suggest puzzle anchors.
    """

    @abstractmethod
    async def analyze(self, image_path: str) -> SceneAnalysis: ...


class PuzzleGenerator(ABC):
    """Generates a complete puzzle scenario from scene analysis and user config.

    Real implementation: calls an LLM (e.g. GPT-4o, Gemini) with a structured
    prompt that includes detected objects, mood, theme, mode, and difficulty to
    produce a full ScenarioResponse with title, story, transformations, puzzles,
    final escape, and voice host intro.
    """

    @abstractmethod
    async def generate(
        self,
        scene: SceneAnalysis,
        theme: str,
        mode: str,
        difficulty: str,
        original_image_url: str,
    ) -> ScenarioResponse: ...


class ImageTransformer(ABC):
    """Generates a themed transformed image based on the original scene.

    Real implementation: calls an image generation API (e.g. DALL-E, Midjourney,
    Stable Diffusion) with a prompt derived from the scene analysis and theme
    to produce a stylized version of the original room.
    Expected real latency: 5-15 seconds.
    """

    @abstractmethod
    async def transform(self, image_path: str, prompt: str) -> str: ...


class HintProvider(ABC):
    """Provides contextual hints based on the current puzzle state.

    Real implementation: calls an LLM with the scenario context and current step
    to generate a short, helpful hint that doesn't reveal the solution directly.
    """

    @abstractmethod
    async def get_hint(
        self,
        context: dict,
        step: int,
        question: str | None = None,
    ) -> HintResponse: ...
