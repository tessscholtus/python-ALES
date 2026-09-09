# Hybride maakbaarheidsanalyse vanuit PDF en STEP

Datum: 2026-09-07

## Doel

Het ultieme doel is een betrouwbaar analyse-systeem dat een totaalbeeld geeft
van de maakbaarheid van een product door informatie uit STEP en PDF te
combineren.

De STEP-engine levert de geometrische waarheid: vorm, classificatie, gaten als
geometrie, plaatdikte-kandidaten, zettingen, unfold, volume, gewicht,
contouren en snijlengtes. De PDF-extractor levert de maakintentie die vaak niet
of niet betrouwbaar uit STEP te halen is: materiaaltekst, oppervlaktebehandeling,
tapgat-callouts, passingen, toleranties, ruheid, GD&T, revisie, notities en BOM-
informatie.

Het systeem moet niet blind kiezen tussen bronnen. Het moet per veld vastleggen:
waarde, bron, methode, confidence, bewijspositie en eventuele conflicten.

## Huidige startpunten

### PDF-extractor

Locatie:

`G:/AccessApps/AlesMetaal/AlesERP-modern/PDF_reader`

Huidige sterke punten:

- Gemini Vision leest technische PDF-tekeningen.
- Extractie naar gestructureerde JSON volgens schema.
- XML-output met `PartNumber`, `Material`, `SurfaceTreatment`, `Holes`,
  `ToleratedLengths` en `PDF_Warnings`.
- Klantconfiguraties voor `elten`, `rademaker` en `base`.
- Detectie van tapgaten, gaten met toleranties, expliciete lengtetoleranties,
  oppervlaktebehandeling, materiaal en BOM-partnummers.

Huidige beperkingen:

- Primaire extractie hangt sterk aan Gemini-output en promptkwaliteit.
- Geen vaste regressieset met echte PDF's en verwachte extractie-output.
- PartNumber wordt in de huidige flow feitelijk uit de PDF-bestandsnaam gezet.
- Evidence zoals pagina, zone, crop of bounding box ontbreekt nog grotendeels.
- Geen formele conflictlaag tussen PDF, STEP en ERP.

### STEP-engine

Locatie:

`G:/AccessApps/AlesMetaal/AlesERP-modern/Spaceclaim_verv/alestest`

Huidige sterke punten:

- STEP-inlezen en productclassificatie.
- Classificaties: vlakke plaat, gezette plaat, profiel en anders.
- Detectie van geometrische gaten, vormgaten, countersinks en draadindicaties.
- Zetanalyse en unfold voor gezette plaat via FreeCAD/SheetMetal.
- XML/Excel-output richting ERP-achtige verwerking.
- Profiler, timing, cache, job-statussen en bestaande tests.
- Bestaande autoriteitsgedachte: analyse berekent, export schrijft.

Huidige beperkingen:

- STEP ziet niet altijd productintentie uit de tekening.
- STEP kan vaak geen betrouwbare conclusie trekken over tapgat-callouts,
  passingen zoals H7/H9, oppervlaktebehandeling, ruheid, GD&T, notities en
  klant-specifieke tekeningtekst.
- Een STEP-geometriegat is niet automatisch hetzelfde als een productie-callout.

## Bronautoriteit

### STEP is primair voor geometrie

- `final_class`
- plaat/profiel/anders-classificatie
- buitenmaten en bounding boxes
- geometrische plaatdikte-kandidaten
- volume, gewicht en oppervlak
- gaten als fysieke geometrie
- contouren en snijlengtes
- zettingen, bend-radii, bend-counts
- unfold-success en vlakke uitslagmaten

### PDF is primair voor maakintentie

- materiaaltekst zoals getekend
- oppervlaktebehandeling en nabehandeling
- tapgat-callouts zoals `M6`, `4x M8`
- passingen zoals `H7`, `H9`, `h7`, `f7`
- expliciete lengte-, diameter- en positietoleranties
- ruheid zoals `Ra`
- GD&T / vorm- en plaatstoleranties
- notities zoals ontbramen, lassen, ruimen, verzinken, poedercoaten
- revisie, tekeningnummer, titelblokvelden
- BOM-partnummers en aantallen uit de tekening

### ERP is primair voor bedrijfscontext

- klant en ordercontext
- materiaalprijzen, machinekeuzes en routingstandaarden
- levertijden, planning en voorraadcontext
- calculatieregels en standaardopslagen

