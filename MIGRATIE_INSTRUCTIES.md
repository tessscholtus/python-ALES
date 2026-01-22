# Migratie Instructies: google-generativeai → google-genai

**Datum:** 21-22 januari 2026  
**Reden:** De oude `google-generativeai` package is deprecated (niet meer ondersteund door Google)

---

## STAP 1: requirements.txt

### Zoek deze regel:
```
google-generativeai>=0.8.0
```

### Vervang door:
```
google-genai>=1.0.0
```

---

## STAP 2: extractor/utils.py

### Zoek deze code:
```python
def get_api_key() -> str:
    """
    Get Gemini API key from environment.
    
    Checks:
    1. GEMINI_API_KEY
    2. VITE_GEMINI_API_KEY
    """
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("VITE_GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Set GEMINI_API_KEY (or VITE_GEMINI_API_KEY) in your environment"
        )
    return key
```

### Vervang door:
```python
def get_api_key() -> str:
    """
    Get Gemini API key from environment.
    
    Checks:
    1. GEMINI_API_KEY
    2. VITE_GEMINI_API_KEY
    
    Also removes GOOGLE_API_KEY from environment to prevent
    the google-genai library warning about conflicting keys.
    """
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("VITE_GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "Set GEMINI_API_KEY (or VITE_GEMINI_API_KEY) in your environment"
        )
    
    # Remove GOOGLE_API_KEY to prevent google-genai library warning:
    # "Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY."
    if "GOOGLE_API_KEY" in os.environ:
        del os.environ["GOOGLE_API_KEY"]
    
    return key
```

---

## STAP 3: extractor/customer_detection.py

### 3A. Zoek deze imports (bovenaan het bestand):
```python
"""Customer detection service using Gemini Vision API."""

import logging

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .constants import DEFAULT_GEMINI_MODEL
```

### Vervang door:
```python
"""Customer detection service using Gemini Vision API."""

import base64
import logging

from google import genai
from google.genai import types

from .constants import DEFAULT_GEMINI_MODEL
```

---

### 3B. Zoek deze code in de `detect_customer_from_pdf_vision` functie:
```python
    try:
        api_key = get_api_key()
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(DEFAULT_GEMINI_MODEL)

        prompt = """You are analyzing a technical drawing PDF. Look at the BOM table (Bill of Materials) in the BOTTOM RIGHT corner of the drawing.
```

### Vervang door:
```python
    try:
        api_key = get_api_key()
        client = genai.Client(api_key=api_key)

        prompt = """You are analyzing a technical drawing PDF. Look at the BOM table (Bill of Materials) in the BOTTOM RIGHT corner of the drawing.
```

---

### 3C. Zoek deze code (PDF part creatie en API call):
```python
        # Create PDF part
        pdf_part = {
            "inline_data": {
                "mime_type": "application/pdf",
                "data": pdf_base64,
            }
        }

        response = await model.generate_content_async([prompt, pdf_part])
        response_text = response.text.strip().upper()
```

### Vervang door:
```python
        # Create PDF part
        pdf_part = types.Part.from_bytes(
            data=base64.b64decode(pdf_base64),
            mime_type="application/pdf",
        )

        response = await client.aio.models.generate_content(
            model=DEFAULT_GEMINI_MODEL,
            contents=[prompt, pdf_part],
        )
        response_text = response.text.strip().upper()
```

---

### 3D. Zoek deze exception handling (aan het einde van de try block):
```python
    except google_exceptions.GoogleAPIError as e:
        logger.warning(f"Vision-based customer detection failed (API error): {e}")
        return CustomerDetectionResult(
            customer="base",
            confidence="low",
            reason=f"Vision API error: {str(e)}",
        )
    except ValueError as e:
        logger.warning(f"Vision-based customer detection failed (value error): {e}")
        return CustomerDetectionResult(
            customer="base",
            confidence="low",
            reason=f"Value error: {str(e)}",
        )
```

### Vervang door:
```python
    except Exception as e:
        logger.warning(f"Vision-based customer detection failed: {e}")
        return CustomerDetectionResult(
            customer="base",
            confidence="low",
            reason=f"Vision API error: {str(e)}",
        )
```

---

## STAP 4: extractor/gemini_service.py

### 4A. Zoek deze imports (bovenaan het bestand):
```python
import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory
```

