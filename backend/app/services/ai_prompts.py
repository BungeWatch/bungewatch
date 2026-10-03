from app.utils.enums import Sector

SYSTEM_PROMPT = """You are summarizing Kenyan parliamentary bills for ordinary citizens.

Rules you must follow strictly:
1. Use ONLY the bill text provided. Do not use outside knowledge of Kenyan law,
   politics, or this bill's history — even if you recognize it.
2. Every pro and every con MUST cite the specific section/clause it comes from.
   If you cannot point to a specific section supporting a claim, do not include that claim.
3. If the bill amends another Act and you were not given that Act's text,
   do not guess what the amended provision originally said. Say so in `notes` instead.
4. Write the summary in plain language a person with no legal background can understand.
   Avoid repeating legal jargon from the bill without explaining it.
5. Stay neutral. Pros and cons are the bill's likely intended effects and possible
   concerns based on its text — not political opinions for or against it.
6. Choose sectors_affected ONLY from the provided fixed list. Do not invent new categories.
"""


def build_summary_prompt(bill_title: str, bill_text: str) -> str:
    """
    User-turn prompt, kept separate from the system prompt so the grounding
    RULES are never diluted by per-bill content — if combined into one
    string, text inside the bill itself could read like an instruction and
    confuse the model about which part is a rule vs. which part is data.
    """
    sector_list = ", ".join(s.value for s in Sector)
    return f"""Bill title: {bill_title}

Available sectors (choose only from this list): {sector_list}

Bill text:
---
{bill_text}
---

Summarize this bill following the rules you were given."""