## Gewenste eindarchitectuur

```text
PDF + STEP + ERP-context
        |
        v
Bestandskoppeling en normalisatie
        |
        +--> STEP-engine analyse
        |       - classificatie
        |       - geometrie
        |       - gaten
        |       - zettingen
        |       - unfold
        |       - timing/cache
        |
        +--> PDF analyse
        |       - layout/OCR zones
        |       - Gemini Vision extractie
        |       - optionele specialistische tekening-engine
        |       - evidence per veld
        |
        v
Evidence merge
        - bronautoriteit
        - confidence
        - conflict detectie
        - ontbrekende informatie
        |
        v
Maakbaarheidsanalyse
        - benodigde bewerkingen
        - risico's
        - review redenen
        - calculatie-input
        |
        v
Review UI / AlesERP concept / XML-JSON export
```

## Fase 0: Nulmeting en corpus

Doel: eerst meten wat de huidige systemen werkelijk kunnen.

Werk:

- Kies een vaste testset van echte orders met PDF + STEP.
- Start klein: 20 tot 30 representatieve orders.
- Groei later naar 100+ orders.
- Label per onderdeel de gewenste waarheid:
  - materiaal
  - dikte
  - oppervlaktebehandeling
  - gaten/tapgaten
  - passingen
  - toleranties
  - ruheid
  - GD&T indien relevant
  - zettingen
  - classificatie
  - benodigde bewerkingen
- Draai huidige STEP-engine en huidige PDF-extractor op dezelfde set.
- Leg runtime, kosten en fouten vast.

Acceptatie:

- Er is een vaste corpusmap of corpusmanifest.
- Elke testorder heeft verwachte velden.
- Runtime en foutpercentages zijn bekend.
- We weten per veld of STEP, PDF of mens nu de beste bron is.

Performance-meting:

- totale runtime per order
- STEP-runtime per order
- PDF-runtime per order
- Gemini-runtime per PDF
- API-kosten per order
- cache-hit-rate
- percentage onderdelen met review nodig

## Fase 1: Gezamenlijk resultaatcontract

Doel: een nieuw intern JSON-contract maken dat STEP- en PDF-evidence samen kan
dragen voordat er XML of ERP-output wordt gemaakt.

Werk:

- Definieer een `ManufacturabilityAnalysis` contract.
- Definieer per onderdeel:
  - identiteit
  - STEP-evidence
  - PDF-evidence
  - ERP-context
  - merged fields
  - conflicts
  - warnings
  - recommended route
- Definieer per veld:
  - `value`
  - `source`
  - `method`
  - `confidence`
  - `evidence_ref`
  - `status`
- Maak bronautoriteit expliciet:
  - STEP mag geometrievelden schrijven.
  - PDF mag maakintentievelden schrijven.
  - ERP mag bedrijfscontext schrijven.
  - Merge-laag mag combineren, maar niet ongemerkt overschrijven.
- Voeg conflictstatussen toe:
  - `ok`
  - `missing`
  - `conflict`
  - `low_confidence`
  - `needs_review`

Acceptatie:

- Contract is versieerbaar.
- Bestaande STEP-output kan naar het nieuwe contract worden gemapt.
- Bestaande PDF-output kan naar het nieuwe contract worden gemapt.
- Geen XML-writer hoeft businessregels te verzinnen.

Eerste velden:

- `part_number`
- `quantity`
- `material`
- `thickness_mm`
- `surface_treatment`
- `classification`
- `dimensions`
- `holes_geometry`
- `holes_callouts`
- `threaded_holes`
- `fits`
- `tolerances`
- `roughness`
- `bend_count`
- `unfold`
- `manufacturing_operations`
- `review_reasons`

## Fase 2: PDF-extractor stabiliseren

Doel: de huidige PDF-extractor minder afhankelijk maken van een enkele Gemini-
interpretatie.

Werk:

- Houd de bestaande Gemini-route operationeel.
- Voeg een voorbewerkingslaag toe:
  - PDF naar tekst waar mogelijk.
  - PDF-render naar images voor scan/vision.
  - zoneherkenning: titelblok, BOM, notes, views, tolerantietabel.
  - eenvoudige lokale regex-detectie voor bekende signalen.
- Laat Gemini gericht werken:
  - title block prompt
  - BOM prompt
  - hole/tap prompt
  - tolerance prompt
  - notes/finish prompt
