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
# Basis (customer: base, automatische preflight, snelle modelroute)
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
# Zonder klantdetectie (standaard en aanbevolen voor snelle verwerking)
python -m extractor.main /pad/naar/pdf_folder --customer base

# Met specifieke klant
python -m extractor.main /pad/naar/pdf_folder --customer elten
python -m extractor.main /pad/naar/pdf_folder --customer rademaker

# Met specifiek model
python -m extractor.main /pad/naar/pdf_folder -c base -m gemini-2.5-pro

# Met custom output folder
python -m extractor.main /pad/naar/pdf_folder -c base -o /pad/naar/output
```

---

## Opties Overzicht

| Optie | Kort | Beschrijving | Default |
|-------|------|--------------|---------|
| `--customer` | `-c` | Expliciete klantconfiguratie | `base` |
| `--model` | `-m` | Optionele Gemini-modeloverride | automatisch |
| `--scan-depth` | - | `auto`, `fast` of `deep` | `auto` |
| `--assembly-recheck` | - | Langzamere tweede assemblage-call | uit |
| `--output` | `-o` | Output folder | `output/order_<naam>/` |
| `--xml` | - | Specifiek XML pad | `<output>/<partnumber>.xml` |

### Customer Opties

| Waarde | Beschrijving |
|--------|--------------|
| `auto` | Compatibiliteitsalias voor `base`; doet geen Vision-call |
| `elten` | ELTEN configuratie (forceer) |
| `rademaker` | Rademaker configuratie (forceer) |
| `base` | Basis configuratie (geen klant-specifieke regels) |

#### Klantconfiguratie

Automatische klantdetectie is uitgeschakeld om een extra Vision-call per batch
te vermijden. Gebruik standaard `base`. Geef `elten` of `rademaker` alleen
expliciet mee wanneer die informatie al uit order- of ERP-data bekend is.

**Wanneer specifieke klant (`elten`/`rademaker`) gebruiken:**

- Als je 100% zeker weet welke klant het is
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

De normale route gebruikt `gemini-3.6-flash`. Gebruik `--scan-depth deep` of
een expliciete modeloverride voor kritieke tekeningen die extra controle nodig
hebben. De bovenstaande benchmark is historisch en betreft een andere
Flash-preview; gebruik hem niet als actuele performancegarantie.

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

**Alleen XML** - bestandsnaam is gebaseerd op de input mapnaam:

```txt
input_folder/                  ← De map met PDFs die je inlaadt
└── PDF_XML_<MAPNAAM>.xml      ← Output XML in dezelfde map
```

### Single PDF Voorbeeld

```bash
python -m extractor.main /Users/tess/orders/10009043_1/tekening.pdf
```

Output:

```txt
/Users/tess/orders/10009043_1/
├── tekening.pdf
└── PDF_XML_10009043_1.xml     ← XML in dezelfde map als PDF
```

### Batch Voorbeeld

```bash
python -m extractor.main /Users/tess/orders/20260001/ -c auto
```

Output:

```txt
/Users/tess/orders/20260001/
├── tekening1.pdf
├── tekening2.pdf
├── tekening3.pdf
└── PDF_XML_20260001.xml       ← XML met mapnaam
```

### Custom Output

```bash
python -m extractor.main /Users/tess/orders/order123/ -o /Users/naam/Desktop/resultaten
```

Output:

```txt
/Users/naam/Desktop/resultaten/
└── PDF_XML_order123.xml
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

### Voorbeeld 3: Basisconfiguratie zonder klantdetectie

```bash
python -m extractor.main /Users/tess/orders/onbekende_order/ -c base
```

### Voorbeeld 4: Windows Paden

```cmd
python -m extractor.main C:\Users\Naam\tekeningen\order_123 -c base -o C:\output
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
python -m extractor.main "/Users/naam/My Documents/order folder" -c base
```

---

## Tips

1. **Gebruik standaard `base`**; haal een bekende klant bij voorkeur uit ERP
2. **Gebruik `--scan-depth auto`**; forceer `deep` alleen wanneer nodig
3. **Check de XML output** voor operator warnings (tapgaten, toleranties)
4. **Assembly detectie** - het systeem detecteert automatisch welke PDF de assembly is
5. **XML naamgeving** - De output heet `PDF_XML_<mapnaam>.xml` en staat in dezelfde map als de input PDFs
