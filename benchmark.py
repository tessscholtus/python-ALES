#!/usr/bin/env python3
"""
Benchmark script to compare Gemini models for PDF extraction.

Compares: gemini-2.5-pro vs gemini-3.0-flash-preview
Measures: Speed, Success rate, Output consistency
"""

import asyncio
import time
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Import the extractor
import sys
sys.path.insert(0, str(Path(__file__).parent))

from extractor.main import extract_batch
from extractor.gemini_service import read_pdf_as_base64

console = Console()

MODELS = [
    "gemini-3-flash-preview",  # Start with flash (no ".0" in name)
    "gemini-2.5-pro",
]

# Limit to first N folders (set to None for all)
MAX_FOLDERS = 6

# Cost per PDF (estimated)
COST_PER_PDF = {
    "gemini-2.5-pro": 0.07,
    "gemini-3-flash-preview": 0.03,
}


def get_test_folders() -> list[Path]:
    """Get all test sample folders."""
    samples_dir = Path(__file__).parent / "test_samples"
    folders = [f for f in samples_dir.iterdir() if f.is_dir() and not f.name.startswith(".")]
    folders = sorted(folders)
    if MAX_FOLDERS:
        folders = folders[:MAX_FOLDERS]
    return folders


def count_pdfs_in_folder(folder: Path) -> int:
    """Count PDFs in a folder."""
    return len(list(folder.glob("*.pdf")))


async def run_benchmark_for_model(
    model: str,
    folders: list[Path],
    output_base: Path,
) -> dict:
    """Run benchmark for a single model."""
    results = {
        "model": model,
        "total_pdfs": 0,
        "successful_folders": 0,
        "failed_folders": 0,
        "total_time": 0,
        "folder_times": {},
        "errors": [],
    }

    output_dir = output_base / f"benchmark_{model.replace('.', '_').replace('-', '_')}"
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold blue]Running benchmark with {model}[/bold blue]")
    console.print(f"Output directory: {output_dir}\n")

    start_total = time.time()

    for folder in folders:
        folder_name = folder.name
        pdf_count = count_pdfs_in_folder(folder)
        results["total_pdfs"] += pdf_count

        console.print(f"[cyan]Processing {folder_name}[/cyan] ({pdf_count} PDFs)...")

        start_folder = time.time()
        try:
            await extract_batch(
                pdfs_folder=folder,
                customer_id="auto",
                output_dir=output_dir / f"order_{folder_name}",
                model=model,
            )
            elapsed = time.time() - start_folder
            results["folder_times"][folder_name] = {
                "time": elapsed,
                "pdfs": pdf_count,
                "success": True,
            }
            results["successful_folders"] += 1
            console.print(f"  [green]Done in {elapsed:.1f}s[/green]")
        except Exception as e:
            elapsed = time.time() - start_folder
            results["folder_times"][folder_name] = {
                "time": elapsed,
                "pdfs": pdf_count,
                "success": False,
                "error": str(e),
            }
            results["failed_folders"] += 1
            results["errors"].append(f"{folder_name}: {e}")
            console.print(f"  [red]Failed: {e}[/red]")

    results["total_time"] = time.time() - start_total
    return results


def print_comparison(results: list[dict]):
    """Print comparison table."""
    console.print("\n" + "=" * 60)
    console.print("[bold]BENCHMARK RESULTS[/bold]")
    console.print("=" * 60 + "\n")

    # Summary table
    table = Table(title="Model Comparison")
    table.add_column("Metric", style="cyan")
    for r in results:
        table.add_column(r["model"], style="green")

    # Total time
    table.add_row(
        "Total Time",
        *[f"{r['total_time']:.1f}s ({r['total_time']/60:.1f}min)" for r in results]
    )

    # PDFs processed
    table.add_row(
        "PDFs Processed",
        *[str(r["total_pdfs"]) for r in results]
    )

    # Time per PDF
    table.add_row(
        "Avg Time/PDF",
        *[f"{r['total_time']/r['total_pdfs']:.2f}s" if r['total_pdfs'] > 0 else "N/A" for r in results]
    )

    # Success rate
    table.add_row(
        "Success Rate",
        *[f"{r['successful_folders']}/{r['successful_folders']+r['failed_folders']} folders" for r in results]
    )

    # Estimated cost
    table.add_row(
        "Estimated Cost",
        *[f"€{r['total_pdfs'] * COST_PER_PDF.get(r['model'], 0.05):.2f}" for r in results]
    )

    console.print(table)

    # Speed comparison
    if len(results) == 2:
        time_diff = results[0]["total_time"] - results[1]["total_time"]
        faster_model = results[1]["model"] if time_diff > 0 else results[0]["model"]
        speed_diff = abs(time_diff)
        pct_faster = (speed_diff / max(results[0]["total_time"], results[1]["total_time"])) * 100

        console.print(f"\n[bold]Speed:[/bold] {faster_model} is {speed_diff:.1f}s ({pct_faster:.0f}%) faster")

        cost_diff = abs(
            results[0]["total_pdfs"] * COST_PER_PDF.get(results[0]["model"], 0.05) -
            results[1]["total_pdfs"] * COST_PER_PDF.get(results[1]["model"], 0.05)
        )
        cheaper_model = results[1]["model"] if COST_PER_PDF.get(results[0]["model"], 0.05) > COST_PER_PDF.get(results[1]["model"], 0.05) else results[0]["model"]
        console.print(f"[bold]Cost:[/bold] {cheaper_model} saves €{cost_diff:.2f} for this test")


