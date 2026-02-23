"""Drag-and-drop upload zone component."""

import reflex as rx

from ..state import UploadState


def upload_zone() -> rx.Component:
    """Drag-and-drop file upload area for Excel files."""
    return rx.box(
        rx.upload(
            rx.vstack(
                rx.icon("upload", size=40, color=rx.color("accent", 9)),
                rx.text(
                    "Drag & drop Excel files here, or click to browse",
                    size="3",
                    color=rx.color("gray", 11),
                ),
                rx.text(
                    "Accepts .xlsx and .xls files from members.mse.mn",
                    size="1",
                    color=rx.color("gray", 9),
                ),
                align="center",
                spacing="2",
                padding="40px",
            ),
            id="excel_upload",
            accept={
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                "application/vnd.ms-excel": [".xls"],
            },
            max_size=50 * 1024 * 1024,
            multiple=True,
            border=f"2px dashed {rx.color('accent', 7)}",
            border_radius="12px",
            padding="4px",
            width="100%",
            cursor="pointer",
            _hover={"border_color": rx.color("accent", 9)},
            on_drop=UploadState.handle_upload,
        ),
    )


def selected_files_list() -> rx.Component:
    """Show list of files selected for upload."""
    return rx.cond(
        rx.selected_files("excel_upload").length() > 0,
        rx.vstack(
            rx.text("Selected files:", weight="bold", size="2"),
            rx.foreach(
                rx.selected_files("excel_upload"),
                lambda f: rx.text(f, size="2", color=rx.color("gray", 11)),
            ),
            spacing="1",
            width="100%",
        ),
        rx.fragment(),
    )
