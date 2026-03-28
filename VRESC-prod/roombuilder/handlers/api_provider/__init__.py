"""
API provider package for the roombuilder pipeline.

The ``ApiProvider`` abstract base class defines the interface that all
provider implementations must satisfy.  Import the concrete provider you
want to use from its sub-package.

Available providers
-------------------
  openrouter  →  OpenRouterProvider   (OPENROUTER_API_KEY)
  gemini      →  GeminiProvider       (GOOGLE_API_KEY)

Quick usage
-----------
    from handlers.api_provider import ApiProvider
    from handlers.api_provider.openrouter import OpenRouterProvider
    from handlers.api_provider.gemini import GeminiProvider

    provider: ApiProvider = GeminiProvider()
    provider.generate_audio(prompt, out_path, model="lyria-3-clip-preview")
"""

from .base import ApiProvider

__all__ = ["ApiProvider"]
