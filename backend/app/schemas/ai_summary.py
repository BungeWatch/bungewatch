"""
Contains schemas for AI summary requests and responses.
"""
from pydantic import BaseModel, Field
from app.utils.enums import Sector

class ProCon(BaseModel):
    """
    A single pro or con, always tied to a specific section of the bill
    """
    point: str = Field(..., description="The pro or con itself, in plain language.")
    section_reference: str = Field(
        ..., description="The specific clause/section this claim is based on, e.g. 'Section 12(2)'."
    )


class SummaryOutput(BaseModel):
    """The full structured output the AI must produce for one bill."""
    summary_full: str = Field(..., description="Plain-language summary of what the bill does.")
    pros: list[ProCon]
    cons: list[ProCon]
    sectors_affected: list[Sector]
    notes: str | None = Field(
        default=None,
        description="Anything the model could not determine from the bill text alone — "
                    "e.g. 'this is an amendment bill and the parent Act's text was not provided.'"
    )