"""Navigation sidebar -- 4-step workflow navigation."""
import reflex as rx


def nav_link(label: str, href: str, icon: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=16),
            rx.text(label, size="2", weight="medium"),
            spacing="2",
            align="center",
        ),
        href=href,
        class_name=(
            "flex items-center gap-2 px-3 py-2 rounded-md text-slate-400 "
            "hover:text-green-400 hover:bg-slate-800 transition-colors duration-150 "
            "w-full text-sm"
        ),
    )


def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Logo / title
            rx.box(
                rx.text(
                    "MSE",
                    class_name="text-green-400 font-bold text-lg tracking-tight",
                ),
                rx.text(
                    "Analytica",
                    class_name="text-slate-200 font-bold text-lg tracking-tight",
                ),
                class_name="flex gap-1 items-baseline px-3 py-4",
            ),
            rx.separator(class_name="border-slate-700 w-full"),
            # Navigation links
            rx.vstack(
                nav_link("Upload",    "/",          "upload"),
                nav_link("Screener",  "/screener",  "search"),
                nav_link("Portfolio", "/portfolio", "briefcase"),
                spacing="1",
                width="100%",
                padding_x="2",
                padding_y="3",
            ),
            spacing="0",
            width="100%",
            align="start",
        ),
        class_name=(
            "fixed left-0 top-0 h-full w-52 bg-slate-900 "
            "border-r border-slate-700 flex flex-col z-10"
        ),
    )
