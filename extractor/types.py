"""Type definitions for PDF extraction."""

from typing import Optional, Literal
from pydantic import BaseModel, Field

from .constants import DEFAULT_GEMINI_MODEL


class HoleDetails(BaseModel):
    """Details of a hole in the drawing."""
    count: Optional[int] = None
    type: Optional[str] = None  # Was Literal, but LLM may return other values like "threaded", "drilled"
    diameter: Optional[str] = None
    thread_size: Optional[str] = Field(None, alias="threadSize")
    tolerance: Optional[str] = None
    depth: Optional[str] = None
    location: Optional[str] = None
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


class OrderItem(BaseModel):
    """Single part extracted from a PDF."""
    part_number: Optional[str] = Field(None, alias="partNumber")
    holes: Optional[list[HoleDetails]] = None
    tolerated_lengths: Optional[list[ToleratedLength]] = Field(
        None, alias="toleratedLengths"
    )
    surface_treatment: Optional[str] = Field(None, alias="surfaceTreatment")
    material: Optional[str] = None
    notes: Optional[str] = None
    bom_part_numbers: Optional[list[str]] = Field(None, alias="bomPartNumbers")
    # Extra fields for XML output
    description: Optional[str] = None
    quantity: Optional[int] = None

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

    class Config:
        populate_by_name = True


class ExtractionOptions(BaseModel):
    """Options for PDF extraction."""
    customer_id: str = Field(default="elten", alias="customerId")
    text_signals: list[TextSignal] = Field(default_factory=list, alias="textSignals")
    pdf_filename: Optional[str] = Field(None, alias="pdfFilename")
    model: str = DEFAULT_GEMINI_MODEL
    is_assembly: bool = Field(default=False, alias="isAssembly")

    class Config:
        populate_by_name = True


class CustomerDetectionResult(BaseModel):
    """Result of customer detection."""
    customer: Literal["elten", "rademaker", "base", "unknown"]
    confidence: Literal["high", "medium", "low"]
    reason: str
