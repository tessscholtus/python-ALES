"""Utility functions for the extractor."""

import os

def get_api_key() -> str:
    """
    Get Gemini API key from environment.
    
    Checks:
    1. GEMINI_API_KEY
    2. VITE_GEMINI_API_KEY
    
    Also removes GOOGLE_API_KEY from environment to prevent
    the google-genai library warning about conflicting keys.
    """
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("VITE_GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Set GEMINI_API_KEY (or VITE_GEMINI_API_KEY) in your environment"
        )
    
    # Remove GOOGLE_API_KEY to prevent google-genai library warning:
    # "Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY."
    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]
    
    return key
