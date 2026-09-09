"""Cheap structural PDF scan used to choose an extraction route.

The preflight deliberately does not interpret manufacturing semantics. It only
determines whether useful embedded text, raster images, or vector linework are
present. Critical findings such as threads, fits, and tolerances still require
the normal evidence-backed extraction step.
"""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from pypdf import PdfReader


PdfKind = Literal[
    "text_native",
    "hybrid",
    "raster_scan",
    "vector_outlined",
    "text_unextractable",
    "empty",
    "unknown",
    "protected",
    "unreadable",
]
PdfRoute = Literal[
    "text_fast",
    "vision_fast",
    "skip",
    "manual_review",
]
Complexity = Literal["simple", "moderate", "complex"]


_PATH_OPERATOR_RE = re.compile(
    rb"(?<!\S)(?:m|l|c|v|y|h|re|S|s|f|F|f\*|B|B\*|b|b\*|n)(?!\S)"
)
_TEXT_OPERATOR_RE = re.compile(rb"(?<!\S)(?:BT|Tj|TJ)(?!\S)")


@dataclass(frozen=True)
class PdfPreflightResult:
    """Auditable result of the cheap PDF classification step."""

    kind: PdfKind
    route: PdfRoute
    complexity: Complexity
    confidence: float
    page_count: int
    pages_scanned: int
    text_chars: int
    alnum_chars: int
    font_count: int
    image_count: int
    content_bytes: int
    text_operator_count: int
    vector_operator_count: int
    max_page_area_points: float
    elapsed_ms: float
    evidence: str
    error: str | None = None

    @property
    def needs_visual_scan(self) -> bool:
        return self.route == "vision_fast"

    def model_dump(self) -> dict[str, Any]:
        """Return a serializable representation without requiring Pydantic."""

        return asdict(self)


def _resolve(value: Any) -> Any:
    if hasattr(value, "get_object"):
        return value.get_object()
    return value


def classify_pdf_kind(
    *,
    text_chars: int,
    alnum_chars: int,
    font_count: int,
    image_count: int,
    content_bytes: int = 0,
    text_operator_count: int,
    vector_operator_count: int,
) -> tuple[PdfKind, PdfRoute, float]:
    """Classify a PDF from cheap structural counters.

    Absence of extractable text never means that a drawing is empty. CAD
    systems often convert glyphs into vector outlines; those documents are
    routed to vision automatically.
    """

    usable_text = alnum_chars >= 20 or text_chars >= 50
    has_text_structure = font_count > 0 or text_operator_count > 0
    has_vector_content = vector_operator_count >= 25

    if usable_text and image_count:
        return "hybrid", "vision_fast", 0.92
    if usable_text:
        return "text_native", "text_fast", 0.95
    if image_count and has_vector_content:
        return "hybrid", "vision_fast", 0.88
    if image_count:
        return "raster_scan", "vision_fast", 0.92
    if has_vector_content:
        return "vector_outlined", "vision_fast", 0.94
    if has_text_structure:
        return "text_unextractable", "vision_fast", 0.82
    if content_bytes:
        return "unknown", "manual_review", 0.65
    return "empty", "skip", 0.90


def _complexity(
    *,
    page_count: int,
    vector_operator_count: int,
    image_count: int,
    max_page_area_points: float,
    usable_text: bool,
) -> Complexity:
    score = 0
    if page_count > 1:
        score += min(3, page_count - 1)
    if max_page_area_points >= 3_000_000:
        score += 2
    elif max_page_area_points >= 1_000_000:
        score += 1
    if vector_operator_count >= 5_000:
        score += 2
    elif vector_operator_count >= 500:
        score += 1
    if image_count > 1:
        score += 1
    if not usable_text:
        score += 1

    if score >= 5:
        return "complex"
    if score >= 2:
        return "moderate"
    return "simple"


