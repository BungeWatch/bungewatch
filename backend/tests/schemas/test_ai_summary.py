import pytest
from pydantic import ValidationError
from app.schemas.ai_summary import SummaryOutput

VALID_OUTPUT = {
    "summary_full": "This bill does X.",
    "pros": [{"point": "Improves Y", "section_reference": "Section 3(1)"}],
    "cons": [{"point": "May increase Z", "section_reference": "Section 7"}],
    "sectors_affected": ["agriculture"],
    "notes": None,
}


def test_valid_output_parses():
    result = SummaryOutput.model_validate(VALID_OUTPUT)
    assert result.summary_full == "This bill does X."


def test_invalid_sector_is_rejected():
    bad = {**VALID_OUTPUT, "sectors_affected": ["farming"]}  # not in the enum
    with pytest.raises(ValidationError):
        SummaryOutput.model_validate(bad)


def test_missing_section_reference_is_rejected():
    bad = {**VALID_OUTPUT, "pros": [{"point": "Improves Y"}]}  # missing required field
    with pytest.raises(ValidationError):
        SummaryOutput.model_validate(bad)