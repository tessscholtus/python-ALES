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

    extra_line = (
        f"\n        ...and {truncated_count} additional cue(s) not listed."
        if truncated_count > 0
        else ""
    )

    section = (
        "      ### Detected Text Cues (OCR - for REFERENCE ONLY)\n\n"
        "      **These are HINTS for WHERE to look; always verify in the PDF image.**\n\n"
        f"{chr(10).join(lines)}{extra_line}"
    )

    return section, truncated_count


def build_assembly_prompt(
    customer_name: str,
    surface_treatment_instructions: str,
) -> str:
    """Build prompt for assembly drawing (BOM-only extraction)."""
    return f"""Extract manufacturing data from this assembly drawing PDF.

This is the MAIN ASSEMBLY: focus ONLY on the BOM table and title block.
Return: material, surfaceTreatment, and bomPartNumbers.
DO NOT extract holes or tolerated dimensions for the assembly itself.

Customer: {customer_name}
Surface treatments:{surface_treatment_instructions}

Call extract_manufacturing_data with the result."""


def build_minimal_prompt(p: PromptInput) -> str:
    """Build the extraction prompt for a single technical drawing PDF."""
    signals = f"\n{p.text_signals_section}\n" if p.text_signals_section else ""

    hole_additions = ""
    if p.prompt_additions and p.prompt_additions.get("holes"):
        hole_additions = "\n  - **Customer-specific rules:**\n" + "\n".join(
            f"    - {rule}" for rule in p.prompt_additions["holes"]
        )

    surface_additions = ""
    if p.prompt_additions and p.prompt_additions.get("surface_treatment"):
        surface_additions = "\n  - **Customer-specific rules:**\n" + "\n".join(
            f"    - {rule}" for rule in p.prompt_additions["surface_treatment"]
        )

    return f"""Extract manufacturing data from this technical drawing PDF.

**EXTRACT 5 THINGS:**
1. Surface treatment (HIGHEST PRIORITY — check BOM first!)
2. Holes (tapped holes + toleranced holes)
3. Toleranced dimensions (lengths only)
4. Material
5. BOM part numbers (if drawing has a BOM table)

**GENERAL RULES:**
- Return 1 item per PDF ({p.images_count} image(s) of same part)
- Extract only what is clearly visible
- Use null/"None" if unsure
- Ignore: plain dimensions without tolerances, metadata

---

**1. SURFACE TREATMENT (CHECK THIS FIRST):**
- Scan the entire BOM table (bottom right) for coating keywords
- Keywords: "coating dynamic", "coating static", "poedercoaten", "verzinken", "parelstralen", "electrogalv"
- The coating may appear in ANY cell of the BOM, not in a dedicated column
- Also check: title block, notes
- Examples: "Verzinkt", "Poedercoaten", "Coating Dynamic", or "None"{surface_additions}

**2. HOLES:**
- Normal: "O20" or "O20 H9" → type=normal, diameter=20, tolerance=H9
- Tapped: "M6" or "4x M6" → type=tapped, threadSize=M6, count=4
- Reamed: pre-drill + final size → type=reamed, notes="Pre-drill O19.5"
- **CRITICAL**: Same hole at MULTIPLE locations → create SEPARATE entries (do not combine unless labeled "2x"){hole_additions}

**3. TOLERANCED DIMENSIONS (lengths only):**
- LENGTHS ONLY — diameter tolerances (e.g. "O40 H7") belong in HOLES
- Extract ONLY from the main drawing views, NOT from BOM or notes
- Dimension must have dimension lines/arrows on the drawing
- Only include dimensions with explicit tolerance symbols: ±, +/−, +0.1/−0.05, +1/0
- Examples:
  - "50±0.2" → dimension=50, upperTolerance=+0.2, lowerTolerance=-0.2
  - "32 +1/0" → dimension=32, upperTolerance=+1, lowerTolerance=0
- Ignore: plain numbers, general tolerance tables, BOM values

**4. MATERIAL:**
- Read the COMPLETE text from the material field — do NOT stop after the first word
- Include thickness if present: "RVS 2 mm", "AISI 304 3mm", "S235 5 mm"
- Do NOT extract generic types: "Sheet", "Plaat", "Tube", "Buis" are NOT materials
- Material field is in BOM table (bottom right) under "Material" or "Materiaal"
- If you see "Sheet" / "Plaat", look in the SAME ROW for the actual material grade

**5. BOM PART NUMBERS (if applicable):**
- Check if this drawing has a BOM table (Bill of Materials, usually bottom-right)
- If YES: extract ALL part numbers from the part number column
- If NO: return empty array []
- Extract ONLY part numbers — not quantities or descriptions
- Ignore the main part number of THIS drawing (title block)
- Example: BOM shows "Pos 1: 10009081" and "Pos 2: MD-21-04683"
  → Return: ["10009081", "MD-21-04683"]

---

**Customer: {p.customer_name}**

Tolerated lengths patterns:
{p.tolerated_length_instructions}

Hole patterns:
{p.hole_instructions}

Surface treatments:
{p.surface_treatment_instructions}

Material patterns:
{p.material_instructions}
{signals}
Call extract_manufacturing_data with the extracted data. Use null for missing fields.
"""
