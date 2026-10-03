from fastapi import FastAPI

from app.routers import bills, health

app = FastAPI(
    title="BungeWatch API",
    description="Single core API serving the website, WhatsApp, and USSD channels.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(bills.router)

