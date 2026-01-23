# PDF Extractor - Installatie & Gebruik (ALES)

## Voor ALES Medewerkers

### Eenmalige Installatie

1. Open Windows Verkenner
2. Ga naar `\\ALESWS1\temp\PDF_EXTRACTOR2`
3. Dubbelklik op **`INSTALLEREN.bat`**
4. Volg de instructies (voer API key in als gevraagd)

### Dagelijks Gebruik

**Optie 1: Sleep & Drop**
- Sleep een map met PDFs op **`UITVOEREN.bat`**

**Optie 2: Dubbelklik**
- Dubbelklik op **`UITVOEREN.bat`**
- Voer het pad in wanneer gevraagd

**Optie 3: Command line**
```cmd
\\ALESWS1\temp\PDF_EXTRACTOR2\UITVOEREN.bat "\\ALESWS1\temp\PDF_EXTRACTOR2\10014675_2"
```

### Output

Het programma maakt een XML bestand aan in dezelfde map als de PDFs:
- Input: `\\ALESWS1\temp\PDF_EXTRACTOR2\10014675_2\`
- Output: `\\ALESWS1\temp\PDF_EXTRACTOR2\10014675_2\PDF_XML_10014675_2.xml`

---

## Technische Details (voor IT)

### Waarom werkt dit?

Python's virtual environment werkt niet direct met UNC paden (`\\server\share`). 
De oplossing: het batch script koppelt automatisch het UNC pad aan drive letter `Z:`.

### Vereisten

- Windows 10/11
- Python 3.10+ (met PATH)
- Netwerktoegang tot `\\ALESWS1\temp\`
- Gemini API key

### Bestanden

| Bestand | Doel |
|---------|------|
| `INSTALLEREN.bat` | Eenmalige setup (venv + packages) |
| `UITVOEREN.bat` | Dagelijks gebruik |
| `.env` | API key (niet delen!) |
| `venv/` | Python virtual environment |

### Problemen oplossen

**"Python niet gevonden"**
- Installeer Python van python.org
- Vink "Add Python to PATH" aan

**"Netwerkpad niet bereikbaar"**
- Check of je toegang hebt tot `\\ALESWS1\temp\`
- Vraag IT om toegangsrechten

**"API key fout"**
- Check de `.env` file
- Vraag nieuwe API key aan bij Tess

### Updates uitvoeren

1. Download nieuwe code van GitHub
2. Kopieer naar `\\ALESWS1\temp\PDF_EXTRACTOR2`
3. Draai `INSTALLEREN.bat` opnieuw
