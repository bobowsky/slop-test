"""Mock implementation of PuzzleGenerator.

Replaces: LLM call (e.g. GPT-4o, Gemini) with structured challenge generation prompt
Ignores:  Actual scene analysis content, theme/mode/difficulty values
Returns:  Hardcoded "The Scholar's Chamber" scenario matching the results dashboard HTML
Expected real latency: 5-10 seconds
"""

from __future__ import annotations

import uuid

from app.models.schemas import (
    FinalEscape,
    PuzzleStep,
    ScenarioResponse,
    SceneAnalysis,
    Transformation,
    VapiConfig,
)
from app.services.interfaces import PuzzleGenerator


class MockPuzzleGenerator(PuzzleGenerator):
    async def generate(
        self,
        scene: SceneAnalysis,
        theme: str,
        mode: str,
        difficulty: str,
        original_image_url: str,
    ) -> ScenarioResponse:
        return ScenarioResponse(
            experience_id=f"R2L-{uuid.uuid4().hex[:8].upper()}",
            status="ready",
            title="The Scholar's Chamber",
            theme="The Archive",
            mode="Explore",
            difficulty="Medium",
            story=(
                "Your everyday space has been transformed into a medieval scholar's study. "
                "Ancient maps, illuminated manuscripts, and historical artifacts surround you. "
                "Explore each object to uncover facts about the Middle Ages and prove your knowledge."
            ),
            detected_objects=scene.detected_objects,
            transformations=[
                Transformation(
                    real_object="Coffee Mug",
                    game_object="Medieval Chalice",
                    puzzle_role="Historical quiz anchor",
                ),
                Transformation(
                    real_object="TV Remote",
                    game_object="Astrolabe",
                    puzzle_role="Knowledge challenge device",
                ),
                Transformation(
                    real_object="Bookshelf",
                    game_object="Illuminated Archive",
                    puzzle_role="Fact discovery station",
                ),
            ],
            puzzles=[
                PuzzleStep(
                    step=1,
                    title="Inspect the Chalice",
                    description="Examine the engravings on the Medieval Chalice to discover a historical date.",
                    hint="The chalice bears the coat of arms of a Polish king. When was Poland baptized?",
                    solution="966",
                ),
                PuzzleStep(
                    step=2,
                    title="Read the Astrolabe",
                    description="Use the Astrolabe to determine which century saw the first universities in Europe.",
                    hint="Think about Bologna and Paris. The earliest European universities emerged in this century.",
                    solution="12th century",
                ),
                PuzzleStep(
                    step=3,
                    title="Search the Archive",
                    description="Find the name of the document that established the rights of English nobles in 1215.",
                    hint="King John signed it at Runnymede. It is considered a cornerstone of constitutional law.",
                    solution="Magna Carta",
                ),
            ],
            final_escape=FinalEscape(
                objective="Enter the year of the Magna Carta to complete the knowledge path",
                solution="1215",
            ),
            voice_host_intro=(
                "Welcome, explorer. You have entered the Scholar's Chamber. "
                "Begin with the Medieval Chalice — it holds a historical secret."
            ),
            original_image_url=original_image_url,
            generated_image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCYfAbQ2q7_JFRAkTSkRkjCfq-34Tl-xvLsia6xvbnPUmirnRC1T1bzZT7A3Yl5oRIU3aVCty_xj8eDGlNZ9klIrBvHsc4fjteXXl4_EzqgNhLpct9zs-cMgu-_qCFX4OpqywxEaCAj3UJPZ3-0aSY0lbEkZjev5Bow7VRgV26dQdfPJmCkkg9TZwUTzb_w507Tm6ga8OQhlY4R18_hAckLYKZFSwL3qOFLLMyYizwjqYx5OEJrVDH_v-pNvaUke7W2REWw-PaVKe4",
            transformed_image_prompt=(
                "Transform the uploaded living room scene into a medieval "
                "scholar's study with illuminated manuscripts, ancient maps, "
                "a globe, quill pens, and warm candlelight, "
                "while preserving the original spatial layout of objects."
            ),
            vapi_config=VapiConfig(
                intro_message=(
                    "Welcome, explorer. You have entered the Scholar's Chamber. "
                    "Begin with the Medieval Chalice — it holds a historical secret."
                ),
                persona=(
                    "You are the ghost of a medieval scholar. Speak in a warm, "
                    "knowledgeable tone. You want to help the user learn, and you "
                    "share fascinating historical anecdotes to guide their discovery."
                ),
                guardrails=(
                    "Never reveal the final answer (1215) or challenge solutions directly. "
                    "Only provide the text from the 'hint' fields if the user asks for help."
                ),
            ),
        )
