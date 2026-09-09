from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from extractor.pdf_preflight import classify_pdf_kind, preflight_pdf


def test_classifies_vector_outlined_without_treating_it_as_empty() -> None:
    kind, route, confidence = classify_pdf_kind(
        text_chars=0,
        alnum_chars=0,
        font_count=0,
        image_count=0,
        content_bytes=1000,
        text_operator_count=0,
        vector_operator_count=500,
    )

    assert kind == "vector_outlined"
    assert route == "vision_fast"
    assert confidence >= 0.9


def test_classifies_native_text_as_fast_route() -> None:
    kind, route, _ = classify_pdf_kind(
        text_chars=120,
        alnum_chars=90,
        font_count=1,
        image_count=0,
        content_bytes=1000,
        text_operator_count=3,
        vector_operator_count=20,
    )

    assert kind == "text_native"
    assert route == "text_fast"


def test_preflight_detects_vector_page(tmp_path: Path) -> None:
    pdf_path = tmp_path / "vector.pdf"
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=400)
    stream = DecodedStreamObject()
    stream.set_data((b"0 0 m 100 100 l S\n" * 40))
    page[NameObject("/Contents")] = writer._add_object(stream)
    with pdf_path.open("wb") as output:
        writer.write(output)

    result = preflight_pdf(pdf_path)

    assert result.kind == "vector_outlined"
    assert result.route == "vision_fast"
    assert result.vector_operator_count >= 40
    assert result.text_chars == 0


def test_preflight_skips_truly_empty_page(tmp_path: Path) -> None:
    pdf_path = tmp_path / "empty.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with pdf_path.open("wb") as output:
        writer.write(output)

    result = preflight_pdf(pdf_path)

    assert result.kind == "empty"
    assert result.route == "skip"
