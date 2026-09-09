"""Global constants for the extractor application."""

# Fast is the normal route. Pro is reserved for an explicit deep scan or an
# automatic quality fallback after a sparse result.
FAST_GEMINI_MODEL = "gemini-3.6-flash"
DEEP_GEMINI_MODEL = "gemini-2.5-pro"
DEFAULT_GEMINI_MODEL = FAST_GEMINI_MODEL

# Keep an interactive run bounded. Two retries means at most three API calls
# and 2 + 4 seconds of programmed backoff, excluding request latency.
DEFAULT_MAX_RETRIES = 2
