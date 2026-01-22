# PDF Extractor (Python)

Extract manufacturing data from technical drawing PDFs using Gemini AI.

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install as CLI tool
pip install -e .
```

## Setup

Create a `.env` file with your Gemini API key:

```bash
GEMINI_API_KEY=your_api_key_here
```

## Usage

### Single PDF

```bash
# Basic usage (auto-detects output location)
pdf-extract drawing.pdf

# Specify customer
pdf-extract drawing.pdf --customer elten

# Custom output
pdf-extract drawing.pdf --output results/
pdf-extract drawing.pdf --json output.json --xml output.xml

# Use different model
pdf-extract drawing.pdf --model gemini-2.5-pro
```

### Batch Processing

```bash
# Process all PDFs in a folder (auto-detect customer)
pdf-extract --batch /path/to/pdfs

# Or use the batch subcommand
pdf-extract batch /path/to/pdfs

# Specify customer
pdf-extract batch /path/to/pdfs --customer rademaker

# Auto-detect customer from first PDF
pdf-extract batch /path/to/pdfs --customer auto

# Custom output directory
pdf-extract batch /path/to/pdfs --output results/
```

## Available Models

- `gemini-2.5-flash` (default, fastest)
- `gemini-2.5-pro` (more accurate)
- `gemini-1.5-flash`
- `gemini-1.5-pro`

## Supported Customers

- `elten` - ELTEN drawings with surface treatments (Parelstralen, Poedercoaten, Verzinken)
- `rademaker` - Rademaker drawings
- `base` - Generic extraction rules
- `auto` - Auto-detect customer from BOM table (batch mode only)

## Output

- **XML**: Formatted output with operator warnings for tap holes, toleranced holes, critical dimensions

Output format: `PDF_XML_<foldername>.xml`

Default output location:
- Single PDF: Same folder as the input PDF
- Batch: Same folder as the input PDFs

## Project Structure

```
python_version/
├── extractor/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── types.py             # Pydantic models
│   ├── config_loader.py     # YAML config management
│   ├── gemini_service.py    # Gemini API integration
│   ├── prompt_builder.py    # Prompt generation
│   ├── customer_detection.py # Vision-based detection
│   ├── operator_warnings.py  # Warning generation
│   └── xml_writer.py        # XML output
├── config/
│   ├── base.yaml            # Base configuration
│   └── customers/
│       ├── elten/
│       │   ├── config.yaml
│       │   └── surface-treatments.yaml
│       └── rademaker/
│           ├── config.yaml
│           └── surface-treatments.yaml
├── requirements.txt
├── setup.py
└── README.md
```

## Features

- **Direct CLI**: `pdf-extract` command without npm/server
- **Auto customer detection**: Vision-based detection from BOM table
- **Retry logic**: Exponential backoff on API errors (503, 429)
- **Circuit breaker**: Pause after 5 consecutive failures
- **Assembly detection**: Identifies assembly drawings in batch mode
- **Rich output**: Progress spinners and colored console output

## Example

```bash
# Analyze a batch of technical drawings
$ pdf-extract /path/to/order_123/ --customer auto

Auto-detecting customer from first PDF...
Detected customer: ELTEN (high confidence)
Processing 5 PDFs...
Done: 5 successful, 0 failed
Output: /path/to/order_123/PDF_XML_order_123.xml
```
