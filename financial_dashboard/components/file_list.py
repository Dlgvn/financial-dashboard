"""Parsed files table component."""

import reflex as rx

from ..state import UploadState


def file_list() -> rx.Component:
    """Table showing all parsed/uploaded files."""
    return rx.cond(
        UploadState.uploaded_files.length() > 0,
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Company"),
                        rx.table.column_header_cell("Year"),
                        rx.table.column_header_cell("Original File"),
                        rx.table.column_header_cell("Sheets Parsed"),
                        rx.table.column_header_cell("Parsed At"),
                        rx.table.column_header_cell("Actions"),
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        UploadState.uploaded_files,
                        _file_row,
                    ),
                ),
                width="100%",
            ),
            width="100%",
            overflow_x="auto",
        ),
        rx.callout(
            "No files uploaded yet. Upload an Excel file to get started.",
            icon="info",
            color_scheme="gray",
            width="100%",
        ),
    )


def _file_row(file_info: dict[str, str]) -> rx.Component:
    """Render a single row in the files table."""
    return rx.table.row(
        rx.table.cell(rx.text(file_info["company"], weight="bold")),
        rx.table.cell(file_info["year"]),
        rx.table.cell(
            rx.text(file_info["original_file"], size="1"),
        ),
        rx.table.cell(
            rx.badge(file_info["sheets_parsed"], variant="soft", size="1"),
        ),
        rx.table.cell(
            rx.text(file_info["parsed_at"], size="1"),
        ),
        rx.table.cell(
            rx.icon_button(
                rx.icon("trash-2", size=14),
                color_scheme="red",
                variant="ghost",
                size="1",
                on_click=UploadState.delete_file(file_info["filename"]),
            ),
        ),
    )
