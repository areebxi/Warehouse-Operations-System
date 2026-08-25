from tkinter import Tk

from scripts.gui_theme import apply_theme

from .app import PreflightIssuesApp


def main() -> None:
    root = Tk()
    apply_theme(root)
    PreflightIssuesApp(root)
    root.deiconify()
    root.state("zoomed")
    root.lift()
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))
    root.focus_force()
    root.mainloop()

