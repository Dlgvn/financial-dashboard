import reflex as rx

config = rx.Config(
    app_name="financial_dashboard",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)