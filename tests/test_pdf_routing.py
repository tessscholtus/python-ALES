from extractor.constants import DEEP_GEMINI_MODEL, FAST_GEMINI_MODEL
from extractor.main import is_sparse_extraction, normalize_customer_id, select_model
from extractor.pdf_preflight import PdfPreflightResult
from extractor.types import OrderDetails


def _profile(*, pages: int = 1, route: str = "vision_fast") -> PdfPreflightResult:
    return PdfPreflightResult(
        kind="vector_outlined",
        route=route,
        complexity="complex",
        confidence=0.94,
        page_count=pages,
        pages_scanned=min(pages, 2),
        text_chars=0,
        alnum_chars=0,
        font_count=0,
        image_count=0,
        content_bytes=1000,
        text_operator_count=0,
        vector_operator_count=5000,
        max_page_area_points=4_000_000,
        elapsed_ms=10.0,
        evidence="test",
    )


def test_auto_uses_fast_model_for_single_page_outlined_pdf() -> None:
    assert select_model(_profile(), "auto", None) == FAST_GEMINI_MODEL


def test_auto_uses_deep_model_for_large_multipage_complex_pdf() -> None:
    assert select_model(_profile(pages=5), "auto", None) == DEEP_GEMINI_MODEL


def test_manual_model_override_wins() -> None:
    assert select_model(_profile(), "deep", "gemini-test") == "gemini-test"


def test_auto_customer_does_not_call_detection() -> None:
    assert normalize_customer_id("auto") == "base"


def test_sparse_result_can_trigger_quality_fallback() -> None:
    assert is_sparse_extraction(OrderDetails(items=[{"partNumber": "part-1"}]))
    assert not is_sparse_extraction(
        OrderDetails(items=[{"partNumber": "part-1", "material": "S235"}])
    )
