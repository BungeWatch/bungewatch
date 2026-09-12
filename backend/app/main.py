from fastapi import FastAPI

from app.routers import bills, health

app = FastAPI(
    title="BungeWatch API",
    description="Single core API serving the website, WhatsApp, and USSD channels.",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(bills.router)

# Routers to add as we build them out:
# app.include_router(subscriptions.router)
# app.include_router(whatsapp_webhook.router)
# app.include_router(ussd_webhook.router)
