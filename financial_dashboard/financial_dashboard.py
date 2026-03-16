"""MSE Analytica - Financial Dashboard for Mongolian Stock Exchange."""

import reflex as rx

from .components.file_list import file_list
from .components.upload_zone import selected_files_list, upload_zone
from .pages.company import company_page
from .pages.screener import screener_page
from .state import AnalysisState, UploadState


def index() -> rx.Component:
    """Main page: upload zone + parsed files table."""
    return rx.box(
        rx.color_mode.button(position="top-right"),
        rx.container(
            rx.vstack(
                # Header
                rx.heading("MSE Analytica", size="7", trim="both"),
                rx.text(
                    "Upload financial statements from members.mse.mn",
                    color=rx.color("gray", 11),
                    size="3",
                ),
                rx.separator(),

                # Upload zone
                upload_zone(),
                selected_files_list(),

                # Upload progress spinner
                rx.cond(
                    UploadState.is_uploading,
                    rx.hstack(
                        rx.spinner(size="3"),
                        rx.text("Parsing files...", size="2"),
                        align="center",
                        spacing="2",
                    ),
                ),

                # Success message
                rx.cond(
                    UploadState.success_message != "",
                    rx.callout(
                        UploadState.success_message,
                        icon="check",
                        color_scheme="green",
                        width="100%",
                    ),
                ),

                # Error message
                rx.cond(
                    UploadState.parse_error != "",
                    rx.callout(
                        UploadState.parse_error,
                        icon="triangle-alert",
                        color_scheme="red",
                        width="100%",
                    ),
                ),

                rx.separator(),

                # Parsed files table
                rx.heading("Uploaded Files", size="5"),
                file_list(),

                spacing="4",
                width="100%",
                padding_y="6",
            ),
            max_width="900px",
        ),
        min_height="100vh",
    )


app = rx.App()
app.add_page(index, on_load=UploadState.on_load)
app.add_page(screener_page, route="/screener", on_load=AnalysisState.load_screener)
app.add_page(
    company_page,
    route="/company/[company]",
    on_load=AnalysisState.on_load_company,
)
