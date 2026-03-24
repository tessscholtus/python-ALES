"""Global constants for the extractor application."""

# ---------------------------------------------------------------------------
# Gemini Model Selection
# ---------------------------------------------------------------------------
#
# Override via CLI:  pdf-extract drawing.pdf --model gemini-2.0-flash
#
# Benchmarks (67 PDFs, 6 orders — ELTEN/Rademaker technische tekeningen):
#
#   Model                   Kosten/PDF   Snelheid   Accuraatheid
#   ─────────────────────────────────────────────────────────────────────
#   gemini-2.5-pro          €0.07        22.8 s     100% — geen fouten        ← DEFAULT
#   gemini-2.0-flash        €0.025 *     ~18 s      ~99% *
#   gemini-2.0-flash-lite   €0.010 *     ~14 s      ~96% *
#   gemini-1.5-pro          €0.080 *     ~28 s      ~99% *
#   gemini-1.5-flash        €0.020 *     ~20 s      ~98% *
#   gemini-1.5-flash-8b     €0.008 *     ~12 s      ~94% *
#
#   * = schatting gebaseerd op Google's officiële token-prijzen; niet zelf
#       gebenchmarkt op deze dataset. Benchmarkresultaten kunnen afwijken.
#
# Jaarlijkse kosten (schatting):
#
#   Volume        gemini-2.5-pro   gemini-2.0-flash   gemini-2.0-flash-lite
#   ──────────────────────────────────────────────────────────────────────
#   50.000 PDFs   €3.500           €1.250             €500
#   80.000 PDFs   €5.600           €2.000             €800
#
# Aanbeveling:
#   Productie          → gemini-2.5-pro      (hoogste betrouwbaarheid)
#   Kosten drukken     → gemini-2.0-flash    (goede balans)
#   Budget/testen      → gemini-2.0-flash-lite
#
# Opmerking over gemini-2.5-pro kosten:
#   Dit model gebruikt "thinking tokens" (interne redenering) die duurder zijn.
#   De €0.07/PDF is gebaseerd op gemeten gebruik; bij complexere tekeningen
#   kan dit hoger uitvallen.
# ---------------------------------------------------------------------------

DEFAULT_GEMINI_MODEL = "gemini-2.5-pro"

# Alle ondersteunde modellen met metadata
# Gebruik als referentie; het --model argument accepteert elke geldige Gemini model-ID
GEMINI_MODELS: dict[str, dict] = {
    "gemini-2.5-pro": {
        "cost_eur_per_pdf": 0.07,
        "benchmarked": True,
        "notes": "Beste kwaliteit, 100% accuraat op benchmark. Thinking model.",
    },
    "gemini-2.0-flash": {
        "cost_eur_per_pdf": 0.025,
        "benchmarked": False,
        "notes": "Snel en goedkoop. Goede keuze voor hoog volume.",
    },
    "gemini-2.0-flash-lite": {
        "cost_eur_per_pdf": 0.010,
        "benchmarked": False,
        "notes": "Goedkoopste optie. Meer kans op hallucinaties bij complexe tekeningen.",
    },
    "gemini-1.5-pro": {
        "cost_eur_per_pdf": 0.080,
        "benchmarked": False,
        "notes": "Ouder pro-model. Duurder dan 2.5-pro zonder voordeel.",
    },
    "gemini-1.5-flash": {
        "cost_eur_per_pdf": 0.020,
        "benchmarked": False,
        "notes": "Ouder flash-model. Stabiel maar 2.0-flash heeft de voorkeur.",
    },
    "gemini-1.5-flash-8b": {
        "cost_eur_per_pdf": 0.008,
        "benchmarked": False,
        "notes": "Kleinste model. Alleen geschikt voor simpele tekeningen.",
    },
}
