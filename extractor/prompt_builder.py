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


def build_technical_assembly_prompt(
    customer_name: str,
    surface_treatment_instructions: str,
) -> str:
    """Build the structured vision prompt for a main assembly drawing."""

    return f"""Analyse this MAIN ASSEMBLY technical drawing for manufacturing.

Read the visible drawing itself, including title block, BOM, dimensions, GD&T,
notes, welding instructions and surface-treatment fields. The PDF may contain
vector outlines without an extractable text layer, so rely on the rendered
visual content.

Return exactly one item and populate:
- partNumber, revision, description, material and surfaceTreatment;
- bomItems with position, partNumber, quantity, description and material;
- bomPartNumbers with the part numbers from bomItems;
- holes, toleratedLengths and machiningOperations only when explicitly shown;
- technicalAnalysis with manufacturabilityStatus, a short conclusion,
  positiveChecks, risks, weldingNotes, coatingRequirements, revisionNotes,
  gdtRequirements, generalTolerances and assemblyDimensions.

Rules:
- Use only evidence visible in this PDF. Do not invent missing specifications.
- Put unclear or missing production information in risks with severity
  blocker, warning or info.
- Preserve exact values and units in evidence strings.
- Check arithmetic dimension chains only when every operand is visible.
- Do not claim that STEP or ERP agrees unless those sources are supplied.
- If coating, welding quality, revision or inspection interpretation is
  incomplete, report that explicitly instead of guessing.
- Keep every list concise and remove duplicates.

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

**EXTRACT THESE MANUFACTURING FEATURES:**
1. Surface treatment (HIGHEST PRIORITY - check BOM first!)
2. Holes and hole operations (drilled, tapped, reamed, countersunk, fitted)
3. Toleranced dimensions and toleranced holes
4. Material
5. BOM part numbers (if drawing has a BOM table)
6. Machining operations and manufacturing notes
7. Mapping signals for ERP/calculation review

**RULES:**
- Return 1 item per PDF ({p.images_count} image(s) of same part)
- Extract only what's clearly visible
- Use null/"None" if unsure
- Ignore: general dimensions, metadata
- Never hide a concrete hole or machining operation only in technicalAnalysis.
  Also put it in holes and/or machiningOperations with evidence.
- For every concrete manufacturing term, also add a detectedSignals entry with
  category = the normalized code and rawValue = the exact visible term.

**NORMALIZED CODES FOR MAPPING:**
- DRILL: normal drilled/cut holes such as O12.5 or simple clearance holes
- TAP: tapped/threaded holes such as M6, 4x M8, thread, tapped
- REAM: reamed holes, ruiming/ruimen, reaming, H7/H8/H9 with reaming note
- FIT_HOLE: hole fit/tolerance such as H7, H8, H9, F7, +0.6/+0.1 on a hole
- COUNTERSINK: countersunk/verzonken holes
- COUNTERBORE: counterbore/spotface/cilinderverzinking
- MILL: milling/frezen/freesbewerking, pockets, slots, milled surfaces
- TURN: turning/draaien/draaiwerk
- BEND: bending/zetten/kanten
- WELD: welding/lassen
- DEBURR: break sharp edges, ontbramen, sharp edges removed
- SURFACE_TREATMENT: coating, galvanizing, blasting, passivating, painting
- ROUGHNESS: Ra/Rz surface roughness requirements
- BOM: BOM row or referenced child part
- MATERIAL: material grade, thickness or stock specification

**1. SURFACE TREATMENT (CHECK THIS FIRST!):**
- **CRITICAL**: Scan the entire BOM table (bottom right) for coating keywords
- Keywords to look for: "coating dynamic", "coating static", "poedercoaten", "verzinken", "parelstralen", "electrogalv"
- The coating may appear in ANY cell of the BOM, not in a specific column
- Check: title block, BOM, notes
- Examples: "Verzinkt", "Poedercoaten", "Coating Dynamic", or "None"{surface_additions}

**2. HOLES:**
- Every visible hole callout must create a holes row. Do not skip ordinary
  drilled/cut holes just because STEP may also contain geometry.
- Normal: "O20" -> normalizedCode=DRILL, type=normal, diameter=20
- Tapped: "M6" or "4x M6" -> normalizedCode=TAP, type=tapped, threadSize=M6, count=4
- Reamed: "Reaming O20H9 / Cutting Size O19.5" -> normalizedCode=REAM,
  type=reamed, diameter=20, tolerance=H9, cuttingSize=19.5,
  operation=reaming
- Fitted/toleranced hole: "O40 +0.6/+0.1" -> normalizedCode=FIT_HOLE,
  type=normal, diameter=40, upperTolerance=+0.6, lowerTolerance=+0.1
- Countersunk: "verzonken", "countersink", "DIN 74" -> normalizedCode=COUNTERSINK
- Plain holes that have a visible diameter but no operation note still matter
  for PDF/STEP comparison and must be returned as DRILL.
- Use count=1 for each separate visible location when no explicit count is
  printed. Duplicate rows with the same diameter/fit may later be merged.
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
- If the title block/base material table has separate fields such as
  Material=S235, type=Sheet, Height=600, Width=117 and Thickness=12, extract
  material="S235" and put the full stock description in notes.
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

**6. MACHINING OPERATIONS AND MANUFACTURING NOTES:**
- Populate machiningOperations for every visible operation-relevant note, even
  when the same information is also represented in holes.
- Use the normalized codes above. Set targetField="Borengaten" for DRILL, TAP,
  REAM, FIT_HOLE, COUNTERSINK and COUNTERBORE.
- Examples:
  - "M6(4x)" -> normalizedCode=TAP, operation=tapping, count=4,
    threadSize=M6, targetField=Borengaten
  - "Reaming O20H9 / Cutting Size O19.5" -> normalizedCode=REAM,
    operation=reaming, diameter=20, tolerance=H9, cuttingSize=19.5,
    targetField=Borengaten
  - "Break sharp edges" -> normalizedCode=DEBURR, operation=deburring
- Include exact evidence text for every operation.

**7. DETECTED SIGNALS FOR MAPPING:**
- For each hole, operation, surface treatment, roughness, material, BOM part or
  special tolerance, add detectedSignals with:
  category=<normalized code>, rawValue=<exact visible term>, source="vision".
- These signals are used for PdfTermTbl and PdfTermMappingTbl grouping.

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
