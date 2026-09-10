"""Type definitions for PDF extraction."""

from typing import Literal, Optional
from pydantic import BaseModel, Field

from .constants import DEFAULT_GEMINI_MODEL


class HoleDetails(BaseModel):
    """Details of a hole in the drawing."""
    count: Optional[int] = None
    normalized_code: Optional[str] = Field(None, alias="normalizedCode")
    type: Optional[str] = None  # Was Literal, but LLM may return other values like "threaded", "drilled"
    operation: Optional[str] = None
    diameter: Optional[str] = None
    thread_size: Optional[str] = Field(None, alias="threadSize")
    tolerance: Optional[str] = None
    upper_tolerance: Optional[str] = Field(None, alias="upperTolerance")
    lower_tolerance: Optional[str] = Field(None, alias="lowerTolerance")
    cutting_size: Optional[str] = Field(None, alias="cuttingSize")
    depth: Optional[str] = None
    location: Optional[str] = None
    evidence: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        populate_by_name = True


class ToleratedLength(BaseModel):
    """A dimension with explicit tolerance."""
    dimension: Optional[str] = None
    notes: Optional[str] = None
    tolerance_type: Optional[str] = Field(None, alias="toleranceType")
    upper_tolerance: Optional[str] = Field(None, alias="upperTolerance")
    lower_tolerance: Optional[str] = Field(None, alias="lowerTolerance")
    related_feature: Optional[str] = Field(None, alias="relatedFeature")
    evidence: Optional[str] = None

    class Config:
        populate_by_name = True


class TextSignal(BaseModel):
    """OCR hint (deprecated, kept for reference)."""
    category: str  # Was Literal, but models may return other values
    raw_value: str = Field(default="", alias="rawValue")
    page: Optional[int] = None
    source: Optional[str] = None
    context: Optional[str] = None
    note: Optional[str] = None

    class Config:
        populate_by_name = True


class BomItem(BaseModel):
    """One structured row from a drawing BOM."""

    position: Optional[str] = None
    part_number: Optional[str] = Field(None, alias="partNumber")
    quantity: Optional[int] = None
    description: Optional[str] = None
    material: Optional[str] = None

    class Config:
        populate_by_name = True


class MachiningOperation(BaseModel):
    """A visible manufacturing operation or operation-relevant PDF signal."""

    normalized_code: Optional[str] = Field(None, alias="normalizedCode")
    operation: Optional[str] = None
    category: Optional[str] = None
    target_field: Optional[str] = Field(None, alias="targetField")
    count: Optional[int] = None
    diameter: Optional[str] = None
    thread_size: Optional[str] = Field(None, alias="threadSize")
    tolerance: Optional[str] = None
    cutting_size: Optional[str] = Field(None, alias="cuttingSize")
    related_feature: Optional[str] = Field(None, alias="relatedFeature")
    evidence: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        populate_by_name = True


class TechnicalRisk(BaseModel):
    """One evidence-backed manufacturability concern."""

    severity: Optional[str] = None
    category: Optional[str] = None
    summary: str
    evidence: Optional[str] = None

    class Config:
        populate_by_name = True


class TechnicalAnalysis(BaseModel):
    """Structured technical assessment, mainly used for assemblies."""

    manufacturability_status: Optional[str] = Field(
        None, alias="manufacturabilityStatus"
    )
    conclusion: Optional[str] = None
    positive_checks: list[str] = Field(default_factory=list, alias="positiveChecks")
    risks: list[TechnicalRisk] = Field(default_factory=list)
    welding_notes: list[str] = Field(default_factory=list, alias="weldingNotes")
    coating_requirements: list[str] = Field(
        default_factory=list, alias="coatingRequirements"
    )
    revision_notes: list[str] = Field(default_factory=list, alias="revisionNotes")
    gdt_requirements: list[str] = Field(default_factory=list, alias="gdtRequirements")
    general_tolerances: list[str] = Field(
        default_factory=list, alias="generalTolerances"
    )
    assembly_dimensions: list[str] = Field(
        default_factory=list, alias="assemblyDimensions"
    )

    class Config:
        populate_by_name = True


