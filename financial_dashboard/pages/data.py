"""Data management page — upload financial statements and refresh prices."""
import reflex as rx

from ..components.file_list import file_list
from ..components.layout import page_layout
from ..components.upload_zone import selected_files_list, upload_zone
from ..state import UploadState

_NAVY   = "#4361EE"
_BLUE   = "#6B9FFF"
_POWDER = "#B4C5E4"
_TEXT   = "#DDE2F2"
_MUTED  = "#8892A8"
_FAINT  = "#5A627A"
_CARD   = "#161B27"
_BORDER = "#2A3050"


def data_page() -> rx.Component:
    return page_layout(
        rx.vstack(
            rx.vstack(
                rx.heading("Data Management", size="8", class_name="font-bold", style={"color": _TEXT}),
                rx.text("Upload and manage financial statement files", class_name="text-sm", style={"color": _MUTED}),
                spacing="0",
                align="start",
            ),
            # Upload section
            rx.box(
                rx.text("Upload Financial Statements", class_name="font-semibold text-sm mb-1", style={"color": _TEXT}),
                rx.text(".xls or .xlsx files from members.mse.mn", class_name="text-xs mb-4", style={"color": _MUTED}),
                upload_zone(),
                selected_files_list(),
                rx.cond(
                    UploadState.is_uploading,
                    rx.hstack(
                        rx.spinner(size="3"),
                        rx.text("Parsing files...", size="2", style={"color": _TEXT}),
                        align="center",
                        spacing="2",
                    ),
                ),
                rx.cond(
                    UploadState.success_message != "",
                    rx.callout(UploadState.success_message, icon="check", color_scheme="green", width="100%"),
                ),
                rx.cond(
                    UploadState.parse_error != "",
                    rx.callout(UploadState.parse_error, icon="triangle-alert", color_scheme="red", width="100%"),
                ),
                class_name="rounded-2xl p-6 shadow-sm w-full",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            # Uploaded companies
            rx.box(
                rx.text("Uploaded Companies", class_name="font-semibold text-sm mb-4", style={"color": _TEXT}),
                file_list(),
                class_name="rounded-2xl p-6 shadow-sm w-full",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            # Price refresh
            rx.box(
                rx.text("Price Data", class_name="font-semibold text-sm mb-2", style={"color": _TEXT}),
                rx.hstack(
                    rx.button(
                        rx.cond(
                            UploadState.is_refreshing_prices,
                            rx.spinner(size="2"),
                            rx.icon("refresh-cw", size=16),
                        ),
                        "Refresh Prices",
                        on_click=UploadState.refresh_prices,
                        disabled=UploadState.is_refreshing_prices,
                        class_name="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white transition-colors cursor-pointer",
                        style={"backgroundColor": _BLUE},
                    ),
                    rx.cond(
                        UploadState.price_refresh_summary != "",
                        rx.text(UploadState.price_refresh_summary, class_name="text-sm", style={"color": _MUTED}),
                    ),
                    spacing="3",
                    align="center",
                ),
                rx.text("Re-scrapes OHLCV data from old.mse.mn for all uploaded companies", class_name="text-xs mt-1", style={"color": _FAINT}),
                rx.cond(
                    UploadState.price_refresh_log.length() > 0,
                    rx.box(
                        rx.foreach(
                            UploadState.price_refresh_log,
                            lambda entry: rx.hstack(
                                rx.cond(
                                    entry["status"] == "ok",
                                    rx.icon("check-circle", size=14, class_name="text-green-400"),
                                    rx.icon("x-circle", size=14, class_name="text-red-400"),
                                ),
                                rx.text(entry["company"], class_name="text-sm font-medium", style={"color": _TEXT}),
                                rx.text(entry["detail"], class_name="text-xs", style={"color": _MUTED}),
                                spacing="2",
                                align="center",
                            ),
                        ),
                        class_name="mt-3 rounded-xl p-3 space-y-1 max-h-48 overflow-y-auto",
                        style={"backgroundColor": _POWDER + "10", "border": f"1px solid {_POWDER}20"},
                    ),
                ),
                class_name="rounded-2xl p-6 shadow-sm w-full",
                style={"backgroundColor": _CARD, "border": f"1px solid {_BORDER}"},
            ),
            spacing="5",
            width="100%",
            align="start",
        ),
    )
