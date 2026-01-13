# PDF Extractor - Gebruikshandleiding

## Snelle Start

```bash
# Navigeer naar de project folder
cd /pad/naar/python_version

# Activeer virtual environment
source .venv/bin/activate        # Mac/Linux
.venv\Scripts\activate           # Windows

# Run extractie
python -m extractor.main <PDF_OF_FOLDER> [opties]
```

---

## Alle Commando's

### 1. Single PDF Extractie

Verwerk één PDF bestand:

```bash
# Basis (gebruikt default customer: elten, default model: gemini-2.5-pro)
python -m extractor.main tekening.pdf

# Met specifieke klant
python -m extractor.main tekening.pdf --customer elten
python -m extractor.main tekening.pdf --customer rademaker
python -m extractor.main tekening.pdf -c elten              # korte versie

# Met specifiek model
python -m extractor.main tekening.pdf --model gemini-2.5-pro
python -m extractor.main tekening.pdf --model gemini-3-flash-preview
python -m extractor.main tekening.pdf -m gemini-3-flash-preview    # korte versie

# Met custom output folder
python -m extractor.main tekening.pdf --output /pad/naar/output
python -m extractor.main tekening.pdf -o /pad/naar/output    # korte versie

# Met specifiek XML pad
python -m extractor.main tekening.pdf --xml output.xml

# Combinaties
python -m extractor.main tekening.pdf -c rademaker -m gemini-3-flash-preview -o resultaten/
```

### 2. Batch Extractie (Folder met PDFs)

Verwerk alle PDFs in een folder:

```bash
# Met auto-detectie van klant (aanbevolen)
python -m extractor.main /pad/naar/pdf_folder --customer auto
python -m extractor.main /pad/naar/pdf_folder -c auto

# Met specifieke klant
python -m extractor.main /pad/naar/pdf_folder --customer elten
python -m extractor.main /pad/naar/pdf_folder --customer rademaker

# Met specifiek model
python -m extractor.main /pad/naar/pdf_folder -c auto -m gemini-3-flash-preview

# Met custom output folder
python -m extractor.main /pad/naar/pdf_folder -c auto -o /pad/naar/output
```

---

## Opties Overzicht

| Optie | Kort | Beschrijving | Default |
|-------|------|--------------|---------|
| `--customer` | `-c` | Klant configuratie | `elten` |
| `--model` | `-m` | Gemini model | `gemini-2.5-pro` |
| `--output` | `-o` | Output folder | `output/order_<naam>/` |
| `--xml` | - | Specifiek XML pad | `<output>/<partnumber>.xml` |

### Customer Opties

| Waarde | Beschrijving |
|--------|--------------|
| `auto` | **Aanbevolen** - Automatische detectie via Vision API |
| `elten` | ELTEN configuratie (forceer) |
| `rademaker` | Rademaker configuratie (forceer) |
| `base` | Basis configuratie (geen klant-specifieke regels) |

#### Hoe werkt klantdetectie?

**`--customer auto` (Aanbevolen voor productie)**

1. De eerste PDF wordt geanalyseerd door Gemini Vision
2. Gemini zoekt naar klantnamen in de BOM tabel (rechtsonder)
3. Bij detectie van "ELTEN" of "RADEMAKER" wordt de bijbehorende configuratie geladen
4. Als geen klant gevonden wordt, valt het systeem terug op `base` configuratie

**Wanneer `auto` gebruiken:**

- Bij onbekende orders waar je de klant niet van tevoren weet
- In productie-omgevingen waar tekeningen automatisch binnenkomen
- Bij gemengde orders van verschillende klanten

**Wanneer specifieke klant (`elten`/`rademaker`) gebruiken:**

- Als je 100% zeker weet welke klant het is
- Als auto-detectie een verkeerde klant detecteert
- Voor testen met specifieke klant-configuraties

#### YAML Configuraties

Het systeem laadt klant-specifieke configuraties uit YAML bestanden:

```txt
config/
├── base.yaml                    # Basis regels (altijd geladen)
└── customers/
    ├── elten/
    │   ├── config.yaml          # ELTEN-specifieke extractie regels
    │   └── surface-treatments.yaml
    └── rademaker/
        ├── config.yaml          # Rademaker-specifieke extractie regels
        └── surface-treatments.yaml
```

Deze configs bepalen:

- Tolerantie detectie patronen
- Hole/gat herkenning regels
- Surface treatment keywords
- Materiaal extractie instructies

---

## Model Keuze

### Beschikbare Modellen

| Model | Kosten/PDF | Snelheid | Accuraatheid |
|-------|-----------|----------|--------------|
| `gemini-2.5-pro` | ~€0.07 | 22.8s/PDF | **Hoogste** - geen fouten |
| `gemini-3-flash-preview` | ~€0.03 | 34.0s/PDF | Goed - incidenteel hallucinaties |

### Benchmark Resultaten (67 PDFs, 6 orders)

