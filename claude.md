# PDF Extractor Project

## Overzicht

Een Python CLI-tool die technische tekeningen uit PDF's extraheert met behulp van Google Gemini AI. Specifiek ontworpen voor productie-omgevingen (ELTEN, Rademaker) om gestructureerde data te extraheren zoals onderdeelnummers, gatspecificaties, toleranties, materialen en operator-waarschuwingen.

## Projectstructuur

```txt
python_version/
├── extractor/                 # Hoofdmodule
│   ├── main.py               # CLI entry point, batch/single processing
│   ├── gemini_service.py     # Gemini API integratie
│   ├── prompt_builder.py     # Dynamische prompt generatie
│   ├── operator_warnings.py  # Waarschuwingen voor operators
│   ├── xml_writer.py         # XML output formatting
│   ├── csv_logger.py         # Dagelijkse CSV logging
│   ├── config_loader.py      # YAML configuratie management
│   ├── customer_detection.py # Vision-based klant auto-detectie
│   ├── types.py              # Pydantic models
│   ├── constants.py          # Globale constanten (model selectie)
│   └── utils.py              # Utility functies
├── config/
│   ├── base.yaml             # Basis configuratie (altijd geladen)
│   └── customers/            # Klant-specifieke configs
│       ├── elten/
│       │   ├── config.yaml
│       │   └── surface-treatments.yaml
│       └── rademaker/
│           ├── config.yaml
│           └── surface-treatments.yaml
├── logs/                      # Dagelijkse CSV logs
│   └── pdf_extractor_log_YYYY-MM-DD.csv
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
python -m extractor.main drawing.pdf --model gemini-3-flash-preview

# Batch processing
python -m extractor.main /path/to/pdfs --customer auto
python -m extractor.main /path/to/pdfs --customer rademaker
```

## Output

### XML Output

Bestandsnaam is gebaseerd op de input mapnaam: `PDF_XML_<MAPNAAM>.xml`

De XML bevat nu een **Metadata sectie** bovenaan met:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Order>
  <Metadata>
    <TotalPDFs>20</TotalPDFs>
    <SuccessfulPDFs>18</SuccessfulPDFs>
    <FailedPDFs>2</FailedPDFs>
    <DetectedCustomer>ELTEN</DetectedCustomer>
  </Metadata>
  <Items>
    <Item>
      <PartNumber>MD-22-08803_2</PartNumber>
      <Status>FAILED</Status>
    </Item>
    <!-- Succesvolle items met alle data -->
  </Items>
</Order>
```

**Let op:** Gefaalde PDFs worden bovenaan de Items lijst getoond met alleen `<PartNumber>` en `<Status>FAILED</Status>`.

### Dagelijkse CSV Log

Locatie: `logs/pdf_extractor_log_YYYY-MM-DD.csv`

Bevat per PDF:
- Timestamp
- Order naam
- PDF naam
- Status (SUCCESS/FAILED)
- Verwerkingstijd in seconden
- Foutmelding (bij FAILED)
- Gedetecteerde klant

Voorbeeld:

```csv
Timestamp,Order,PDF,Status,Time(s),Error,Customer
2026-02-05 09:15:32,20260231,MD-22-08803_2,SUCCESS,18.3,,ELTEN
2026-02-05 09:15:51,20260231,10015086_1,FAILED,45.2,MAX_TOKENS exceeded,ELTEN
```

Dit bestand wordt aangevuld bij elke run en is bedoeld voor analyse/leren van het model

---

## Gemini Modellen

### Benchmark Resultaten (67 PDFs, 6 orders)

| Model | Kosten/PDF | Snelheid | Accuraatheid |
|-------|-----------|----------|--------------|
| `gemini-2.5-pro` (default) | ~€0.07 | 22.8s/PDF | **100%** - geen fouten |
| `gemini-3-flash-preview` | ~€0.03 | 34.0s/PDF | 99% - 1 hallucinatie |

**Conclusie benchmark:**
- **Pro is 33% sneller** en betrouwbaarder
- **Flash is 57% goedkoper** maar hallucineerde 1x tapgaten die er niet waren
- **Aanbeveling: gebruik Pro voor productie**

### Jaarlijkse Kosten (geschat)

| Volume | gemini-2.5-pro | gemini-3-flash-preview |
|--------|----------------|------------------------|
| 50.000 PDFs | €3.500 | €1.500 |
| 80.000 PDFs | €5.600 | €2.400 |

### Model Selectie

Het default model wordt ingesteld in `extractor/constants.py`:

```python
DEFAULT_GEMINI_MODEL = "gemini-2.5-pro"  # Of "gemini-3-flash-preview"
```

Override via CLI: `--model gemini-3-flash-preview`

---

## Klantdetectie & YAML Configuraties

### Auto-detectie (`--customer auto`)

**Aanbevolen voor productie.** Het systeem detecteert automatisch de klant:

1. Eerste PDF wordt geanalyseerd door Gemini Vision
2. Zoekt naar "ELTEN" of "RADEMAKER" in de BOM tabel (rechtsonder)
3. Laadt bijbehorende klant-configuratie
4. Fallback naar `base` als geen klant gevonden

### Configuratie Hiërarchie

```txt
base.yaml                              ← Altijd geladen (basis regels)
    ↓ merged met
customers/<klant>/config.yaml          ← Klant-specifieke overrides
    +
customers/<klant>/surface-treatments.yaml
```

### Wat de YAML configs bepalen

| Config Sectie | Functie |
|---------------|---------|
| `signals.tolerated_lengths` | Regex patronen voor tolerantie detectie |
| `signals.holes` | Patronen voor gat/tapgat herkenning |
| `surfaceTreatments` | Coating keywords en display names |
| `material_patterns` | Instructies voor materiaal extractie |
| `prompt_additions` | Klant-specifieke prompt instructies |

### Wanneer welke optie gebruiken

| Optie | Gebruik |
|-------|---------|
| `-c auto` | **Productie** - klant onbekend, automatisch detecteren |
| `-c elten` | Forceer ELTEN config (als auto verkeerd detecteert) |
| `-c rademaker` | Forceer Rademaker config |
| `-c base` | Alleen basis regels, geen klant-specifieke |

---

## Dependencies

- `google-genai>=1.0.0` - Gemini API (nieuwe SDK)
- `pyyaml>=6.0` - YAML parsing
- `python-dotenv>=1.0.0` - Environment variables
- `pydantic>=2.0.0` - Data validatie
- `rich>=13.0.0` - Terminal UI
- `click>=8.0.0` - CLI framework

---

## Code Conventies

- **Naamgeving:** Mix van snake_case en camelCase (vanwege API compatibility)
- **Type Hints:** Pydantic models met `Field(alias="camelCase")`
- **Async:** Gebruik `asyncio` voor API calls
- **Config:** YAML bestanden in `config/` directory
- **Output:** XML naar input folder als `PDF_XML_<mapnaam>.xml`
- **Logging:** `logging` module voor warnings/errors

---

## Aanbevelingen

1. **Altijd** `.env` buiten version control houden
2. Gebruik `gemini-2.5-pro` voor productie (hoogste accuraatheid)
3. Monitor API kosten via Google Cloud Console
4. Gebruik `--customer auto` voor automatische klantdetectie
