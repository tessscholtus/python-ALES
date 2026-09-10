"""XML writer for order details with operator warnings."""

from typing import Any, Optional

from .operator_warnings import (
    ExtractedItem,
    escape_xml,
    generate_operator_warnings,
    generate_warning_xml,
)
from .types import OrderDetails, OrderItem


EMPTY_VALUES = {"", "None", "none", "null", "NULL"}


def has_value(value: Any) -> bool:
    """Return True for values worth writing to XML."""

    return value is not None and str(value).strip() not in EMPTY_VALUES


def xml_attrs(**values: Any) -> str:
    """Build escaped XML attributes from non-empty values."""

    attrs = [
        f'{name}="{escape_xml(str(value).strip())}"'
        for name, value in values.items()
        if has_value(value)
    ]
    return " " + " ".join(attrs) if attrs else ""


def append_text_element(lines: list[str], indent: str, tag: str, value: Any) -> None:
    """Append a text node when the value is meaningful."""

    if has_value(value):
        lines.append(f"{indent}<{tag}>{escape_xml(str(value).strip())}</{tag}>")


def append_list_section(
    lines: list[str],
    section_tag: str,
    item_tag: str,
    values: list[Any],
) -> None:
    """Append a simple XML list for technical-analysis notes."""

    meaningful_values = [value for value in values if has_value(value)]
    if not meaningful_values:
        return
    lines.append(f"      <{section_tag}>")
    for value in meaningful_values:
        lines.append(f"        <{item_tag}>{escape_xml(str(value).strip())}</{item_tag}>")
    lines.append(f"      </{section_tag}>")


def operation_value(operation: Any, attribute: str) -> Any:
    """Read a structured operation attribute with dict fallback."""

    if isinstance(operation, dict):
        return operation.get(attribute)
    return getattr(operation, attribute, None)


