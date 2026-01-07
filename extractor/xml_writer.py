"""XML writer for order details with operator warnings."""

from typing import Optional

from .operator_warnings import (
    ExtractedItem,
    escape_xml,
    generate_operator_warnings,
    generate_warning_xml,
)
from .types import OrderDetails, OrderItem


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

    lines.append(f"      <Description>{escape_xml(item.description or '')}</Description>")

    if item.quantity is not None:
        lines.append(f"      <Quantity>{item.quantity}</Quantity>")

    if item.material:
        lines.append(f"      <Material>{escape_xml(item.material)}</Material>")

    if item.surface_treatment:
        lines.append(f"      <SurfaceTreatment>{escape_xml(item.surface_treatment)}</SurfaceTreatment>")

    # Holes
    if item.holes:
        lines.append("      <Holes>")
        for hole in item.holes:
            attrs = []
            if hole.count is not None:
                attrs.append(f'count="{hole.count}"')
            if hole.type:
                attrs.append(f'type="{escape_xml(hole.type)}"')
            if hole.diameter:
                attrs.append(f'diameter="{escape_xml(hole.diameter)}"')
            if hole.thread_size:
                attrs.append(f'threadSize="{escape_xml(hole.thread_size)}"')
            if hole.tolerance:
                attrs.append(f'tolerance="{escape_xml(hole.tolerance)}"')

            attrs_str = " ".join(attrs)
            lines.append(f"        <Hole {attrs_str}/>")
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
            lines.append("        </ToleratedLength>")
        lines.append("      </ToleratedLengths>")

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

    if data.drawing_number:
        parts.append(f"  <DrawingNumber>{escape_xml(data.drawing_number)}</DrawingNumber>")

    if data.drawing_title:
        parts.append(f"  <DrawingTitle>{escape_xml(data.drawing_title)}</DrawingTitle>")

    if data.customer_name:
        parts.append(f"  <Customer>{escape_xml(data.customer_name)}</Customer>")

    parts.append("  <Items>")
    for item in data.items or []:
        parts.append(write_item_xml(item))
    parts.append("  </Items>")

    parts.append("</Order>")
    return "\n".join(parts)
