"""Upload state management for MSE Analytica."""

import reflex as rx

from .parser.excel_parser import parse_excel_file
from .storage.json_store import (
    delete_parsed_file,
    load_index,
    save_parsed_data,
)


class UploadState(rx.State):
    """Manages file upload, parsing, and display state."""

    # Upload status
    is_uploading: bool = False
    upload_progress: int = 0

    # File list from index.json (sheets_parsed stored as comma-joined string)
    uploaded_files: list[dict[str, str]] = []

    # Feedback messages
    parse_error: str = ""
    success_message: str = ""

    # Currently selected file
    selected_file: str = ""

    def _refresh_file_list(self):
        """Reload uploaded files from index.json."""
        index = load_index()
        files = index.get("files", [])
        # Flatten sheets_parsed list to a string for Reflex rendering
        for f in files:
            if isinstance(f.get("sheets_parsed"), list):
                f["sheets_parsed"] = ", ".join(f["sheets_parsed"])
        self.uploaded_files = files

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Handle uploaded files: parse Excel and save as JSON."""
        self.is_uploading = True
        self.parse_error = ""
        self.success_message = ""
        yield

        parsed_count = 0
        errors = []

        for file in files:
            filename = file.filename or "unknown.xlsx"
            try:
                file_bytes = file.file.read()

                if not filename.lower().endswith((".xlsx", ".xls")):
                    errors.append(f"{filename}: Not an Excel file (.xlsx/.xls)")
                    continue

                parsed = parse_excel_file(file_bytes, filename)
                save_parsed_data(parsed)
                parsed_count += 1

            except ValueError as e:
                errors.append(f"{filename}: {e}")
            except Exception as e:
                errors.append(f"{filename}: Unexpected error - {e}")

        self.is_uploading = False
        self.upload_progress = 0
        self._refresh_file_list()

        if parsed_count > 0:
            self.success_message = (
                f"Successfully parsed {parsed_count} file(s)."
            )
        if errors:
            self.parse_error = " | ".join(errors)

    @rx.event
    def on_load(self):
        """Load file list when page loads."""
        self._refresh_file_list()

    @rx.event
    def select_file(self, filename: str):
        """Select a file for viewing."""
        self.selected_file = filename

    @rx.event
    def delete_file(self, filename: str):
        """Delete a parsed file and refresh the list."""
        self.parse_error = ""
        self.success_message = ""
        try:
            delete_parsed_file(filename)
            self.success_message = f"Deleted {filename}."
            self.selected_file = ""
        except Exception as e:
            self.parse_error = f"Error deleting {filename}: {e}"
        self._refresh_file_list()

    @rx.event
    def clear_messages(self):
        """Clear success and error messages."""
        self.parse_error = ""
        self.success_message = ""
