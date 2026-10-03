import asyncio

import anthropic
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ai_summary import SummaryOutput
from app.services.ai_prompts import SYSTEM_PROMPT, build_summary_prompt
from app.utils.exceptions import AIModelError, BillTooLongError

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

MODEL_NAME = "claude-sonnet-4-5"
MAX_OUTPUT_TOKENS = 4000
MAX_INPUT_TOKENS = 150_000

SUMMARY_TOOL = {
    "name": "record_bill_summary",
    "description": "Records the structured summary of a parliamentary bill.",
    "input_schema": SummaryOutput.model_json_schema(),
}


def count_tokens(system_prompt: str, user_prompt: str) -> int:
    """
    Counts the number of tokens in the system and user prompts.
    Routes the bill to chunking if it's too long rather than letting the model fail
    """
    response = client.messages.count_tokens(
        model=MODEL_NAME,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.input_tokens


def call_model(system_prompt: str, user_prompt: str) -> dict:
    """
    Calls the AI model.
    Raises AIModelError on any API-level failure.
    """
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[SUMMARY_TOOL],
            tool_choice={"type": "tool", "name": "record_bill_summary"},
        )
    except anthropic.APIError as e:
        raise AIModelError("Claude", f"API call failed: {e}", original_error=e)

    for block in response.content:
        if block.type == "tool_use":
            return block.input

    raise AIModelError("Claude", "Model did not return a tool_use block despite forced tool_choice.")


def validate_summary_output(raw: dict) -> SummaryOutput:
    """
    Ensures the model's output matches the expected schema. Raises AIModelError if validation fails.
    """
    try:
        return SummaryOutput.model_validate(raw)
    except ValidationError as e:
        raise AIModelError("Claude", f"Response failed schema validation: {e}", original_error=e)


def summarize_bill(bill_title: str, bill_text: str, max_retries: int = 2) -> SummaryOutput:
    """
    AI call to summarize a single bill.
    Raises BillTooLongError if the bill exceeds the model's safe context window.
    Retries upto `max_retries` times on AIModelError before giving up and raising the last error.
    """
    user_prompt = build_summary_prompt(bill_title, bill_text)

    token_count = count_tokens(SYSTEM_PROMPT, user_prompt)
    if token_count > MAX_INPUT_TOKENS:
        raise BillTooLongError(token_count, MAX_INPUT_TOKENS)

    last_error: AIModelError | None = None
    for attempt in range(max_retries + 1):
        try:
            raw = call_model(SYSTEM_PROMPT, user_prompt)
            return validate_summary_output(raw)
        except AIModelError as e:
            last_error = e
            continue  
    raise last_error

async def asummarize_bill(bill_title: str, bill_text: str, max_retries: int = 2) -> SummaryOutput:
    """
    The ONLY function pipeline/worker code should call. Runs the sync
    summarize_bill in a thread pool so it never blocks the event loop —
    this is what makes it safe to call from an arq worker handling
    multiple concurrent jobs on one loop.
    """
    return await asyncio.to_thread(summarize_bill, bill_title, bill_text, max_retries)
