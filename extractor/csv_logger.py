"""CSV logger for daily PDF extraction logs."""

import csv
from datetime import datetime
from pathlib import Path


LOG_FIELDS = [
    "Timestamp",
    "Order",
    "PDF",
    "Status",
    "Time(s)",
    "Preflight(ms)",
    "PDFKind",
    "Route",
    "Model",
    "AI(s)",
    "Error",
    "Customer",
]


def get_log_file_path() -> Path:
    """Get the path for today's log file."""
    today = datetime.now().strftime("%Y-%m-%d")
    # Log file in logs/ directory relative to the extractor package
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"pdf_extractor_log_{today}.csv"
    if log_file.exists():
        try:
            with open(log_file, newline="", encoding="utf-8") as stream:
                existing_header = next(csv.reader(stream), [])
            if existing_header and existing_header != LOG_FIELDS:
                return log_dir / f"pdf_extractor_log_{today}_v2.csv"
        except OSError:
            pass
    return log_file


def log_pdf_result(
    order_name: str,
    pdf_name: str,
    status: str,
    elapsed_time: float,
    error: str,
    customer: str,
    preflight_ms: float | None = None,
    pdf_kind: str = "",
    route: str = "",
    model: str = "",
    ai_time: float | None = None,
) -> None:
    """
    Log a single PDF extraction result to the daily CSV log.

    Args:
        order_name: Name of the order/folder being processed
        pdf_name: Name of the PDF file (without extension)
        status: "SUCCESS" or "FAILED"
        elapsed_time: Time taken to process the PDF in seconds
        error: Error message if failed, empty string if successful
        customer: Explicit customer configuration
        preflight_ms: Duration of the structural preflight
        pdf_kind: Structural PDF classification
        route: Route selected by the preflight
        model: Gemini model used, or "none" for skipped PDFs
        ai_time: Time spent in Gemini calls
    """
    log_file = get_log_file_path()
    file_exists = log_file.exists()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)

        # Write header if file is new
        if not file_exists:
            writer.writeheader()

        # Write the log entry
        writer.writerow(
            {
                "Timestamp": timestamp,
                "Order": order_name,
                "PDF": pdf_name,
                "Status": status,
                "Time(s)": f"{elapsed_time:.2f}",
                "Preflight(ms)": "" if preflight_ms is None else f"{preflight_ms:.2f}",
                "PDFKind": pdf_kind,
                "Route": route,
                "Model": model,
                "AI(s)": "" if ai_time is None else f"{ai_time:.2f}",
                "Error": error,
                "Customer": customer,
            }
        )
