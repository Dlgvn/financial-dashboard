"""Step 4 — Portfolio: manage holdings and view blended health, sector, and optimization analysis."""
import reflex as rx
from ..components.layout import page_layout
from ..state import PortfolioState

_NAVY   = "#4361EE"
_BLUE   = "#6B9FFF"
_POWDER = "#B4C5E4"
_TEXT   = "#DDE2F2"
_MUTED  = "#8892A8"
_FAINT  = "#5A627A"
_CARD   = "#161B27"
_BORDER = "#2A3050"


def tip(text: str) -> rx.Component:
    return rx.tooltip(
        rx.icon("info", size=13, class_name="cursor-help shrink-0", style={"color": _POWDER + "70"}),
        content=text,
    )


def col_header(label: str, tooltip_text: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, class_name="text-xs uppercase tracking-wider", style={"color": _FAINT}),
            tip(tooltip_text),
            spacing="1",
            align="center",
        ),
        class_name="px-4 py-3",
    )


def holding_row(holding: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.tooltip(
                rx.link(
                    holding["company"],
                    href=holding["url"],
                    class_name="font-semibold hover:underline text-sm",
                    style={"color": _BLUE},
                ),
                content="Click to view full company analysis",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.hstack(
                rx.tooltip(
                    rx.hstack(
                        rx.input(
                            default_value=holding["weight_pct"],
                            on_blur=lambda v: PortfolioState.set_holding_weight(holding["company"], v),
                            class_name=(
                                "bg-transparent text-sm font-mono w-16 text-right "
                                "border rounded px-1"
                            ),
                            style={"color": _TEXT, "borderColor": _BORDER},
                            type="number",
                            min="0",
                            max="100",
                            step="0.1",
                        ),
                        rx.text("%", class_name="text-sm", style={"color": _MUTED}),
                        spacing="1",
                        align="center",
                    ),
                    content="Portfolio allocation weight for this company (0–100%). Weights auto-rebalance when adding/removing companies.",
                ),
                spacing="1",
                align="center",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.tooltip(
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
                content="Composite health score 0–100. Weighted blend of profitability (25%), liquidity (20%), solvency (20%), activity (15%), Altman Z-Score (10%), Piotroski F-Score (10%).",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.tooltip(
                rx.text(holding["label"], class_name="text-sm", style={"color": _MUTED}),
                content="Qualitative rating derived from the health score: Excellent (≥80), Good (60–79), Fair (40–59), Weak (<40).",
            ),
            class_name="py-3 px-4",
        ),
        rx.table.cell(
            rx.tooltip(
                rx.button(
                    rx.icon("trash-2", size=14),
                    on_click=PortfolioState.remove_from_portfolio(holding["company"]),
                    class_name="p-1 rounded hover:text-red-400 hover:bg-red-900/20 transition-colors",
                    style={"color": _MUTED},
                    variant="ghost",
                    size="1",
                ),
                content="Remove this company from your portfolio. Remaining weights will rebalance equally.",
            ),
            class_name="py-3 px-4",
        ),
        class_name="border-b hover:bg-blue-900/10 transition-colors",
        style={"borderColor": _BORDER},
    )


def holdings_tab_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.heading("Portfolio", size="6", class_name="font-bold", style={"color": _TEXT}),
                tip("Your selected companies and their portfolio allocation weights."),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.cond(
                PortfolioState.holdings.length() > 0,
                rx.tooltip(
                    rx.box(
                        rx.text(
                            "Blended Health",
                            class_name="text-xs uppercase tracking-wider",
                            style={"color": _MUTED},
                        ),
                        rx.text(
                            PortfolioState.portfolio_health.to_string(),
                            class_name="text-2xl font-bold",
                            style={"color": _NAVY},
                        ),
                        class_name="rounded-lg px-5 py-3 text-center",
                        style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
                    ),
                    content="Weighted average health score across all holdings, using each company's portfolio weight.",
                ),
                rx.box(),
            ),
            width="100%",
            align="center",
        ),
        rx.cond(
            PortfolioState.holdings.length() == 0,
            rx.box(
                rx.vstack(
                    rx.icon("briefcase", size=40, style={"color": _POWDER + "50"}),
                    rx.text("No companies in portfolio yet.", style={"color": _MUTED}),
                    rx.text(
                        "Go to the Screener and click + Add on any company.",
                        class_name="text-sm",
                        style={"color": _FAINT},
                    ),
                    rx.link(
                        "Go to Screener →",
                        href="/screener",
                        class_name="text-sm mt-2",
                        style={"color": _BLUE},
                    ),
                    spacing="2",
                    align="center",
                ),
                class_name="rounded-2xl p-16 w-full flex items-center justify-center",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            col_header("Company", "Legal name of the listed MSE company."),
                            col_header("Weight", "Target allocation weight in your portfolio (%). Must sum to 100%."),
                            col_header("Health Score", "Composite 0–100 financial health score. Higher is better."),
                            col_header("Label", "Qualitative rating: Excellent / Good / Fair / Weak."),
                            rx.table.column_header_cell("", class_name="px-4 py-3"),
                        ),
                        class_name="border-b",
                        style={"borderColor": _BORDER, "backgroundColor": _POWDER + "08"},
                    ),
                    rx.table.body(
                        rx.foreach(PortfolioState.holdings, holding_row),
                    ),
                    variant="ghost",
                    class_name="w-full",
                ),
                class_name="rounded-2xl overflow-hidden w-full",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
        ),
        spacing="5",
        width="100%",
        align="start",
        padding_top="4",
    )