| Metric | gemini-2.5-pro | gemini-3-flash-preview |
|--------|----------------|------------------------|
| Totale tijd | 25.5 min | 38.0 min |
| Kosten | €4.69 | €2.01 |
| Tapgat detectie | 100% correct | 1 hallucinatie (4x M6 gezien die er niet was) |
| Tolerantie detectie | 100% correct | 100% correct |

### Aanbeveling

**Gebruik `gemini-2.5-pro` (default)** voor productie:
- Sneller (33% sneller dan Flash)
- Geen hallucinaties bij tapgat detectie
- Betrouwbaarder voor kritieke productie-informatie

**Overweeg `gemini-3-flash-preview`** alleen als:
- Kosten belangrijker zijn dan 100% accuraatheid
- Je de output handmatig controleert

### Jaarlijkse Kosten (geschat)

| Volume | gemini-2.5-pro | gemini-3-flash-preview | Besparing |
|--------|----------------|------------------------|-----------|
| 50.000 PDFs | €3.500 | €1.500 | €2.000 |
| 80.000 PDFs | €5.600 | €2.400 | €3.200 |

---

## Output Locaties

### Output Formaat

**Alleen XML** - bestandsnaam is de assembly part number:

```txt
output/
└── order_<FOLDERNAAM>/
    └── <ASSEMBLY_PARTNUMBER>.xml
```

### Single PDF Voorbeeld

```bash
python -m extractor.main tekening_12345.pdf
```

Output:

```txt
output/
└── order_12345/
    └── 12345.xml
```

### Batch Voorbeeld

```bash
python -m extractor.main order_folder/ -c auto
```

Output:

```txt
output/
└── order_order_folder/
    └── <ASSEMBLY_PARTNUMBER>.xml
```

### Custom Output

```bash
python -m extractor.main tekening.pdf -o /Users/naam/Desktop/resultaten
```

Output:

```txt
/Users/naam/Desktop/resultaten/
└── <PARTNUMBER>.xml
```

---

## Voorbeelden

### Voorbeeld 1: Simpele Extractie

```bash
python -m extractor.main /Users/tess/tekeningen/part_001.pdf
```

### Voorbeeld 2: Rademaker Order

```bash
python -m extractor.main /Users/tess/orders/rademaker_batch/ \
    --customer rademaker \
    --output /Users/tess/output/
```

### Voorbeeld 3: Auto-detectie Klant

```bash
python -m extractor.main /Users/tess/orders/onbekende_order/ -c auto
```

### Voorbeeld 4: Windows Paden

```cmd
python -m extractor.main C:\Users\Naam\tekeningen\order_123 -c auto -o C:\output
```

---

## XML Output Formaat

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Order>
  <Items>
    <Item>
      <PartNumber>12345_Rev_01</PartNumber>
      <Material>AISI 304 3mm</Material>
      <SurfaceTreatment>Verzinkt</SurfaceTreatment>
      <Holes>
        <Hole count="4" type="tapped" threadSize="M6"/>
        <Hole count="2" type="reamed" diameter="20" tolerance="H9"/>
      </Holes>
      <ToleratedLengths>
        <ToleratedLength>
          <Dimension>250</Dimension>
          <Type>symmetric</Type>
          <Upper>+0.5</Upper>
          <Lower>-0.5</Lower>
        </ToleratedLength>
      </ToleratedLengths>
      <PDF_Warnings>
        <Message>Nabewerking: 4x M6 tapgat, 2x O20 H9, 250 tol</Message>
      </PDF_Warnings>
    </Item>
  </Items>
</Order>
```

### Wat wordt gedetecteerd?

| Element | Beschrijving | Voorbeeld |
|---------|--------------|-----------|
| `PartNumber` | Onderdeelnummer uit tekening | `MD-22-08811_2` |
| `Material` | Materiaal + dikte | `S235 8 mm` |
| `SurfaceTreatment` | Oppervlaktebehandeling | `Powder coating (9)` |
| `Holes` | Gaten met toleranties | `M6 tapped`, `O20 H9` |
| `ToleratedLengths` | Maten met toleranties | `250 ±0.5` |
| `PDF_Warnings` | Samenvatting voor operator | Nabewerkingen |

---

## Troubleshooting

### "Module not found" Error

```bash
# Zorg dat je in de juiste folder bent
cd /pad/naar/python_version

# Activeer virtual environment
source .venv/bin/activate
```

### "API Key not found" Error

Maak `.env` bestand aan in `python_version/`:

```txt
GEMINI_API_KEY=jouw_api_key_hier
```

### "Model not found" Error

Controleer modelnaam:

- `gemini-2.5-pro` (correct)
- `gemini-3-flash-preview` (correct, zonder ".0")

### Pad met Spaties

Gebruik quotes:

```bash
python -m extractor.main "/Users/naam/My Documents/order folder" -c auto
```

---

## Tips

1. **Gebruik `--customer auto`** voor batch orders - detecteert automatisch ELTEN/Rademaker
2. **Gebruik `gemini-2.5-pro`** (default) voor hoogste accuraatheid
3. **Check de XML output** voor operator warnings (tapgaten, toleranties)
4. **Assembly detectie** - het systeem detecteert automatisch welke PDF de assembly is
