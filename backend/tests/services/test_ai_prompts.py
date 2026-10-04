from app.services.ai_prompts import build_summary_prompt
from app.schemas.ai_summary import Sector


def test_build_summary_prompt_includes_bill_title_and_text():
    prompt = build_summary_prompt("Finance Bill 2026", "Section 1: ...")
    assert "Finance Bill 2026" in prompt
    assert "Section 1: ..." in prompt


def test_build_summary_prompt_lists_all_sectors():
    prompt = build_summary_prompt("Test Bill", "text")
    for sector in Sector:
        assert sector.value in prompt