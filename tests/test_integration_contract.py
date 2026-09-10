from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from extractor.config_loader import find_config_root
from extractor.gemini_service import (
    backfill_detected_signals,
    normalize_holes,
    normalize_machining_operations,
)
from extractor.integration_cli import INTEGRATION_SCHEMA_VERSION, build_compact_summary, run
from extractor.main import should_run_gemini
from extractor.pdf_preflight import PdfPreflightResult
from extractor.types import ExtractionOptions, OrderDetails, ProcessingMetadata
from extractor.xml_writer import build_simple_order_xml


def test_package_config_wins_over_unrelated_working_directory(
    tmp_path: Path, monkeypatch
) -> None:
    (tmp_path / "config").mkdir()
    monkeypatch.chdir(tmp_path)

    assert (find_config_root() / "base.yaml").is_file()


def test_expected_step_part_number_is_an_explicit_option() -> None:
    options = ExtractionOptions(
        pdfFilename="drawing-name",
        expectedPartNumber="STEP-PART-42",
    )

    assert options.pdf_filename == "drawing-name"
    assert options.expected_part_number == "STEP-PART-42"


def test_integration_metadata_is_written_to_xml() -> None:
    data = OrderDetails(
        items=[{"partNumber": "STEP-PART-42", "material": "S235"}],
        metadata=ProcessingMetadata(
            totalPDFs=1,
            successfulPDFs=1,
            failedPDFs=0,
            detectedCustomer="BASE",
            sourcePDF="drawing.pdf",
            stepPartId="solid-7",
            stepSolidIndex=7,
            stepPartName="STEP-PART-42",
            matchStrategy="exact_normalized",
            matchConfidence=1.0,
            preflightKind="text_native",
            preflightRoute="text_fast",
            preflightConfidence=0.95,
            preflightMs=12.5,
            geminiModel="gemini-test",
            geminiSeconds=1.25,
        ),
    )

    xml = build_simple_order_xml(data)

    assert "<PartNumber>STEP-PART-42</PartNumber>" in xml
    assert "<SourcePDF>drawing.pdf</SourcePDF>" in xml
    assert "<StepPartId>solid-7</StepPartId>" in xml
    assert "<StepSolidIndex>7</StepSolidIndex>" in xml
    assert "<MatchConfidence>1.0</MatchConfidence>" in xml
    assert "<GeminiModel>gemini-test</GeminiModel>" in xml


def test_integration_schema_version_is_explicit() -> None:
    assert INTEGRATION_SCHEMA_VERSION == "1.0"


def test_integration_rejects_unknown_request_schema(tmp_path: Path) -> None:
    args = argparse.Namespace(
        pdf=tmp_path / "missing.pdf",
        xml=tmp_path / "result.xml",
        part_number="P-1",
        part_id="solid-3",
        solid_index=3,
        schema_version="9.9",
    )

    assert asyncio.run(run(args)) == 4


def test_post_processing_can_be_followed_by_final_pydantic_validation() -> None:
    payload = {
        "items": [
            {
                "partNumber": "P-1",
                "machiningOperations": [
                    {"normalizedCode": "TAP", "operation": "tapping", "threadSize": "M6"}
                ],
            }
        ]
    }
    raw = OrderDetails(**payload).model_dump(by_alias=True, exclude_none=True)
    normalize_machining_operations(raw)
    normalize_holes(raw)
    backfill_detected_signals(raw)

    final = OrderDetails(**raw)

    assert final.items[0].machining_operations
    assert final.detected_signals


def _preflight(route: str) -> PdfPreflightResult:
    return PdfPreflightResult(
        kind="hybrid" if route == "vision_fast" else "text_native",
        route=route,
        complexity="moderate",
        confidence=0.9,
        page_count=1,
        pages_scanned=1,
        text_chars=100,
        alnum_chars=80,
        font_count=1,
        image_count=1,
        content_bytes=1000,
        text_operator_count=1,
        vector_operator_count=1,
        max_page_area_points=100.0,
        elapsed_ms=5.0,
        evidence="fixture",
    )


def test_gemini_policy_is_applied_after_preflight() -> None:
    assert should_run_gemini(_preflight("text_fast"), "auto") is True
    assert should_run_gemini(_preflight("manual_review"), "auto") is False
    assert should_run_gemini(_preflight("text_fast"), "vision_only") is False
    assert should_run_gemini(_preflight("vision_fast"), "vision_only") is True
    assert should_run_gemini(_preflight("vision_fast"), "never") is False


def test_compact_summary_contains_pdf_headline_results() -> None:
    data = OrderDetails(
        drawingNumber="D-42",
        items=[
            {
                "material": "S235",
                "surfaceTreatment": "powder coating",
                "revision": "B",
                "holes": [{"count": 3, "diameter": "6 mm"}],
                "toleratedLengths": [{"dimension": "20", "upperTolerance": "+0.1"}],
                "machiningOperations": [{"normalizedCode": "TAP", "operation": "tapping"}],
            }
        ],
    )

    summary = build_compact_summary(data, gemini_used=True)

    assert summary["materials"] == ["S235"]
    assert summary["operations"] == ["TAP"]
    assert summary["hole_count"] == 3
    assert summary["tolerance_count"] == 1