def preflight_pdf(path: Path, max_pages: int = 2) -> PdfPreflightResult:
    """Inspect at most ``max_pages`` without rendering or external AI calls."""

    started = time.perf_counter()
    try:
        reader = PdfReader(str(path), strict=False)
        if reader.is_encrypted:
            try:
                unlocked = reader.decrypt("")
            except Exception:  # noqa: BLE001 - the result records the failure.
                unlocked = 0
            if not unlocked:
                return PdfPreflightResult(
                    kind="protected",
                    route="manual_review",
                    complexity="complex",
                    confidence=0.99,
                    page_count=0,
                    pages_scanned=0,
                    text_chars=0,
                    alnum_chars=0,
                    font_count=0,
                    image_count=0,
                    content_bytes=0,
                    text_operator_count=0,
                    vector_operator_count=0,
                    max_page_area_points=0.0,
                    elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
                    evidence="PDF is encrypted and cannot be opened with an empty password.",
                )

        page_count = len(reader.pages)
        pages_scanned = min(page_count, max(1, max_pages))
        text_parts: list[str] = []
        font_count = 0
        image_count = 0
        content_bytes_total = 0
        text_operator_count = 0
        vector_operator_count = 0
        max_page_area_points = 0.0

        for page in reader.pages[:pages_scanned]:
            try:
                text_parts.append(page.extract_text() or "")
            except Exception:  # noqa: BLE001 - structural routing can continue.
                text_parts.append("")

            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            max_page_area_points = max(max_page_area_points, width * height)

            resources = _resolve(page.get("/Resources")) or {}
            fonts = _resolve(resources.get("/Font")) or {}
            font_count += len(fonts)
            xobjects = _resolve(resources.get("/XObject")) or {}
            for value in xobjects.values():
                try:
                    obj = _resolve(value)
                    if obj.get("/Subtype") == "/Image":
                        image_count += 1
                except Exception:  # noqa: BLE001 - malformed objects are ignored.
                    continue

            try:
                contents = page.get_contents()
                content_bytes = contents.get_data() if contents is not None else b""
            except Exception:  # noqa: BLE001 - counters remain conservative.
                content_bytes = b""
            content_bytes_total += len(content_bytes)
            text_operator_count += len(_TEXT_OPERATOR_RE.findall(content_bytes))
            vector_operator_count += len(_PATH_OPERATOR_RE.findall(content_bytes))

        text = "\n".join(text_parts)
        text_chars = len(text.strip())
        alnum_chars = sum(character.isalnum() for character in text)
        kind, route, confidence = classify_pdf_kind(
            text_chars=text_chars,
            alnum_chars=alnum_chars,
            font_count=font_count,
            image_count=image_count,
            content_bytes=content_bytes_total,
            text_operator_count=text_operator_count,
            vector_operator_count=vector_operator_count,
        )
        complexity = _complexity(
            page_count=page_count,
            vector_operator_count=vector_operator_count,
            image_count=image_count,
            max_page_area_points=max_page_area_points,
            usable_text=alnum_chars >= 20 or text_chars >= 50,
        )
        evidence = (
            f"pages={page_count}; scanned={pages_scanned}; text_chars={text_chars}; "
            f"fonts={font_count}; images={image_count}; "
            f"content_bytes={content_bytes_total}; text_ops={text_operator_count}; "
            f"vector_ops={vector_operator_count}"
        )
        return PdfPreflightResult(
            kind=kind,
            route=route,
            complexity=complexity,
            confidence=confidence,
            page_count=page_count,
            pages_scanned=pages_scanned,
            text_chars=text_chars,
            alnum_chars=alnum_chars,
            font_count=font_count,
            image_count=image_count,
            content_bytes=content_bytes_total,
            text_operator_count=text_operator_count,
            vector_operator_count=vector_operator_count,
            max_page_area_points=round(max_page_area_points, 2),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            evidence=evidence,
        )
    except Exception as exc:  # noqa: BLE001 - return an auditable routing result.
        return PdfPreflightResult(
            kind="unreadable",
            route="manual_review",
            complexity="complex",
            confidence=0.99,
            page_count=0,
            pages_scanned=0,
            text_chars=0,
            alnum_chars=0,
            font_count=0,
            image_count=0,
            content_bytes=0,
            text_operator_count=0,
            vector_operator_count=0,
            max_page_area_points=0.0,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            evidence="PDF parsing failed.",
            error=str(exc),
        )