class OrderItem(BaseModel):
    """Single part extracted from a PDF."""
    part_number: Optional[str] = Field(None, alias="partNumber")
    holes: Optional[list[HoleDetails]] = None
    tolerated_lengths: Optional[list[ToleratedLength]] = Field(
        None, alias="toleratedLengths"
    )
    surface_treatment: Optional[str] = Field(None, alias="surfaceTreatment")
    material: Optional[str] = None
    revision: Optional[str] = None
    notes: Optional[str] = None
    bom_part_numbers: Optional[list[str]] = Field(None, alias="bomPartNumbers")
    bom_items: Optional[list[BomItem]] = Field(None, alias="bomItems")
    machining_operations: Optional[list[MachiningOperation | str]] = Field(
        None, alias="machiningOperations"
    )
    technical_analysis: Optional[TechnicalAnalysis] = Field(
        None, alias="technicalAnalysis"
    )
    # Extra fields for XML output
    description: Optional[str] = None
    quantity: Optional[int] = None
    # Status field for failed extractions
    status: Optional[Literal["SUCCESS", "FAILED"]] = None

    class Config:
        populate_by_name = True


class ProcessingMetadata(BaseModel):
    """Metadata about the batch processing run."""
    total_pdfs: int = Field(alias="totalPDFs")
    successful_pdfs: int = Field(alias="successfulPDFs")
    failed_pdfs: int = Field(alias="failedPDFs")
    detected_customer: Optional[str] = Field(None, alias="detectedCustomer")
    source_pdf: Optional[str] = Field(None, alias="sourcePDF")
    step_part_id: Optional[str] = Field(None, alias="stepPartId")
    step_solid_index: Optional[int] = Field(None, alias="stepSolidIndex")
    step_part_name: Optional[str] = Field(None, alias="stepPartName")
    match_strategy: Optional[str] = Field(None, alias="matchStrategy")
    match_confidence: Optional[float] = Field(None, alias="matchConfidence")
    preflight_kind: Optional[str] = Field(None, alias="preflightKind")
    preflight_route: Optional[str] = Field(None, alias="preflightRoute")
    preflight_confidence: Optional[float] = Field(None, alias="preflightConfidence")
    preflight_ms: Optional[float] = Field(None, alias="preflightMs")
    gemini_model: Optional[str] = Field(None, alias="geminiModel")
    gemini_seconds: Optional[float] = Field(None, alias="geminiSeconds")

    class Config:
        populate_by_name = True


class OrderDetails(BaseModel):
    """Top-level extraction result."""
    items: list[OrderItem] = []
    detected_signals: Optional[list[TextSignal]] = Field(
        None, alias="detectedSignals"
    )
    # Extra fields for XML output
    drawing_number: Optional[str] = Field(None, alias="drawingNumber")
    drawing_title: Optional[str] = Field(None, alias="drawingTitle")
    customer_name: Optional[str] = Field(None, alias="customerName")
    # Processing metadata
    metadata: Optional[ProcessingMetadata] = None

    class Config:
        populate_by_name = True


class ExtractionOptions(BaseModel):
    """Options for PDF extraction."""
    customer_id: str = Field(default="elten", alias="customerId")
    text_signals: list[TextSignal] = Field(default_factory=list, alias="textSignals")
    pdf_filename: Optional[str] = Field(None, alias="pdfFilename")
    expected_part_number: Optional[str] = Field(None, alias="expectedPartNumber")
    model: str = DEFAULT_GEMINI_MODEL
    is_assembly: bool = Field(default=False, alias="isAssembly")
    technical_analysis: bool = Field(default=False, alias="technicalAnalysis")

    class Config:
        populate_by_name = True


class CustomerDetectionResult(BaseModel):
    """Result of customer detection."""
    customer: Literal["elten", "rademaker", "base", "unknown"]
    confidence: Literal["high", "medium", "low"]
    reason: str