### Vervang door:
```python
from google import genai
from google.genai import types
```

---

### 4B. Zoek deze code in de `extract_order_details_from_pdf` functie:
```python
    # Configure Gemini
    api_key = get_api_key()
    genai.configure(api_key=api_key)

    # Create the model with JSON response
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": ORDER_DETAILS_SCHEMA,
            "temperature": 0.0,
            "top_p": 1.0,
            "top_k": 1,
        },
    )

    # Safety settings (allow all content for technical drawings)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    # Create PDF part
    pdf_part = {
        "inline_data": {
            "mime_type": "application/pdf",
            "data": pdf_base64,
        }
    }

    # Generate content
    response = await model.generate_content_async(
        [prompt, pdf_part],
        safety_settings=safety_settings,
    )
```

### Vervang door:
```python
    # Configure Gemini client (new google-genai API)
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)

    # Create PDF part
    pdf_part = types.Part.from_bytes(
        data=base64.b64decode(pdf_base64),
        mime_type="application/pdf",
    )

    # Generate content with JSON response
    response = await client.aio.models.generate_content(
        model=model_name,
        contents=[prompt, pdf_part],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ORDER_DETAILS_SCHEMA,
            temperature=0.0,
            top_p=1.0,
            top_k=1,
        ),
    )
```

---

## STAP 5: Na de code wijzigingen - Packages installeren (Windows / ALES Server)

### ⚠️ BELANGRIJK: Dit moet je doen NA het aanpassen van de code

De nieuwe `google-genai` package is een **compleet andere package** dan de oude `google-generativeai`. 
Je moet de oude package verwijderen en de nieuwe installeren.

---

### Optie A: Als je een bestaande venv hebt (AANBEVOLEN)

Open Command Prompt (cmd) of PowerShell **als Administrator** en navigeer naar de project folder:

```cmd
cd C:\temp\PDF_EXTRACTOR
```

Activeer de virtual environment:
```cmd
venv\Scripts\activate
```

Verwijder de oude package en installeer de nieuwe:
```cmd
pip uninstall google-generativeai -y
pip install -r requirements.txt --upgrade
```

---

### Optie B: Nieuwe venv aanmaken (als er problemen zijn)

Als er na Optie A nog steeds problemen zijn, maak dan een compleet nieuwe virtual environment:

```cmd
cd C:\temp\PDF_EXTRACTOR

REM Verwijder de oude venv folder
rmdir /s /q venv

REM Maak een nieuwe venv aan
python -m venv venv

REM Activeer de nieuwe venv
venv\Scripts\activate

REM Installeer alle packages opnieuw
pip install -r requirements.txt
```

---

### Controleren of het gelukt is

Na installatie kun je controleren of de juiste package is geïnstalleerd:

```cmd
pip list | findstr google
```

Je zou moeten zien:
```
google-genai          1.x.x    ← DIT IS CORRECT
```

Je zou NIET moeten zien:
```
google-generativeai   x.x.x    ← DIT IS DE OUDE PACKAGE
```

---

### Test de installatie

Voer een test uit om te controleren of alles werkt:

```cmd
python -m extractor.main "pad\naar\een\test\pdf\folder"
```

De FutureWarning over `google.generativeai` zou nu NIET meer moeten verschijnen.

---

## Samenvatting van bestanden die aangepast moeten worden:

| Bestand | Wat te doen |
|---------|-------------|
| `requirements.txt` | Package naam wijzigen |
| `extractor/utils.py` | GOOGLE_API_KEY verwijderen uit environment |
| `extractor/customer_detection.py` | Imports + API calls updaten |
| `extractor/gemini_service.py` | Imports + API calls updaten |

---

## Checklist voor de migratie

- [ ] STAP 1: `requirements.txt` aangepast
- [ ] STAP 2: `extractor/utils.py` aangepast
- [ ] STAP 3A-D: `extractor/customer_detection.py` aangepast (4 wijzigingen)
- [ ] STAP 4A-B: `extractor/gemini_service.py` aangepast (2 wijzigingen)
- [ ] STAP 5: Oude package verwijderd en nieuwe geïnstalleerd
- [ ] Test uitgevoerd - geen FutureWarning meer

---

## Contact

Bij vragen over deze migratie, neem contact op met Tess Scholtus.