def save_results(results: list[dict], output_path: Path):
    """Save results to a markdown file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(output_path, "w") as f:
        f.write(f"# Benchmark Results\n\n")
        f.write(f"**Date:** {timestamp}\n\n")

        f.write("## Summary\n\n")
        f.write("| Metric | " + " | ".join(r["model"] for r in results) + " |\n")
        f.write("|--------|" + "|".join(["--------" for _ in results]) + "|\n")
        f.write("| Total Time | " + " | ".join(f"{r['total_time']:.1f}s" for r in results) + " |\n")
        f.write("| PDFs Processed | " + " | ".join(str(r["total_pdfs"]) for r in results) + " |\n")
        f.write("| Avg Time/PDF | " + " | ".join(f"{r['total_time']/r['total_pdfs']:.2f}s" if r['total_pdfs'] > 0 else "N/A" for r in results) + " |\n")
        f.write("| Success Rate | " + " | ".join(f"{r['successful_folders']}/{r['successful_folders']+r['failed_folders']}" for r in results) + " |\n")
        f.write("| Est. Cost | " + " | ".join(f"€{r['total_pdfs'] * COST_PER_PDF.get(r['model'], 0.05):.2f}" for r in results) + " |\n")

        f.write("\n## Per-Folder Details\n\n")
        for r in results:
            f.write(f"\n### {r['model']}\n\n")
            f.write("| Folder | PDFs | Time | Status |\n")
            f.write("|--------|------|------|--------|\n")
            for folder, data in r["folder_times"].items():
                status = "OK" if data["success"] else f"FAIL: {data.get('error', 'Unknown')}"
                f.write(f"| {folder} | {data['pdfs']} | {data['time']:.1f}s | {status} |\n")

        if any(r["errors"] for r in results):
            f.write("\n## Errors\n\n")
            for r in results:
                if r["errors"]:
                    f.write(f"\n### {r['model']}\n\n")
                    for err in r["errors"]:
                        f.write(f"- {err}\n")

    console.print(f"\n[green]Results saved to {output_path}[/green]")


async def main():
    """Run the benchmark."""
    console.print("[bold]PDF Extractor Model Benchmark[/bold]")
    console.print("=" * 40)

    folders = get_test_folders()
    total_pdfs = sum(count_pdfs_in_folder(f) for f in folders)

    console.print(f"\nFound {len(folders)} test folders with {total_pdfs} PDFs total")
    console.print(f"Models to test: {', '.join(MODELS)}")

    estimated_cost = sum(total_pdfs * COST_PER_PDF.get(m, 0.05) for m in MODELS)
    console.print(f"Estimated total cost: €{estimated_cost:.2f}")
    console.print(f"Estimated time: ~{len(MODELS) * total_pdfs * 5 / 60:.0f} minutes\n")

    # Confirm
    console.print("[yellow]Press Enter to start or Ctrl+C to cancel...[/yellow]")
    input()

    output_base = Path(__file__).parent / "benchmark_output"
    output_base.mkdir(exist_ok=True)

    all_results = []

    for model in MODELS:
        results = await run_benchmark_for_model(model, folders, output_base)
        all_results.append(results)

    # Print comparison
    print_comparison(all_results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_results(all_results, output_base / f"benchmark_results_{timestamp}.md")


if __name__ == "__main__":
    asyncio.run(main())
