"""Machine-readable single-PDF entry point for the hybrid orchestrator."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .main import extract_routed_pdf
from .types import ProcessingMetadata
from .xml_writer import build_simple_order_xml

INTEGRATION_SCHEMA_VERSION = "1.0"


def emit(event: str, **payload: Any) -> None:
    print(
        json.dumps(
            {"schema_version": INTEGRATION_SCHEMA_VERSION, "event": event, **payload},
            ensure_ascii=False,
        ),
        flush=True,
    )


def _unique(values: list[str], limit: int = 8) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value or "").strip()
        key = cleaned.casefold()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def build_compact_summary(data, *, gemini_used: bool) -> dict[str, Any]:
    """Return browser-safe headline facts without duplicating the full XML."""

    materials: list[str] = []
    treatments: list[str] = []
    revisions: list[str] = []
    operations: list[str] = []
    risks: list[dict[str, str | None]] = []
    hole_count = 0
    tolerance_count = 0
    for item in data.items or []:
        materials.append(item.material or "")
        treatments.append(item.surface_treatment or "")
        revisions.append(item.revision or "")
        for hole in item.holes or []:
            hole_count += hole.count if hole.count is not None else 1
        tolerance_count += len(item.tolerated_lengths or [])
        for operation in item.machining_operations or []:
            if isinstance(operation, str):
                operations.append(operation)
            else:
                operations.append(operation.normalized_code or operation.operation or "")
        analysis = item.technical_analysis
        if analysis:
            for risk in analysis.risks:
                risks.append(
                    {
                        "severity": risk.severity,
                        "summary": risk.summary,
                    }
                )

    return {
        "mode": "gemini" if gemini_used else "preflight_only",
        "drawing_number": data.drawing_number,
        "drawing_title": data.drawing_title,
        "materials": _unique(materials),
        "surface_treatments": _unique(treatments),
        "revisions": _unique(revisions),
        "operations": _unique(operations),
        "hole_count": hole_count,
        "tolerance_count": tolerance_count,
        "risks": risks[:3],
        "signal_categories": _unique(
            [signal.category for signal in data.detected_signals or []]
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one PDF extraction with JSONL progress events.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--xml", required=True, type=Path)
    parser.add_argument("--part-number", required=True)
    parser.add_argument("--part-id", required=True)
    parser.add_argument("--solid-index", required=True, type=int)
    parser.add_argument("--schema-version", default=INTEGRATION_SCHEMA_VERSION)
    parser.add_argument("--customer", default="base")
    parser.add_argument("--model")
    parser.add_argument("--scan-depth", choices=("auto", "fast", "deep"), default="auto")
    parser.add_argument("--match-strategy", default="")
    parser.add_argument("--match-confidence", type=float)
    parser.add_argument(
        "--gemini-policy",
        choices=("auto", "always", "vision_only", "never"),
        default="auto",
    )
    return parser.parse_args()


async def run(args: argparse.Namespace) -> int:
    package_root = Path(__file__).resolve().parents[1]
    load_dotenv(package_root / ".env")
    pdf_path = args.pdf.resolve()
    xml_path = args.xml.resolve()

    if args.schema_version != INTEGRATION_SCHEMA_VERSION:
        emit(
            "contract_rejected",
            message=(
                f"Unsupported integration schema {args.schema_version}; "
                f"expected {INTEGRATION_SCHEMA_VERSION}"
            ),
        )
        return 4

    if not pdf_path.is_file():
        emit("failed", message=f"PDF not found: {pdf_path}")
        return 2

    def status_callback(event: str, payload: dict[str, Any]) -> None:
        emit(
            event,
            part_id=args.part_id,
            solid_index=args.solid_index,
            part_name=args.part_number,
            pdf_path=str(pdf_path),
            **payload,
        )

    try:
        data, preflight, model, gemini_seconds = await extract_routed_pdf(
            pdf_path,
            customer_id=args.customer,
            scan_depth=args.scan_depth,
            requested_model=args.model,
            expected_part_number=args.part_number,
            status_callback=status_callback,
            gemini_policy=args.gemini_policy,
        )
        gemini_used = model != "none"
        success = any(item.status != "FAILED" for item in data.items)
        data.metadata = ProcessingMetadata(
            totalPDFs=1,
            successfulPDFs=1 if success else 0,
            failedPDFs=0 if success else 1,
            detectedCustomer=args.customer.upper(),
            sourcePDF=pdf_path.name,
            stepPartId=args.part_id,
            stepSolidIndex=args.solid_index,
            stepPartName=args.part_number,
            matchStrategy=args.match_strategy or None,
            matchConfidence=args.match_confidence,
            preflightKind=preflight.kind,
            preflightRoute=preflight.route,
            preflightConfidence=preflight.confidence,
            preflightMs=round(preflight.elapsed_ms, 3),
            geminiModel=model if gemini_used else None,
            geminiSeconds=round(gemini_seconds, 3),
        )
        # Final validation after mapping/post-processing and metadata enrichment.
        data = type(data).model_validate(data.model_dump(by_alias=True))
        xml_path.parent.mkdir(parents=True, exist_ok=True)
        xml_path.write_text(build_simple_order_xml(data), encoding="utf-8")
        emit(
            "completed",
            part_id=args.part_id,
            solid_index=args.solid_index,
            part_name=args.part_number,
            pdf_path=str(pdf_path),
            xml_path=str(xml_path),
            model=model,
            success=success,
            gemini_used=gemini_used,
            requires_review=preflight.route == "manual_review" and not gemini_used,
            summary=build_compact_summary(data, gemini_used=gemini_used),
        )
        return 0 if success else 3
    except Exception as exc:  # noqa: BLE001 - boundary reports a structured failure
        emit(
            "failed",
            part_id=args.part_id,
            solid_index=args.solid_index,
            part_name=args.part_number,
            pdf_path=str(pdf_path),
            error_type=type(exc).__name__,
            message=str(exc),
        )
        return 1


def main() -> int:
    return asyncio.run(run(parse_args()))


if __name__ == "__main__":
    sys.exit(main())
