"""Customer detection service using Gemini Vision API."""

import logging
from typing import Literal

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .constants import DEFAULT_GEMINI_MODEL
from .types import CustomerDetectionResult
from .utils import get_api_key

logger = logging.getLogger(__name__)


CustomerType = Literal["elten", "rademaker", "base", "unknown"]


async def detect_customer_from_pdf_vision(
    pdf_base64: str,
) -> CustomerDetectionResult:
    """
    Detect customer from PDF using Gemini Vision.

    Looks at the BOM table (bottom right) for customer name.

    Args:
        pdf_base64: Base64-encoded PDF content

    Returns:
        CustomerDetectionResult with customer, confidence, and reason
    """
    try:
        api_key = get_api_key()
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(DEFAULT_GEMINI_MODEL)

        prompt = """You are analyzing a technical drawing PDF. Look at the BOM table (Bill of Materials) in the BOTTOM RIGHT corner of the drawing.

TASK: Identify the customer name from the BOM table.

Common customer names to look for:
- "ELTEN" or "Elten"
- "RADEMAKER" or "Rademaker"
- Other company names in the BOM header or title block

IMPORTANT:
- Look specifically in the bottom right area where the BOM table is located
- The customer name is usually in the title block or BOM header
- Return ONLY the customer name, nothing else
- If you see "ELTEN", respond with: ELTEN
- If you see "RADEMAKER", respond with: RADEMAKER
- If you cannot clearly identify a customer name, respond with: UNKNOWN

Your response should be a single word: either the customer name or UNKNOWN."""

        # Create PDF part
        pdf_part = {
            "inline_data": {
                "mime_type": "application/pdf",
                "data": pdf_base64,
            }
        }

        response = await model.generate_content_async([prompt, pdf_part])
        response_text = response.text.strip().upper()

        # Parse the response
        if "ELTEN" in response_text:
            return CustomerDetectionResult(
                customer="elten",
                confidence="high",
                reason='Detected "ELTEN" in BOM table via Vision API',
            )
        elif "RADEMAKER" in response_text:
            return CustomerDetectionResult(
                customer="rademaker",
                confidence="high",
                reason='Detected "RADEMAKER" in BOM table via Vision API',
            )
        elif "UNKNOWN" in response_text:
            return CustomerDetectionResult(
                customer="base",
                confidence="low",
                reason="No customer name found in BOM table - using base configuration",
            )
        else:
            return CustomerDetectionResult(
                customer="base",
                confidence="medium",
                reason=f'Found customer name "{response_text}" but no specific config - using base configuration',
            )

    except google_exceptions.GoogleAPIError as e:
        logger.warning(f"Vision-based customer detection failed (API error): {e}")
        return CustomerDetectionResult(
            customer="base",
            confidence="low",
            reason=f"Vision API error: {str(e)}",
        )
    except ValueError as e:
        logger.warning(f"Vision-based customer detection failed (value error): {e}")
        return CustomerDetectionResult(
            customer="base",
            confidence="low",
            reason=f"Value error: {str(e)}",
        )


def detect_customer_from_text(pdf_text: str) -> CustomerDetectionResult:
    """
    Detect customer from PDF text content (DEPRECATED - kept for fallback).

    Args:
        pdf_text: Extracted text from PDF

    Returns:
        CustomerDetectionResult with customer, confidence, and reason
    """
    text_lower = pdf_text.lower()

    if "rademaker" in text_lower:
        return CustomerDetectionResult(
            customer="rademaker",
            confidence="medium",
            reason='Detected "rademaker" in text',
        )
    elif "elten" in text_lower:
        return CustomerDetectionResult(
            customer="elten",
            confidence="medium",
            reason='Detected "elten" in text',
        )
    else:
        return CustomerDetectionResult(
            customer="base",
            confidence="low",
            reason="No customer name found in text - using base configuration",
        )


# Synchronous wrapper
def detect_customer_from_pdf_vision_sync(pdf_base64: str) -> CustomerDetectionResult:
    """Synchronous version of detect_customer_from_pdf_vision."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # Already in async context - create new loop in thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, detect_customer_from_pdf_vision(pdf_base64))
            return future.result()
    else:
        return asyncio.run(detect_customer_from_pdf_vision(pdf_base64))
