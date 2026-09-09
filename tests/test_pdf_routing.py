import asyncio
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from extractor import main
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


def _write_vector_pdf(path: Path) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=400)
    stream = DecodedStreamObject()
    stream.set_data(b"0 0 m 100 100 l S\n" * 40)
    page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as output:
        writer.write(output)


def test_vector_pdf_routes_automatically_without_second_command(
    tmp_path: Path, monkeypatch
) -> None:
    pdf_path = tmp_path / "vector.pdf"
    _write_vector_pdf(pdf_path)
    calls: list[str] = []

    async def fake_process(_pdf_base64, options, max_retries=2):
        calls.append(options.model)
        return OrderDetails(items=[{"partNumber": "vector", "material": "S235"}])

    monkeypatch.setattr(main, "read_pdf_as_base64", lambda _path: "pdf-data")
    monkeypatch.setattr(main, "process_with_retry", fake_process)

    _, preflight, selected_model, _ = asyncio.run(
        main.extract_routed_pdf(pdf_path, customer_id="base")
    )

    assert preflight.kind == "vector_outlined"
    assert preflight.route == "vision_fast"
    assert selected_model == FAST_GEMINI_MODEL
    assert calls == [FAST_GEMINI_MODEL]


def test_empty_fast_result_escalates_once_in_auto_mode(
    tmp_path: Path, monkeypatch
) -> None:
    pdf_path = tmp_path / "vector.pdf"
    _write_vector_pdf(pdf_path)
    calls: list[str] = []

    async def fake_process(_pdf_base64, options, max_retries=2):
        calls.append(options.model)
        if options.model == FAST_GEMINI_MODEL:
            return OrderDetails(items=[{"partNumber": "vector"}])
        return OrderDetails(items=[{"partNumber": "vector", "material": "S235"}])

    monkeypatch.setattr(main, "read_pdf_as_base64", lambda _path: "pdf-data")
    monkeypatch.setattr(main, "process_with_retry", fake_process)

    data, _, selected_model, _ = asyncio.run(
        main.extract_routed_pdf(pdf_path, customer_id="base")
    )

    assert data.items[0].material == "S235"
    assert selected_model == DEEP_GEMINI_MODEL
    assert calls == [FAST_GEMINI_MODEL, DEEP_GEMINI_MODEL]
