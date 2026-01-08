# PDF Extractor Project

## Overzicht

Een Python CLI-tool die technische tekeningen uit PDF's extraheert met behulp van Google Gemini AI. Specifiek ontworpen voor productie-omgevingen (ELTEN, Rademaker) om gestructureerde data te extraheren zoals onderdeelnummers, gatspecificaties, toleranties, materialen en operator-waarschuwingen.

## Projectstructuur

```
python_version/
├── extractor/                 # Hoofdmodule (~1,770 regels)
│   ├── main.py               # CLI entry point, batch/single processing
│   ├── gemini_service.py     # Gemini API integratie
│   ├── prompt_builder.py     # Dynamische prompt generatie
│   ├── operator_warnings.py  # Waarschuwingen voor operators
│   ├── xml_writer.py         # XML output formatting
│   ├── config_loader.py      # YAML configuratie management
│   ├── customer_detection.py # Vision-based klant auto-detectie
│   ├── types.py              # Pydantic models
│   ├── constants.py          # Globale constanten (model selectie)
│   └── utils.py              # Utility functies
├── config/
│   ├── base.yaml             # Basis configuratie
│   └── customers/            # Klant-specifieke configs
│       ├── elten/
│       └── rademaker/
├── requirements.txt
├── setup.py
└── .env                      # API key (NIET COMMITTEN!)
```

## Installatie & Gebruik

```bash
# Installatie
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# .env aanmaken met GEMINI_API_KEY=<jouw_key>

# Single PDF (gebruikt default model: gemini-2.5-pro)
python -m extractor.main drawing.pdf
python -m extractor.main drawing.pdf --customer elten

# Met specifiek model
python -m extractor.main drawing.pdf --model gemini-3.0-flash-preview

# Batch processing
python -m extractor.main /path/to/pdfs --customer auto
python -m extractor.main /path/to/pdfs --customer rademaker --model gemini-3.0-flash-preview
```

## Output

**Alleen XML output** - bestandsnaam is de assembly part number:

```
test_output/
└── order_<FOLDERNAAM>/
    └── <ASSEMBLY_PARTNUMBER>.xml
```

Voorbeeld: Als assembly `10009043_1` is → output is `10009043_1.xml`

## Gemini Modellen

### Beschikbare Modellen

| Model | Kosten/PDF | Gebruik |
|-------|-----------|---------|
| `gemini-2.5-pro` (default) | ~€0.07 | Hoogste kwaliteit, stabiel |
| `gemini-3.0-flash-preview` | ~€0.03 | Nieuwste preview, goedkoper |

### Kostenberekening (50.000 - 80.000 PDFs/jaar)

| Model | Per PDF | 50k PDFs/jaar | 80k PDFs/jaar |
|-------|---------|---------------|---------------|
| `gemini-2.5-pro` | €0.07 | €3.680/jaar | €5.890/jaar |
| `gemini-3.0-flash-preview` | €0.03 | €1.380/jaar | €2.210/jaar |

**Besparing met 3.0 Flash:** ~€2.300 - €3.680/jaar

### Model Selectie

Het default model wordt ingesteld in [constants.py](extractor/constants.py):

```python
DEFAULT_GEMINI_MODEL = "gemini-2.5-pro"  # Of "gemini-3.0-flash-preview"
```

Override via CLI: `--model gemini-3.0-flash-preview`

## Dependencies

- `google-generativeai>=0.8.0` - Gemini API (deprecated, migratie naar `google.genai` aanbevolen)
- `pyyaml>=6.0` - YAML parsing
- `python-dotenv>=1.0.0` - Environment variables
- `pydantic>=2.0.0` - Data validatie
- `rich>=13.0.0` - Terminal UI
- `click>=8.0.0` - CLI framework

---

## Opgeloste Bugs (v1.1)

De volgende bugs zijn opgelost in de huidige versie:

| Bug | Oplossing |
|-----|-----------|
| Duplicate import in main.py | Verwijderd |
| JSON parsing zonder error handling | Try/except toegevoegd |
| Race condition in circuit breaker | `asyncio.Lock()` toegevoegd |
| Generic exception handling | Specifieke exceptions + logging |
| Incorrecte regex voor M-threads | `M(\d+)` pattern |
| Stille config failures | `required` parameter toegevoegd |
| Async wrapper problemen | ThreadPoolExecutor fallback |
| Dubbele regel in prompt | Verwijderd |

## Code Conventies

- **Naamgeving:** Mix van snake_case en camelCase (vanwege API compatibility)
- **Type Hints:** Pydantic models met `Field(alias="camelCase")`
- **Async:** Gebruik `asyncio` voor API calls
- **Config:** YAML bestanden in `config/` directory
- **Output:** XML naar `test_output/order_<partNumber>/<assembly>.xml`
- **Logging:** `logging` module voor warnings/errors

## Testing

Test samples staan in `test_samples/`:

- `10009043_1/` - ELTEN order (3 PDFs)
- `Rademaker tekening/` - Rademaker order (9 PDFs)

```bash
# Test run
python -m extractor.main test_samples/10009043_1 --customer auto
python -m extractor.main test_samples/Rademaker\ tekening --customer auto
```

## Aanbevelingen voor Ontwikkeling

1. **Altijd** `.env` buiten version control houden
2. Test met beide modellen voor kwaliteitsvergelijking
3. Monitor API kosten via Google Cloud Console
4. Migreer naar `google.genai` package wanneer stabiel