def risk_metric_card(label: str, value, description: str, tooltip_text: str) -> rx.Component:
    return rx.tooltip(
        rx.box(
            rx.text(label, class_name="text-xs uppercase tracking-wider", style={"color": _MUTED}),
            rx.text(value, class_name="text-2xl font-bold mt-1", style={"color": _NAVY}),
            rx.text(description, class_name="text-xs mt-1", style={"color": _FAINT}),
            class_name="rounded-lg p-4 flex-1",
            style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
        ),
        content=tooltip_text,
    )


def optimization_row(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(row["company"], class_name="text-sm", style={"color": _TEXT}),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.tooltip(
                rx.text(row["current"] + "%", class_name="font-mono text-sm", style={"color": _MUTED}),
                content="Your current manual allocation weight.",
            ),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.tooltip(
                rx.hstack(
                    rx.text(row["optimal"] + "%", class_name="font-mono text-sm", style={"color": _BLUE}),
                    rx.text(row["arrow"], style={"color": _FAINT}),
                    spacing="1",
                ),
                content="Weight recommended by the Max Sharpe optimizer to maximize risk-adjusted return.",
            ),
            class_name="py-2 px-4",
        ),
        class_name="border-b",
        style={"borderColor": _BORDER},
    )


def stats_row(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(row["company"], class_name="text-sm font-medium", style={"color": _TEXT}),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.tooltip(
                rx.text(row["daily_return"], class_name="font-mono text-xs", style={"color": _MUTED}),
                content="Average daily return based on historical price data.",
            ),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.tooltip(
                rx.text(row["annual_return"], class_name="font-mono text-xs", style={"color": _BLUE}),
                content="Annualized return (daily return × 252 trading days).",
            ),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.tooltip(
                rx.text(row["daily_vol"], class_name="font-mono text-xs", style={"color": _MUTED}),
                content="Standard deviation of daily returns — measures day-to-day price variability.",
            ),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.tooltip(
                rx.text(row["annual_vol"], class_name="font-mono text-xs text-amber-400"),
                content="Annualized volatility (daily vol × √252). Higher means more risk.",
            ),
            class_name="py-2 px-4",
        ),
        rx.table.cell(
            rx.tooltip(
                rx.text(row["sharpe"], class_name="font-mono text-xs font-bold", style={"color": _NAVY}),
                content="Sharpe Ratio = Annualized Return / Annualized Volatility. Higher is better; >1 is considered good.",
            ),
            class_name="py-2 px-4",
        ),
        class_name="border-b",
        style={"borderColor": _BORDER},
    )


