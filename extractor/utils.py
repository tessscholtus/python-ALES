"""Utility functions for the extractor."""

import os

def get_api_key() -> str:
    """
    Get Gemini API key from environment.
    
    Checks:
    1. GEMINI_API_KEY
    2. VITE_GEMINI_API_KEY
    """
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("VITE_GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Set GEMINI_API_KEY (or VITE_GEMINI_API_KEY) in your environment"
        )
    return key
