"""Prompt builder for Gemini API extraction."""

from dataclasses import dataclass
from typing import Optional

from .types import TextSignal


@dataclass
class PromptInput:
    """Input for building the extraction prompt."""
    customer_name: str
    images_count: int
    tolerated_length_instructions: str
    hole_instructions: str
    surface_treatment_instructions: str
    material_instructions: str
    text_signals_section: Optional[str] = None
    prompt_additions: Optional[dict[str, list[str]]] = None


def build_text_signals_section(
    signals: list[TextSignal],
    max_entries: int = 5,
) -> tuple[str, int]:
    """
    Build the text signals section for the prompt.

    Returns:
        Tuple of (section_text, truncated_count)
    """
    if not signals:
        return (
            "      ### Detected Text Cues (OCR - for REFERENCE ONLY)\n"
            "        - No OCR matches found. Extract information ONLY from what you SEE in the actual PDF images.",
            0,
        )

    limited_signals = signals[:max_entries]
    truncated_count = len(signals) - len(limited_signals)

    lines = []
    for i, s in enumerate(limited_signals):
        ctx = (s.context or "").replace("\n", " ").strip()
        short_ctx = f"{ctx[:77]}..." if len(ctx) > 80 else ctx
        ctx_part = f' | context: "{short_ctx}"' if short_ctx else ""
        lines.append(
            f"        {i + 1}. [{s.category.upper()}] {s.raw_value} "
            f"(page {s.page}, {s.source}){ctx_part}"
        )

    extra_line = f"\n        ...and {truncated_count} additional cue(s) not listed." if truncated_count > 0 else ""

    section = f"""      ### Detected Text Cues (OCR - for REFERENCE ONLY)

      **These are HINTS for WHERE to look; always verify in the PDF image.**

{chr(10).join(lines)}{extra_line}"""

    return section, truncated_count


def build_assembly_prompt(
    customer_name: str,
    surface_treatment_instructions: str,
) -> str:
    """Build prompt for assembly drawing (BOM-only extraction)."""
    return f"""Extract manufacturing data from technical drawing PDF.

This PDF is the MAIN ASSEMBLY: focus ONLY on the BOM + title block.
Return: material, surfaceTreatment, and bomPartNumbers.
DO NOT extract holes or tolerated dimensions for the assembly.

Customer: {customer_name}
Surface treatments:{surface_treatment_instructions}

Return valid JSON per schema."""


def build_minimal_prompt(p: PromptInput) -> str:
    """Build the minimal extraction prompt."""
    signals = f"\n{p.text_signals_section}\n" if p.text_signals_section else ""

    # Build customer-specific additions for holes section
    hole_additions = ""
    if p.prompt_additions and p.prompt_additions.get("holes"):
        hole_additions = "\n  - **Customer-specific rules:**\n" + "\n".join(
            f"    - {rule}" for rule in p.prompt_additions["holes"]
        )

    # Build customer-specific additions for surface treatment section
    surface_additions = ""
    if p.prompt_additions and p.prompt_additions.get("surface_treatment"):
        surface_additions = "\n  - **Customer-specific rules:**\n" + "\n".join(
            f"    - {rule}" for rule in p.prompt_additions["surface_treatment"]
        )

    return f"""Extract manufacturing data from technical drawing PDF.

**EXTRACT 4 THINGS:**
1. Surface treatment (HIGHEST PRIORITY - check BOM first!)
2. Holes (tapgaten + toleranced holes)
3. Toleranced dimensions
4. Material
5. BOM part numbers (if drawing has a BOM table)

**RULES:**
- Return 1 item per PDF ({p.images_count} image(s) of same part)
- Extract only what's clearly visible
- Use null/"None" if unsure
- Ignore: general dimensions, metadata

**1. SURFACE TREATMENT (CHECK THIS FIRST!):**
- **CRITICAL**: Scan the entire BOM table (bottom right) for coating keywords
- Keywords to look for: "coating dynamic", "coating static", "poedercoaten", "verzinken", "parelstralen", "electrogalv"
- The coating may appear in ANY cell of the BOM, not in a specific column
- Check: title block, BOM, notes
- Examples: "Verzinkt", "Poedercoaten", "Coating Dynamic", or "None"{surface_additions}

**2. HOLES:**
- Normal: "O20" or "O20 H9" -> type=normal, diameter=20, tolerance=H9
- Tapped: "M6" or "4x M6" -> type=tapped, threadSize=M6, count=4
- Reamed: pre-drill + final -> type=reamed, notes="Pre-drill O19.5"
- **CRITICAL**: Same hole at MULTIPLE locations -> create SEPARATE entries for EACH (don't combine unless labeled "2x"){hole_additions}

**3. TOLERANCED DIMENSIONS (Lengths only):**
- **CRITICAL**: For LENGTHS ONLY. Tolerances on diameters (e.g., "O40 H7") belong in the HOLES section.
- **CRITICAL**: Only extract dimensions from the MAIN DRAWING (technical views), NOT from BOM or notes
- **CRITICAL**: Dimension must have dimension lines/arrows on the drawing
- Only dimensions with explicit tolerance symbols: +/-, +/-, +0.1/-0.05, +1/0
- Examples: "50+/-0.2" -> dimension=50, upperTolerance=+0.2, lowerTolerance=-0.2
- Examples: "32 +1" or "32 +1/0" -> dimension=32, upperTolerance=+1, lowerTolerance=0
- Ignore: plain numbers, general tolerance tables, BOM values, random numbers without dimension indicators

**4. MATERIAL:**
- **CRITICAL**: Read the COMPLETE ENTIRE text from material field - do NOT stop after first word!
- **INCLUDE THICKNESS**: If material field says "RVS 2 mm" or "RVS 3mm", extract ALL of it!
- **WRONG**: Extracting only "RVS" when the field says "RVS 2 mm" - you MUST read the full field!
- **CORRECT**: "RVS 2 mm", "AISI 304 3mm", "S235 5 mm"
- **DO NOT extract generic types**: "Sheet", "Plaat", "Tube", "Buis" are NOT materials!
- Material field is in BOM table (bottom right) under 'Material' or 'Materiaal' column
- If you see "Sheet" or "Plaat", look in the SAME ROW for the actual material number
- Use patterns below for more customer-specific guidance.

**5. BOM PART NUMBERS (if applicable):**
- **Check if this drawing has a BOM table** (Bill of Materials, usually bottom-right)
- **If YES**: Extract ALL part numbers from the BOM's part number column
- **If NO**: Return empty array []
- BOM typically has columns: Pos, Part Number, Qty, Description
- **Extract ONLY the part numbers** (not quantities, not descriptions)
- Example: If BOM shows "Pos 1: 10009081, Qty 1" and "Pos 2: MD-21-04683, Qty 1"
  -> Return: ["10009081", "MD-21-04683"]
- **Ignore the main part number** (the part number of THIS drawing in title block)
- Only extract part numbers that refer to OTHER parts/components

**Customer: {p.customer_name}**

Tolerated Lengths patterns:
{p.tolerated_length_instructions}

Hole patterns:
{p.hole_instructions}

Surface treatments:
{p.surface_treatment_instructions}

Material patterns:
{p.material_instructions}
{signals}

Return valid JSON per schema. Use null for missing data.
"""
