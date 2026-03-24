"""Utility functions for the extractor."""

import os


def get_api_key() -> str:
    """Get Gemini API key from environment."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("VITE_GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Set GEMINI_API_KEY (or VITE_GEMINI_API_KEY) in your environment"
        )
    return key


def setup_environment() -> None:
    """
    One-time environment setup called at application startup.

    Removes GOOGLE_API_KEY from the environment to prevent the google-genai
    library from preferring it over GEMINI_API_KEY, which would cause a
    confusing warning: "Both GOOGLE_API_KEY and GEMINI_API_KEY are set."
    """
    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]
