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
│   ├── constants.py          # Globale constanten
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

# Single PDF
pdf-extract drawing.pdf
pdf-extract drawing.pdf --customer elten

# Batch processing
pdf-extract --batch /path/to/pdfs
pdf-extract batch /path/to/pdfs --customer auto
```

## Dependencies

- `google-generativeai>=0.8.0` - Gemini API
- `pyyaml>=6.0` - YAML parsing
- `python-dotenv>=1.0.0` - Environment variables
- `pydantic>=2.0.0` - Data validatie
- `rich>=13.0.0` - Terminal UI
- `click>=8.0.0` - CLI framework

---

## Bekende Problemen & Bugs

### KRITIEK

#### 1. API Key in Repository (SECURITY)
**Locatie:** `.env`

De API key staat in plain text en is mogelijk al gecommit naar git history.

**Fix:**
- Revoke de huidige key onmiddellijk
- Verwijder uit git history: `git filter-branch` of `bfg`
- Gebruik environment variables

#### 2. Ongeldig Model Naam
**Locatie:** [constants.py:2](extractor/constants.py#L2)

```python
DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"  # BESTAAT NIET
```

**Fix:** Wijzig naar `"gemini-2.5-flash"` of `"gemini-1.5-flash"`

#### 3. Duplicate Import
**Locatie:** [main.py:35](extractor/main.py#L35) en [main.py:40](extractor/main.py#L40)

`DEFAULT_GEMINI_MODEL` wordt twee keer geimporteerd.

### HOOG

#### 4. Race Condition in Circuit Breaker
**Locatie:** [main.py:212-333](extractor/main.py#L212-L333)

```python
# Globale mutable state zonder synchronisatie
consecutive_failures = 0  # RACE CONDITION in async context
```

**Fix:** Gebruik `asyncio.Lock()` voor thread-safe updates:
```python
failure_lock = asyncio.Lock()
async with failure_lock:
    consecutive_failures += 1
```

#### 5. Geen JSON Error Handling
**Locatie:** [gemini_service.py:297-298](extractor/gemini_service.py#L297-L298)

```python
data = json.loads(json_text)  # Geen try/except!
```

**Fix:**
```python
try:
    data = json.loads(json_text)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON from Gemini: {e}") from e
```

#### 6. Incorrecte Regex voor Thread Sorting
**Locatie:** [operator_warnings.py:65-67](extractor/operator_warnings.py#L65-L67)

```python
match = re.search(r"\d+", item[0])  # Matcht eerste getal, niet thread size
```

**Fix:**
```python
match = re.search(r"M(\d+)", item[0])  # Specifiek voor M-threads
```

#### 7. Generic Exception Handling
**Locatie:** [customer_detection.py:91-97](extractor/customer_detection.py#L91-L97)

- Gebruikt `print()` i.p.v. logging
- Vangt alle exceptions zonder specifieke handling

### MEDIUM

#### 8. Incomplete Async Wrapper
**Locatie:** [gemini_service.py:328-334](extractor/gemini_service.py#L328-L334)

```python
def extract_order_details_from_pdf_sync(...):
    import asyncio  # Import hoort bovenaan
    return asyncio.run(...)  # Faalt als al in async context
```

**Fix:** Gebruik `nest_asyncio` of refactor naar proper async design.

#### 9. Stille Config Failures
**Locatie:** [config_loader.py:108-109](extractor/config_loader.py#L108-L109)

```python
if not file_path.exists():
    return {}  # Stille failure!
```

**Fix:** Raise `FileNotFoundError` voor required configs.

#### 10. Case-Sensitive Assembly Matching
**Locatie:** [main.py:347-350](extractor/main.py#L347-L350)

```python
assembly_pdf = next(
    (f for f in pdf_files if f.stem == assembly_part_number), None
)  # Case-sensitive!
```

**Fix:** Gebruik `.lower()` voor case-insensitive matching.

#### 11. Type Hints Verzwakt
**Locatie:** [types.py:37-46](extractor/types.py#L37-L46)

Required fields zijn optional gemaakt, `Literal` types vervangen door `str`. Dit vermindert type safety.

### LAAG

#### 12. Geen Logging Framework
Overal `print()` i.p.v. structured logging. Voeg `logging` module toe.

#### 13. Hardcoded Prompts
**Locatie:** [prompt_builder.py](extractor/prompt_builder.py)

Overweeg een template systeem voor betere onderhoudbaarheid.

#### 14. Geen CLI Argument Validatie
**Locatie:** [main.py:403-417](extractor/main.py#L403-L417)

Customer ID wordt niet gevalideerd tegen bekende waarden.

#### 15. Geen Retry voor Customer Detection
**Locatie:** [main.py:273-276](extractor/main.py#L273-L276)

Main extraction heeft retry logic, customer detection niet.

---

## Code Conventies

- **Naamgeving:** Mix van snake_case en camelCase (vanwege API compatibility)
- **Type Hints:** Pydantic models met `Field(alias="camelCase")`
- **Async:** Gebruik `asyncio` voor API calls
- **Config:** YAML bestanden in `config/` directory
- **Output:** JSON en XML naar `test_output/order_<partNumber>/`

## Testing

Momenteel geen test suite aanwezig. Aanbevolen:
- Unit tests voor `prompt_builder.py`
- Integration tests voor `gemini_service.py` (met mocks)
- E2E tests met sample PDFs

## Aanbevelingen voor Ontwikkeling

1. **Altijd** `.env` buiten version control houden
2. Valideer JSON responses van Gemini
3. Gebruik logging i.p.v. print statements
4. Test met edge cases (lege PDFs, corrupte bestanden)
5. Voeg proper async locking toe voor batch processing
