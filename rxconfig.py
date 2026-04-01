import os
import reflex as rx

config = rx.Config(
    app_name="financial_dashboard",
    # API_URL must be set as a Railway environment variable after first deploy.
    # Set it to the Railway-assigned HTTPS URL (e.g. https://your-app.up.railway.app).
    # Without this, the frontend WebSocket connects to localhost:8000 and all state events fail in production.
    api_url=os.environ.get("API_URL", "http://localhost:8000"),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)
