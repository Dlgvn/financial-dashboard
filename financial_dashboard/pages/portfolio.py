"""Step 4 — Portfolio: manage holdings and view blended health."""
import reflex as rx
from ..components.layout import page_layout
from ..state import PortfolioState


def holding_row(holding: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.link(
                holding["company"],
                href=holding["url"],
                class_name="text-green-400 hover:text-green-300 font-medium",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(
                (holding["weight"] * 100).to_string() + "%",
                class_name="text-slate-300 text-sm font-mono",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(
                holding["score"].to_string(),
                class_name=rx.cond(
                    holding["color"] == "green",
                    "font-bold text-green-400",
                    rx.cond(
                        holding["color"] == "red",
                        "font-bold text-red-400",
                        "font-bold text-amber-400",
                    ),
                ),
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(holding["label"], class_name="text-slate-400 text-sm"),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.button(
                rx.icon("trash-2", size=14),
                on_click=PortfolioState.remove_from_portfolio(holding["company"]),
                class_name=(
                    "p-1 rounded text-slate-500 hover:text-red-400 "
                    "hover:bg-red-500/10 transition-colors"
                ),
                variant="ghost",
                size="1",
            ),
            class_name="py-3 px-4",
        ),
        class_name="border-b border-slate-800 hover:bg-slate-900/50 transition-colors",
    )


def portfolio_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Portfolio", size="6", class_name="text-slate-100"),
                rx.spacer(),
                rx.cond(
                    PortfolioState.holdings.length() > 0,
                    rx.box(
                        rx.text("Blended Health", class_name="text-slate-400 text-xs uppercase tracking-wider"),
                        rx.text(
                            PortfolioState.portfolio_health.to_string(),
                            class_name="text-2xl font-bold text-green-400",
                        ),
                        class_name="bg-slate-900 rounded-lg border border-slate-800 px-5 py-3 text-center",
                    ),
                    rx.box(),
                ),
                width="100%",
                align="center",
            ),
            # Empty state or holdings table
            rx.cond(
                PortfolioState.holdings.length() == 0,
                rx.box(
                    rx.vstack(
                        rx.icon("briefcase", size=40, class_name="text-slate-600"),
                        rx.text(
                            "No companies in portfolio yet.",
                            class_name="text-slate-400",
                        ),
                        rx.text(
                            "Go to the Screener and click + Add on any company.",
                            class_name="text-slate-500 text-sm",
                        ),
                        rx.link(
                            "Go to Screener →",
                            href="/screener",
                            class_name="text-green-400 hover:text-green-300 text-sm mt-2",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    class_name=(
                        "bg-slate-900 rounded-lg border border-slate-800 "
                        "p-16 w-full flex items-center justify-center"
                    ),
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Company",      class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3"),
                                rx.table.column_header_cell("Weight",       class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3"),
                                rx.table.column_header_cell("Health Score", class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3"),
                                rx.table.column_header_cell("Label",        class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3"),
                                rx.table.column_header_cell("",             class_name="px-4 py-3"),
                            ),
                            class_name="bg-slate-900/50",
                        ),
                        rx.table.body(
                            rx.foreach(PortfolioState.holdings, holding_row),
                        ),
                        variant="ghost",
                        class_name="w-full",
                    ),
                    class_name="bg-slate-900 rounded-lg border border-slate-800 overflow-hidden w-full",
                ),
            ),
            spacing="5",
            width="100%",
            align="start",
        ),
    )
