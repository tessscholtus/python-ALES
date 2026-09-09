from extractor.prompt_builder import build_technical_assembly_prompt
from extractor.types import ExtractionOptions, OrderDetails


def test_technical_analysis_contract_accepts_structured_assembly_result() -> None:
    result = OrderDetails(
        items=[
            {
                "partNumber": "10041748_1",
                "revision": "1",
                "bomItems": [
                    {
                        "position": "11",
                        "partNumber": "MD-16-04206",
                        "quantity": 8,
                        "description": "Round tube",
                        "material": "S235",
                    }
                ],
                "technicalAnalysis": {
                    "manufacturabilityStatus": "conditional",
                    "conclusion": "Maakbaar na bevestiging van coating.",
                    "positiveChecks": ["Maatketen klopt."],
                    "risks": [
                        {
                            "severity": "warning",
                            "category": "coating",
                            "summary": "Coating is niet volledig gespecificeerd.",
                            "evidence": "Coating Dynamic",
                        }
                    ],
                    "weldingNotes": ["Houd gaten lasvrij."],
                    "gdtRequirements": ["Haaksheid 0,2 t.o.v. datum A"],
                },
            }
        ]
    )

    item = result.items[0]
    assert item.revision == "1"
    assert item.bom_items is not None
    assert item.bom_items[0].quantity == 8
    assert item.technical_analysis is not None
    assert item.technical_analysis.manufacturability_status == "conditional"
    assert item.technical_analysis.risks[0].category == "coating"


def test_technical_analysis_option_and_prompt_are_explicit() -> None:
    options = ExtractionOptions(technicalAnalysis=True, isAssembly=True)
    prompt = build_technical_assembly_prompt("ELTEN", "Coating Dynamic")

    assert options.technical_analysis is True
    assert options.is_assembly is True
    assert "MAIN ASSEMBLY" in prompt
    assert "technicalAnalysis" in prompt
    assert "Do not invent" in prompt