- Voeg evidence toe:
  - pagina
  - zone
  - raw text
  - eventueel crop-pad of bounding box
- Normaliseer output naar het nieuwe contract uit Fase 1.

Acceptatie:

- PDF-output bevat niet alleen waarde, maar ook bronbewijs.
- Gemini mag `null` teruggeven bij twijfel.
- Bekende velden krijgen validatie.
- Er is onderscheid tussen geometrisch gat en PDF-callout.

Performance-aanpak:

- Eerst snelle tekst/OCR/regex.
- Gemini alleen aanroepen wanneer:
  - veld niet lokaal gevonden is;
  - lokaal gevonden veld onzeker is;
  - veld expliciet visueel/geometrisch op de tekening staat.
- Cache op PDF-hash + promptversie + modelnaam.

## Fase 3: Regressietests voor PDF

Doel: wijzigingen aan prompts, schema's en postprocessing veilig kunnen doen.

Werk:

- Maak golden fixtures voor echte PDF's.
- Leg verwachte JSON vast per PDF.
- Maak unit tests zonder echte Gemini-call:
  - schema-validatie
  - normalisatie
  - XML-output
  - warnings
  - conflictdetectie
- Maak aparte integration tests met echte Gemini-call:
  - klein aantal representatieve PDF's
  - niet standaard in elke snelle test-run
- Maak veldniveau-diffs:
  - verwacht vs gevonden
  - ontbrekend
  - extra/hallucinatie
  - confidence afwijking

Acceptatie:

- Elke PDF-promptwijziging kan tegen fixtures worden getest.
- Foutpositieven tellen zwaar, vooral bij tapgaten en toleranties.
- Testresultaten geven per veld oorzaak en bron.

Belangrijkste testvelden:

- materiaal
- oppervlaktebehandeling
- tapgaten
- getolereerde gaten
- H7/H9/passingen
- expliciete lengtetoleranties
- BOM-partnummers
- notities met nabewerking

## Fase 4: STEP-PDF koppeling

Doel: PDF en STEP betrouwbaar aan hetzelfde onderdeel of dezelfde assemblyregel
koppelen.

Werk:

- Normaliseer bestandsnamen en partnummers.
- Koppel op:
  - exact partnummer
  - bestandsnaam zonder revisievarianten
  - BOM-relaties
  - assembly occurrence
  - eventueel ERP-orderregel
- Rapporteer onbekoppelde bestanden.
- Rapporteer meerdere mogelijke matches.

Acceptatie:

- Geen automatische merge bij ambigue koppeling.
- Elk onderdeel krijgt `matched`, `unmatched` of `ambiguous`.
- Conflicts blijven zichtbaar.

## Fase 5: Evidence merge en conflictregels

Doel: van losse extracties naar een betrouwbaar totaalbeeld.

Werk:

- Implementeer bronautoriteit per veld.
- Detecteer conflicten zoals:
  - PDF-materiaal wijkt af van STEP/ERP.
  - PDF-dikte wijkt af van STEP-dikte.
  - PDF noemt tapgat, STEP toont alleen cilindrisch gat.
  - PDF noemt H9, STEP heeft geen onderscheidende feature.
  - PDF noemt coating, ERP/order niet.
- Maak conflict severity:
  - blocker
  - warning
  - info
- Maak review reasons geschikt voor een werkvoorbereider.

Acceptatie:

- Geen silent overwrite tussen STEP en PDF.
- Elke conflictregel heeft bronwaarden en uitleg.
- Merged output kan als concept naar ERP/review.

## Fase 6: Maakbaarheidsanalyse v1

Doel: vertaal evidence naar benodigde bewerkingen en risico's.

Werk:

- Bouw een rule-engine voor bewerkingen:
  - lasersnijden
  - zetten
  - tappen
  - ruimen
  - frezen
  - boren
  - verzinken/countersinken
  - ontbramen
  - lassen
  - poedercoaten
  - verzinken/electrogalv
  - parelstralen
- Bouw eenvoudige DFM-risico's:
  - ontbrekend materiaal
  - ontbrekende dikte
  - unfold mislukt
  - strakke tolerantie
  - passing vereist nabewerking
  - tapgat vereist extra bewerking
  - coating zonder duidelijke specificatie
  - PDF/STEP mismatch

Acceptatie:

- Output is bruikbaar voor calculatie/werkvoorbereiding.
- Elke bewerking is herleidbaar naar STEP, PDF of ERP.
- Geen automatische productiebeslissing zonder bewijs.