def write_item_xml(item: OrderItem) -> str:
    """
    Generate XML for a single order item.

    Args:
        item: OrderItem to convert to XML

    Returns:
        XML string for the item
    """
    lines: list[str] = []
    lines.append("    <Item>")

    if item.part_number:
        lines.append(f"      <PartNumber>{escape_xml(item.part_number)}</PartNumber>")

    # If this is a failed item, only show PartNumber and Status
    if item.status == "FAILED":
        lines.append("      <Status>FAILED</Status>")
        lines.append("    </Item>")
        return "\n".join(lines)

    lines.append(f"      <Description>{escape_xml(item.description or '')}</Description>")

    if item.quantity is not None:
        lines.append(f"      <Quantity>{item.quantity}</Quantity>")

    if item.material:
        lines.append(f"      <Material>{escape_xml(item.material)}</Material>")

    if item.surface_treatment:
        lines.append(f"      <SurfaceTreatment>{escape_xml(item.surface_treatment)}</SurfaceTreatment>")

    if item.holes:
        lines.append("      <Holes>")
        for hole in item.holes:
            attrs = xml_attrs(
                count=hole.count,
                normalizedCode=hole.normalized_code,
                type=hole.type,
                operation=hole.operation,
                diameter=hole.diameter,
                threadSize=hole.thread_size,
                tolerance=hole.tolerance,
                upperTolerance=hole.upper_tolerance,
                lowerTolerance=hole.lower_tolerance,
                cuttingSize=hole.cutting_size,
                depth=hole.depth,
                location=hole.location,
            )
            child_lines: list[str] = []
            append_text_element(child_lines, "          ", "Evidence", hole.evidence)
            append_text_element(child_lines, "          ", "Notes", hole.notes)
            if child_lines:
                lines.append(f"        <Hole{attrs}>")
                lines.extend(child_lines)
                lines.append("        </Hole>")
            else:
                lines.append(f"        <Hole{attrs}/>")
        lines.append("      </Holes>")

    # Tolerated Lengths
    if item.tolerated_lengths:
        lines.append("      <ToleratedLengths>")
        for t in item.tolerated_lengths:
            lines.append("        <ToleratedLength>")
            if t.dimension:
                lines.append(f"          <Dimension>{escape_xml(t.dimension)}</Dimension>")
            if t.tolerance_type:
                lines.append(f"          <Type>{escape_xml(t.tolerance_type)}</Type>")
            if t.upper_tolerance:
                lines.append(f"          <Upper>{escape_xml(t.upper_tolerance)}</Upper>")
            if t.lower_tolerance:
                lines.append(f"          <Lower>{escape_xml(t.lower_tolerance)}</Lower>")
            if t.notes:
                lines.append(f"          <Notes>{escape_xml(t.notes)}</Notes>")
            if t.evidence:
                lines.append(f"          <Evidence>{escape_xml(t.evidence)}</Evidence>")
            lines.append("        </ToleratedLength>")
        lines.append("      </ToleratedLengths>")

    if item.machining_operations:
        lines.append("      <MachiningOperations>")
        for operation in item.machining_operations:
            if isinstance(operation, str):
                lines.append(
                    f"        <Operation>{escape_xml(operation.strip())}</Operation>"
                )
                continue
            attrs = xml_attrs(
                normalizedCode=operation.normalized_code,
                operation=operation.operation,
                category=operation.category,
                targetField=operation.target_field,
                count=operation.count,
                diameter=operation.diameter,
                threadSize=operation.thread_size,
                tolerance=operation.tolerance,
                cuttingSize=operation.cutting_size,
                relatedFeature=operation.related_feature,
            )
            child_lines = []
            append_text_element(child_lines, "          ", "Evidence", operation.evidence)
            append_text_element(child_lines, "          ", "Notes", operation.notes)
            if child_lines:
                lines.append(f"        <Operation{attrs}>")
                lines.extend(child_lines)
                lines.append("        </Operation>")
            else:
                lines.append(f"        <Operation{attrs}/>")
        lines.append("      </MachiningOperations>")

    if item.technical_analysis:
        analysis = item.technical_analysis
        lines.append("      <TechnicalAnalysis>")
        append_text_element(
            lines,
            "        ",
            "ManufacturabilityStatus",
            analysis.manufacturability_status,
        )
        append_text_element(lines, "        ", "Conclusion", analysis.conclusion)
        append_list_section(
            lines, "PositiveChecks", "Check", analysis.positive_checks
        )
        if analysis.risks:
            lines.append("        <Risks>")
            for risk in analysis.risks:
                attrs = xml_attrs(severity=risk.severity, category=risk.category)
                child_lines = []
                append_text_element(child_lines, "            ", "Summary", risk.summary)
                append_text_element(child_lines, "            ", "Evidence", risk.evidence)
                if child_lines:
                    lines.append(f"          <Risk{attrs}>")
                    lines.extend(child_lines)
                    lines.append("          </Risk>")
                else:
                    lines.append(f"          <Risk{attrs}/>")
            lines.append("        </Risks>")
        append_list_section(lines, "WeldingNotes", "Note", analysis.welding_notes)
        append_list_section(
            lines, "CoatingRequirements", "Requirement", analysis.coating_requirements
        )
        append_list_section(lines, "RevisionNotes", "Note", analysis.revision_notes)
        append_list_section(
            lines, "GdtRequirements", "Requirement", analysis.gdt_requirements
        )
        append_list_section(
            lines, "GeneralTolerances", "Tolerance", analysis.general_tolerances
        )
        append_list_section(
            lines, "AssemblyDimensions", "Dimension", analysis.assembly_dimensions
        )
        lines.append("      </TechnicalAnalysis>")

    # Operator warnings (tap holes, toleranced holes, critical dimensions)
    extracted_item = ExtractedItem(
        part_number=item.part_number,
        description=item.description,
        material=item.material,
        surface_treatment=item.surface_treatment,
        holes=[
            {
                "type": h.type or "normal",
                "threadSize": h.thread_size,
                "diameter": h.diameter,
                "tolerance": h.tolerance,
                "upperTolerance": h.upper_tolerance,
                "lowerTolerance": h.lower_tolerance,
                "count": h.count,
            }
            for h in (item.holes or [])
        ],
        critical_lengths=[
            {
                "dimension": t.dimension or "",
                "toleranceType": t.tolerance_type,
                "upperTolerance": t.upper_tolerance,
                "lowerTolerance": t.lower_tolerance,
                "note": t.notes,
            }
            for t in (item.tolerated_lengths or [])
        ],
    )

    warnings = generate_operator_warnings(extracted_item)
    warnings_xml = generate_warning_xml(warnings)
    if warnings_xml:
        lines.append(warnings_xml.rstrip())

    lines.append("    </Item>")
    return "\n".join(lines)


