"""Step 4 — Portfolio: manage holdings and view blended health, sector, and optimization analysis."""
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
            rx.hstack(
                rx.input(
                    default_value=holding["weight_pct"],
                    on_blur=lambda v: PortfolioState.set_holding_weight(holding["company"], v),
                    class_name=(
                        "bg-transparent text-slate-300 text-sm font-mono w-16 text-right "
                        "border border-slate-700 rounded px-1"
                    ),
                    type="number",
                    min="0",
                    max="100",
                    step="0.1",
                ),
                rx.text("%", class_name="text-slate-500 text-sm"),
                spacing="1",
                align="center",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.text(
                holding["score_str"],
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


def holdings_tab_content() -> rx.Component:
    """Holdings tab: header with blended health + holdings table or empty state."""
    return rx.vstack(
        # Header row
        rx.hstack(
            rx.heading("Portfolio", size="6", class_name="text-slate-100"),
            rx.spacer(),
            rx.cond(
                PortfolioState.holdings.length() > 0,
                rx.box(
                    rx.text(
                        "Blended Health",
                        class_name="text-slate-400 text-xs uppercase tracking-wider",
                    ),
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
                            rx.table.column_header_cell(
                                "Company",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "Weight",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "Health Score",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "Label",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-3",
                            ),
                            rx.table.column_header_cell(
                                "",
                                class_name="px-4 py-3",
                            ),
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
        padding_top="4",
    )


def risk_metric_card(label: str, value, description: str) -> rx.Component:
    return rx.box(
        rx.text(label, class_name="text-slate-400 text-xs uppercase tracking-wider"),
        rx.text(value, class_name="text-2xl font-bold text-green-400 mt-1"),
        rx.text(description, class_name="text-slate-500 text-xs mt-1"),
        class_name="bg-slate-900 rounded-lg border border-slate-800 p-4",
    )


def optimization_row(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(row["company"], class_name="text-slate-300"),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.text(row["current"] + "%", class_name="text-slate-400 font-mono"),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.hstack(
                rx.text(row["optimal"] + "%", class_name="text-green-400 font-mono"),
                rx.text(row["arrow"], class_name="text-slate-500"),
                spacing="1",
            ),
            class_name="py-2 px-4",
        ),
        class_name="border-b border-slate-800",
    )


def analysis_tab_content() -> rx.Component:
    """Analysis tab: sector donut, risk metrics, frontier, optimization table."""
    return rx.cond(
        PortfolioState.can_show_analysis,
        # --- Analysis content ---
        rx.vstack(
            # Row 1: Sector donut (left) + 3 risk metric cards (right)
            rx.hstack(
                # Sector donut (per D-20)
                rx.box(
                    rx.text(
                        "Sector Allocation",
                        class_name="text-slate-400 text-xs uppercase tracking-wider mb-2",
                    ),
                    rx.recharts.pie_chart(
                        rx.recharts.pie(
                            data=PortfolioState.sector_chart_data,
                            data_key="value",
                            name_key="name",
                            inner_radius="50%",
                            outer_radius="80%",
                            fill="#4ade80",
                            label=True,
                        ),
                        rx.recharts.legend(),
                        width=300,
                        height=250,
                    ),
                    class_name="bg-slate-900 rounded-lg border border-slate-800 p-4 flex-1",
                ),
                # 3 risk cards (per D-12, D-13)
                rx.vstack(
                    risk_metric_card(
                        "Sortino Ratio",
                        PortfolioState.sortino_str,
                        "Risk-adjusted return (downside only)",
                    ),
                    risk_metric_card(
                        "Max Drawdown",
                        PortfolioState.max_drawdown_str,
                        "Largest peak-to-trough decline",
                    ),
                    risk_metric_card(
                        "CVaR (95%)",
                        PortfolioState.cvar_str,
                        "Expected loss in worst 5% of days",
                    ),
                    spacing="3",
                ),
                spacing="4",
                width="100%",
                align="start",
            ),
            # Row 2: Efficient frontier scatter plot (per D-15, D-16, D-17)
            rx.box(
                rx.text(
                    "Efficient Frontier",
                    class_name="text-slate-400 text-xs uppercase tracking-wider mb-2",
                ),
                rx.recharts.scatter_chart(
                    rx.recharts.scatter(
                        data=PortfolioState.frontier_data,
                        name="Frontier",
                        fill="#475569",
                    ),
                    rx.recharts.scatter(
                        data=PortfolioState.current_point_data,
                        name="Current",
                        fill="#4ade80",
                    ),
                    rx.recharts.x_axis(data_key="risk", name="Risk (%)", type_="number"),
                    rx.recharts.y_axis(data_key="return", name="Return (%)", type_="number"),
                    width="100%",
                    height=350,
                ),
                class_name="bg-slate-900 rounded-lg border border-slate-800 p-4 w-full",
            ),
            # Row 3: Optimization table + Apply button (per D-09, D-10)
            rx.box(
                rx.text(
                    "Optimization",
                    class_name="text-slate-400 text-xs uppercase tracking-wider mb-2",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                "Company",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-2",
                            ),
                            rx.table.column_header_cell(
                                "Current",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-2",
                            ),
                            rx.table.column_header_cell(
                                "Optimal",
                                class_name="text-slate-400 text-xs uppercase tracking-wider px-4 py-2",
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(PortfolioState.optimization_data, optimization_row),
                    ),
                    variant="ghost",
                    class_name="w-full",
                ),
                rx.button(
                    "Apply Optimal Weights",
                    on_click=PortfolioState.apply_optimal_weights,
                    class_name="mt-3 bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded text-sm font-medium",
                ),
                class_name="bg-slate-900 rounded-lg border border-slate-800 p-4 w-full",
            ),
            spacing="4",
            width="100%",
            align="start",
            padding_top="4",
        ),
        # --- Placeholder (fewer than 2 holdings with price data) ---
        rx.box(
            rx.vstack(
                rx.icon("bar-chart-3", size=40, class_name="text-slate-600"),
                rx.text(
                    "Add at least 2 companies with price history to see portfolio analysis.",
                    class_name="text-slate-400 text-center",
                ),
                spacing="2",
                align="center",
            ),
            class_name=(
                "bg-slate-900 rounded-lg border border-slate-800 "
                "p-16 w-full flex items-center justify-center"
            ),
        ),
    )


def portfolio_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger(
                        "Holdings",
                        value="holdings",
                        class_name=(
                            "text-slate-400 data-[state=active]:text-green-400 "
                            "data-[state=active]:border-b-2 data-[state=active]:border-green-400 "
                            "px-4 py-2 text-sm font-medium"
                        ),
                    ),
                    rx.tabs.trigger(
                        "Analysis",
                        value="analysis",
                        class_name=(
                            "text-slate-400 data-[state=active]:text-green-400 "
                            "data-[state=active]:border-b-2 data-[state=active]:border-green-400 "
                            "px-4 py-2 text-sm font-medium"
                        ),
                    ),
                    class_name="border-b border-slate-800",
                ),
                rx.tabs.content(holdings_tab_content(), value="holdings"),
                rx.tabs.content(analysis_tab_content(), value="analysis"),
                on_change=PortfolioState.on_tab_change,
                default_value="holdings",
                width="100%",
            ),
            spacing="5",
            width="100%",
            align="start",
        ),
    )
