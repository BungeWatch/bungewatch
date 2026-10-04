import re
import asyncio

from app.services.ai_summarizer import (
    count_tokens, call_model, validate_summary_output,
    asummarize_bill, MAX_INPUT_TOKENS,
)
from app.services.ai_prompts import SYSTEM_PROMPT, build_summary_prompt
from app.schemas.ai_summary import SummaryOutput
from app.utils.exceptions import AIModelError


def needs_chunking(bill_title: str, bill_text: str) -> bool:
    prompt = build_summary_prompt(bill_title, bill_text)
    return count_tokens(SYSTEM_PROMPT, prompt) > MAX_INPUT_TOKENS


def split_by_budget(text: str, max_chars: int, overlap_sentences: int = 1) -> list[str]:
    """
    Chunks long txt into smaller pieces, each under max_chars, with a small overlap between chunks.
    Overlap is measured in sentences, not characters, to avoid cutting off mid-sentence.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        if current_len + len(sentence) > max_chars and current:
            chunks.append(" ".join(current))
            current = current[-overlap_sentences:] if overlap_sentences else []
            current_len = sum(len(s) for s in current)
        current.append(sentence)
        current_len += len(sentence)

    if current:
        chunks.append(" ".join(current))
    return chunks


def _group_chunks_within_token_budget(bill_title: str, bill_text: str) -> list[str]:
    """
    Runs a conservative estimate of the number of characters that would exceed the token limit,
    then splits the bill into chunks that are guaranteed to be under the limit.
    """
    approx_chars_budget = MAX_INPUT_TOKENS * 3
    raw_chunks = split_by_budget(bill_text, max_chars=approx_chars_budget)

    verified: list[str] = []
    for chunk in raw_chunks:
        prompt = build_summary_prompt(bill_title, chunk)
        if count_tokens(SYSTEM_PROMPT, prompt) <= MAX_INPUT_TOKENS:
            verified.append(chunk)
        else:
            verified.extend(split_by_budget(chunk, max_chars=approx_chars_budget // 2))

    return verified


MERGE_SYSTEM_PROMPT = """You are consolidating multiple partial summaries of DIFFERENT PARTS
of the SAME bill into one final, coherent summary. The parts may overlap slightly.

Rules:
1. The partial summaries you're given were each generated from real, grounded
   text of this bill — do not second-guess or alter their facts.
2. Remove redundancy — overlapping parts may produce near-duplicate pros/cons;
   keep only one instance of each distinct point.
3. Keep every section_reference exactly as given — do not renumber or guess new ones.
4. Combine sectors_affected into a single deduplicated list.
5. Write one unified summary_full that reads as a single coherent description
   of the whole bill, not a list of "Part 1 does X, Part 2 does Y."
"""


def _build_merge_prompt(bill_title: str, partial_outputs: list[SummaryOutput]) -> str:
    sections_text = "\n\n".join(
        f"--- Partial summary {i+1} ---\n"
        f"Summary: {p.summary_full}\n"
        f"Pros: {[(pc.point, pc.section_reference) for pc in p.pros]}\n"
        f"Cons: {[(pc.point, pc.section_reference) for pc in p.cons]}\n"
        f"Sectors: {[s.value for s in p.sectors_affected]}"
        for i, p in enumerate(partial_outputs)
    )
    return f"""Bill title: {bill_title}

{sections_text}

Consolidate these partial summaries into one final SummaryOutput following your rules."""


async def _amerge(bill_title: str, partial_outputs: list[SummaryOutput]) -> SummaryOutput:
    merge_prompt = _build_merge_prompt(bill_title, partial_outputs)

    def _sync_merge() -> SummaryOutput:
        raw = call_model(MERGE_SYSTEM_PROMPT, merge_prompt)
        return validate_summary_output(raw)

    try:
        return await asyncio.to_thread(_sync_merge)
    except AIModelError as e:
        raise AIModelError("Claude", f"Merge step failed: {e.message}", original_error=e)


async def summarize_long_bill(bill_title: str, bill_text: str) -> SummaryOutput:
    chunks = _group_chunks_within_token_budget(bill_title, bill_text)

    partial_outputs: list[SummaryOutput] = []
    for chunk in chunks:
        output = await asummarize_bill(bill_title, chunk)
        partial_outputs.append(output)

    if len(partial_outputs) == 1:
        return partial_outputs[0]

    return await _amerge(bill_title, partial_outputs)