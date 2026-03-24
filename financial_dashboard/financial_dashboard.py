"""MSE Analytica - Financial Dashboard for Mongolian Stock Exchange."""

import reflex as rx

from .components.file_list import file_list
from .components.layout import page_layout
from .components.upload_zone import selected_files_list, upload_zone
from .pages.company import company_page
from .pages.portfolio import portfolio_page
from .pages.screener import screener_page
from .state import AnalysisState, PortfolioState, UploadState


def index() -> rx.Component:
    """Main page: upload zone + parsed files table."""
    return page_layout(
        rx.vstack(
            rx.heading("Upload Financial Statements", size="6", class_name="text-slate-100"),
            rx.text(
                "Upload .xls or .xlsx files from members.mse.mn",
                class_name="text-slate-400 text-sm",
            ),
            # Demo shortcut
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("zap", size=18, class_name="text-green-400"),
                        rx.text(
                            "Demo Mode",
                            class_name="text-green-400 font-semibold text-sm",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Skip upload — instantly load all 7 pre-parsed MSE companies.",
                        class_name="text-slate-400 text-sm",
                    ),
                    rx.button(
                        rx.icon("play", size=16),
                        "Load 7 MSE Companies",
                        on_click=AnalysisState.load_demo_data,
                        class_name=(
                            "flex items-center gap-2 px-6 py-2 rounded-lg "
                            "bg-green-600 hover:bg-green-500 text-white font-semibold "
                            "transition-colors text-sm"
                        ),
                    ),
                    spacing="2",
                    align="start",
                ),
                class_name=(
                    "bg-green-500/5 border border-green-500/20 rounded-lg p-4 w-full"
                ),
            ),
            rx.separator(class_name="border-slate-700"),
            upload_zone(),
            selected_files_list(),
            rx.cond(
                UploadState.is_uploading,
                rx.hstack(
                    rx.spinner(size="3"),
                    rx.text("Parsing files...", size="2", class_name="text-slate-300"),
                    align="center",
                    spacing="2",
                ),
            ),
            rx.cond(
                UploadState.success_message != "",
                rx.callout(
                    UploadState.success_message,
                    icon="check",
                    color_scheme="green",
                    width="100%",
                ),
            ),
            rx.cond(
                UploadState.parse_error != "",
                rx.callout(
                    UploadState.parse_error,
                    icon="triangle-alert",
                    color_scheme="red",
                    width="100%",
                ),
            ),
            rx.separator(class_name="border-slate-700"),
            rx.text("Uploaded Companies", class_name="text-slate-200 font-semibold"),
            file_list(),
            spacing="4",
            width="100%",
        ),
    )


app = rx.App()
app.add_page(index, on_load=UploadState.on_load)
app.add_page(screener_page, route="/screener", on_load=AnalysisState.load_screener)
app.add_page(
    company_page,
    route="/company/[company]",
    on_load=AnalysisState.on_load_company,
)
app.add_page(portfolio_page, route="/portfolio")