def build_simple_order_xml(data: OrderDetails) -> str:
    """
    Build XML string for order details.

    Args:
        data: OrderDetails to convert to XML

    Returns:
        Complete XML string
    """
    parts: list[str] = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append("<Order>")

    # Add metadata section if present
    if data.metadata:
        parts.append("  <Metadata>")
        parts.append(f"    <TotalPDFs>{data.metadata.total_pdfs}</TotalPDFs>")
        parts.append(f"    <SuccessfulPDFs>{data.metadata.successful_pdfs}</SuccessfulPDFs>")
        parts.append(f"    <FailedPDFs>{data.metadata.failed_pdfs}</FailedPDFs>")
        if data.metadata.detected_customer:
            parts.append(f"    <DetectedCustomer>{escape_xml(data.metadata.detected_customer)}</DetectedCustomer>")
        append_text_element(parts, "    ", "SourcePDF", data.metadata.source_pdf)
        append_text_element(parts, "    ", "StepPartId", data.metadata.step_part_id)
        append_text_element(parts, "    ", "StepSolidIndex", data.metadata.step_solid_index)
        append_text_element(parts, "    ", "StepPartName", data.metadata.step_part_name)
        append_text_element(parts, "    ", "MatchStrategy", data.metadata.match_strategy)
        append_text_element(parts, "    ", "MatchConfidence", data.metadata.match_confidence)
        append_text_element(parts, "    ", "PreflightKind", data.metadata.preflight_kind)
        append_text_element(parts, "    ", "PreflightRoute", data.metadata.preflight_route)
        append_text_element(parts, "    ", "PreflightConfidence", data.metadata.preflight_confidence)
        append_text_element(parts, "    ", "PreflightMs", data.metadata.preflight_ms)
        append_text_element(parts, "    ", "GeminiModel", data.metadata.gemini_model)
        append_text_element(parts, "    ", "GeminiSeconds", data.metadata.gemini_seconds)
        parts.append("  </Metadata>")

    if data.drawing_number:
        parts.append(f"  <DrawingNumber>{escape_xml(data.drawing_number)}</DrawingNumber>")

    if data.drawing_title:
        parts.append(f"  <DrawingTitle>{escape_xml(data.drawing_title)}</DrawingTitle>")

    if data.customer_name:
        parts.append(f"  <Customer>{escape_xml(data.customer_name)}</Customer>")

    if data.detected_signals:
        parts.append("  <DetectedSignals>")
        for signal in data.detected_signals:
            attrs = xml_attrs(
                category=signal.category,
                rawValue=signal.raw_value,
                page=signal.page,
                source=signal.source,
            )
            child_lines: list[str] = []
            append_text_element(child_lines, "      ", "Context", signal.context)
            append_text_element(child_lines, "      ", "Note", signal.note)
            if child_lines:
                parts.append(f"    <Signal{attrs}>")
                parts.extend(child_lines)
                parts.append("    </Signal>")
            else:
                parts.append(f"    <Signal{attrs}/>")
        parts.append("  </DetectedSignals>")

    parts.append("  <Items>")
    for item in data.items or []:
        parts.append(write_item_xml(item))
    parts.append("  </Items>")

    parts.append("</Order>")
    return "\n".join(parts)
