# Scraping, text-extraction (native + OCR), and AI-summarization logic lives here.
# This is deliberately NOT wired into any API router — it's meant to be invoked
# by a scheduled job (cron / task queue), not by an HTTP request. A bill-ingestion
# job can take minutes (PDF download + OCR); that's the wrong shape for a request
# handler, which should respond in milliseconds.