def analysis_tab_content() -> rx.Component:
    return rx.cond(
        PortfolioState.can_show_analysis,
        rx.vstack(
            # Row 1: Sector donut + risk cards
            rx.grid(
                rx.box(
                    rx.hstack(
                        rx.text(
                            "Sector Allocation",
                            class_name="text-xs uppercase tracking-wider",
                            style={"color": _MUTED},
                        ),
                        tip("Breakdown of your portfolio by sector, weighted by allocation. Helps identify concentration risk."),
                        spacing="2",
                        align="center",
                        class_name="mb-2",
                    ),
                    rx.recharts.pie_chart(
                        rx.recharts.pie(
                            rx.foreach(
                                PortfolioState.sector_chart_data,
                                lambda item: rx.recharts.cell(fill=item["fill"]),
                            ),
                            data=PortfolioState.sector_chart_data,
                            data_key="value",
                            name_key="name",
                            inner_radius="40%",
                            outer_radius="70%",
                            label=True,
                        ),
                        rx.recharts.legend(),
                        width="100%",
                        height=300,
                    ),
                    class_name="rounded-2xl p-4",
                    style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
                ),
                rx.vstack(
                    risk_metric_card(
                        "Sortino Ratio",
                        PortfolioState.sortino_str,
                        "Risk-adjusted return (downside only)",
                        "Sortino Ratio measures return per unit of downside risk only (ignores upside volatility). Higher is better; >1 is generally considered good.",
                    ),
                    risk_metric_card(
                        "Max Drawdown",
                        PortfolioState.max_drawdown_str,
                        "Largest peak-to-trough decline",
                        "Maximum Drawdown is the largest observed loss from a portfolio peak to a subsequent trough. A smaller (less negative) value indicates lower downside risk.",
                    ),
                    spacing="3",
                    height="100%",
                ),
                columns="2",
                spacing="4",
                width="100%",
            ),
            # Row 2: Efficient frontier
            rx.box(
                rx.hstack(
                    rx.text(
                        "Efficient Frontier",
                        class_name="text-xs uppercase tracking-wider",
                        style={"color": _MUTED},
                    ),
                    tip("Each grey dot is a randomly simulated portfolio. The blue dot is your current portfolio. Portfolios further up-left offer better return for less risk."),
                    spacing="2",
                    align="center",
                    class_name="mb-2",
                ),
                rx.recharts.scatter_chart(
                    rx.recharts.scatter(
                        data=PortfolioState.frontier_data,
                        name="Frontier",
                        fill=_POWDER + "50",
                    ),
                    rx.recharts.scatter(
                        data=PortfolioState.current_point_data,
                        name="Current",
                        fill=_BLUE,
                    ),
                    rx.recharts.x_axis(data_key="risk", name="Risk (%)", type_="number", tick={"fill": _FAINT, "fontSize": 11}),
                    rx.recharts.y_axis(data_key="return", name="Return (%)", type_="number", tick={"fill": _FAINT, "fontSize": 11}),
                    width="100%",
                    height=350,
                ),
                class_name="rounded-2xl p-4 w-full",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            # Row 3: Stats table
            rx.box(
                rx.hstack(
                    rx.text(
                        "Company Statistics",
                        class_name="text-xs uppercase tracking-wider",
                        style={"color": _MUTED},
                    ),
                    tip("Per-company return and risk statistics derived from historical price data."),
                    spacing="2",
                    align="center",
                    class_name="mb-2",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            col_header("Company", "MSE-listed company name."),
                            col_header("Daily Return", "Average daily price return."),
                            col_header("Annual Return", "Annualized return (daily × 252)."),
                            col_header("Daily Vol", "Standard deviation of daily returns."),
                            col_header("Annual Vol", "Annualized volatility (daily × √252)."),
                            col_header("Sharpe", "Sharpe Ratio = Annual Return / Annual Vol. Higher is better."),
                        ),
                        class_name="border-b",
                        style={"borderColor": _BORDER, "backgroundColor": _POWDER + "08"},
                    ),
                    rx.table.body(
                        rx.foreach(PortfolioState.individual_stats, stats_row),
                    ),
                    variant="ghost",
                    class_name="w-full",
                ),
                class_name="rounded-2xl p-4 w-full",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            # Row 4: Optimization
            rx.box(
                rx.hstack(
                    rx.text(
                        "Optimization",
                        class_name="text-xs uppercase tracking-wider",
                        style={"color": _MUTED},
                    ),
                    tip("Compares your current weights against mathematically optimal allocations using Modern Portfolio Theory."),
                    spacing="2",
                    align="center",
                    class_name="mb-2",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            col_header("Company", "MSE-listed company name."),
                            col_header("Current", "Your current portfolio weight."),
                            col_header("Optimal (Max Sharpe)", "Weight that maximizes the Sharpe Ratio — best risk-adjusted return."),
                        ),
                        class_name="border-b",
                        style={"borderColor": _BORDER, "backgroundColor": _POWDER + "08"},
                    ),
                    rx.table.body(
                        rx.foreach(PortfolioState.optimization_data, optimization_row),
                    ),
                    variant="ghost",
                    class_name="w-full",
                ),
                rx.hstack(
                    rx.tooltip(
                        rx.button(
                            rx.icon("shield", size=14),
                            "Min Risk",
                            on_click=PortfolioState.apply_min_risk_weights,
                            class_name="mt-3 px-4 py-2 rounded text-sm font-medium gap-1 text-white cursor-pointer",
                            style={"backgroundColor": _BLUE},
                        ),
                        content="Apply minimum-variance weights — minimizes portfolio volatility regardless of return.",
                    ),
                    rx.tooltip(
                        rx.button(
                            rx.icon("trending-up", size=14),
                            "Max Return",
                            on_click=PortfolioState.apply_max_return_weights,
                            class_name="mt-3 bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded text-sm font-medium gap-1 cursor-pointer",
                        ),
                        content="Apply maximum-return weights — concentrates in the highest-returning asset. High risk.",
                    ),
                    rx.tooltip(
                        rx.button(
                            rx.icon("zap", size=14),
                            "Max Sharpe (Efficient)",
                            on_click=PortfolioState.apply_optimal_weights,
                            class_name="mt-3 text-white px-4 py-2 rounded text-sm font-medium gap-1 cursor-pointer",
                            style={"backgroundColor": _NAVY},
                        ),
                        content="Apply Max Sharpe weights — the efficient frontier portfolio with the best risk-adjusted return.",
                    ),
                    spacing="3",
                    wrap="wrap",
                ),
                class_name="rounded-2xl p-4 w-full",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            spacing="4",
            width="100%",
            align="start",
            padding_top="4",
        ),
        rx.box(
            rx.vstack(
                rx.icon("bar-chart-3", size=40, style={"color": _POWDER + "50"}),
                rx.text(
                    "Add at least 2 companies with price history to see portfolio analysis.",
                    class_name="text-center",
                    style={"color": _MUTED},
                ),
                spacing="2",
                align="center",
            ),
            class_name="rounded-2xl p-16 w-full flex items-center justify-center",
            style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
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
                        class_name="data-[state=active]:border-b-2 px-4 py-2 text-sm font-medium",
                        style={"color": _MUTED},
                    ),
                    rx.tabs.trigger(
                        "Analysis",
                        value="analysis",
                        class_name="data-[state=active]:border-b-2 px-4 py-2 text-sm font-medium",
                        style={"color": _MUTED},
                    ),
                    class_name="border-b",
                    style={"borderColor": _BORDER},
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