## Fase 7: Performance en schaalbaarheid

Doel: voorkomen dat de hybride analyse te traag of te duur wordt.

Werk:

- Maak timing per fase verplicht.
- Gebruik cache op:
  - STEP-hash
  - PDF-hash
  - promptversie
  - modelversie
  - extractorversie
- Verwerk batches parallel met limieten.
- Maak een snelle modus:
  - STEP + lokale PDF-tekst + bestaande cache
- Maak een volledige modus:
  - STEP + OCR/layout + Gemini + specialistische checks
- Maak een review-only modus:
  - alleen conflicten en ontbrekende velden opnieuw analyseren.

Acceptatie:

- Per order is zichtbaar waar tijd en kosten zitten.
- Gemini wordt niet opnieuw aangeroepen voor ongewijzigde PDF's.
- Grote orders kunnen gefaseerd verwerkt worden.

## Fase 8: Specialistische tekening-engine benchmark

Doel: bepalen of een gespecialiseerde technische-tekening-engine waarde toevoegt
naast Gemini.

Kandidaten:

- Werk24
- Azure Document Intelligence custom/layout
- Google Document AI layout parser
- eventueel eigen lokale OCR/layout-pipeline later

Benchmarkvelden:

- GD&T
- toleranties
- passingen
- tapgaten
- materiaal
- surface treatment
- ruheid
- title block
- BOM
- evidence/bounding boxes
- kosten en runtime

Acceptatie:

- Beslissing op basis van eigen Ales-corpus.
- Specialistische engine wordt alleen toegevoegd als hij meetbaar minder review
  of minder fouten oplevert.
- Geen vendor lock-in in het interne contract.

## Fase 9: Review UI

Doel: werkvoorbereiding snel laten beoordelen wat het systeem niet zeker weet.

Werk:

- Toon per onderdeel:
  - STEP-resultaten
  - PDF-resultaten
  - merged conclusie
  - conflicten
  - bewijsregels
  - waarschuwingen
- Toon PDF-crop of pagina/zone bij elk PDF-veld.
- Correcties opslaan als nieuwe fixtures.
- Correcties later gebruiken om regels/prompts te verbeteren.

Acceptatie:

- Review is sneller dan handmatig vanaf nul analyseren.
- Correcties verdwijnen niet in losse notities.
- Elke correctie kan een regressietest worden.

## Fase 10: ERP-integratie

Doel: bewezen analyse gecontroleerd meenemen naar AlesERP.

Werk:

- Start met concept-only output.
- Exporteer naar JSON/XML die AlesERP kan lezen.
- Maak statusvelden:
  - `ready_for_erp`
  - `needs_review`
  - `blocked`
  - `failed`
- Blokkeer automatische doorgang bij blocker-conflicts.
- Log elke bron en beslissing.

Acceptatie:

- Geen definitieve ERP-boeking bij onzekerheden.
- Werkvoorbereider ziet waarom een order wel/niet klaar is.
- Output is reproduceerbaar vanuit dezelfde PDF/STEP-input.

## Eerste verdiepingsonderwerpen

De volgende stap is Fase 1 tot en met Fase 3 verdiepen:

1. Fase 1: exact JSON-resultaatcontract en veldautoriteit.
2. Fase 2: concrete PDF-extractiestrategie met zones, prompts, cache en evidence.
3. Fase 3: testcorpus, golden files en regressieprotocol.

## Open ontwerpvragen

- Welke 20 tot 30 orders vormen de eerste representatieve testset?
- Welke PDF-velden zijn absoluut blocker als ze ontbreken?
- Welke toleranties veroorzaken altijd nabewerking?
- Wanneer is een PDF/STEP conflict blocker en wanneer alleen warning?
- Welke output moet eerst naar AlesERP: JSON, XML of beide?
- Wat is de maximale acceptabele runtime per order?
- Wat is de maximale acceptabele Gemini/API-kost per order?
- Welke velden moeten zichtbaar zijn in de eerste review UI?

## Werkprincipes

- Eerst meten, daarna verbeteren.
- STEP en PDF niet door elkaar laten overschrijven.
- Elk belangrijk veld krijgt bewijs.
- Foutpositieven zijn gevaarlijker dan ontbrekende lage-confidence velden.
- Promptwijzigingen zijn codewijzigingen en krijgen regressietests.
- Performance is een acceptatiecriterium, geen latere optimalisatie.
