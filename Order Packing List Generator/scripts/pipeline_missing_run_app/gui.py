import json
import queue
import sys
import threading
from datetime import date, datetime
from pathlib import Path
from tkinter import BOTH, DISABLED, END, NORMAL, StringVar, BooleanVar, Tk, filedialog, messagebox, ttk

from scripts.gui_theme import apply_theme, make_log_text, make_scrollable_form
from scripts.pipeline_packing_list_app.config import logs_directory
from scripts.pipeline_runtime.pipeline_log import PipelineLog
from scripts.pipeline_runtime.runner_utils import _sanitize_process_for_filename

from .core import (
    ALL_ORDERS_PATH,
    CONFIG_DIR,
    DEFAULT_MISSING_INPUT,
    DEFAULT_MISSING_TYPE,
    MISSING_PDF_SUBDIRS,
    MISSING_RUN_CONFIG,
    PROJECT_ROOT,
    resolve_missing_pdf_copy_dir,
    run_missing_run_from_all_orders,
)


class MissingRunApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Missing Run App")
        self.date_var = StringVar(value=date.today().strftime("%d-%m-%Y"))
        self.shift_var = StringVar()
        self.process_name_var = StringVar()
        self.missing_type_var = StringVar(value=DEFAULT_MISSING_TYPE)
        self.missing_input_var = StringVar(value=str(DEFAULT_MISSING_INPUT))
        self.all_orders_var = StringVar(value=str(ALL_ORDERS_PATH))
        self.apparel_dir_var = StringVar()
        self.logo_custom_single_dir_var = StringVar()
        self.logo_custom_double_dir_var = StringVar()
        self.logo_normal_dir_var = StringVar()
        self.pdf_copy_dir_var = StringVar()
        self.excel_copy_dir_var = StringVar()
        self.use_demo_images_var = BooleanVar(value=False)
        self._log_queue: queue.Queue[str | None] | None = None
        self._run_output_root: Path | None = None
        self._load_config()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_config(self) -> None:
        data = None
        for path in (MISSING_RUN_CONFIG, PROJECT_ROOT / "missing_run_config.json"):
            if not path.is_file():
                continue
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
                    break
            except Exception:
                continue
        if data is None:
            return
        # ponytail: never restore date — always open as today (field stays editable)
        self.shift_var.set(str(data.get("shift", "")).strip())
        self.process_name_var.set(str(data.get("process_name", "")).strip())
        missing_type = str(data.get("missing_type", "")).strip()
        if missing_type in MISSING_PDF_SUBDIRS:
            self.missing_type_var.set(missing_type)
        for key, var in [
            ("missing_input", self.missing_input_var), ("all_orders", self.all_orders_var), ("apparel_dir", self.apparel_dir_var),
            ("logo_custom_single_dir", self.logo_custom_single_dir_var), ("logo_custom_double_dir", self.logo_custom_double_dir_var),
            ("logo_normal_dir", self.logo_normal_dir_var),             ("pdf_copy_dir", self.pdf_copy_dir_var), ("excel_copy_dir", self.excel_copy_dir_var),
        ]:
            val = str(data.get(key, "")).strip()
            if val:
                var.set(val)
        if isinstance(data.get("use_demo_images"), bool):
            self.use_demo_images_var.set(data["use_demo_images"])
        legacy_logo_custom = str(data.get("logo_custom_dir", "")).strip()
        if not self.logo_custom_single_dir_var.get() and legacy_logo_custom:
            self.logo_custom_single_dir_var.set(legacy_logo_custom)

    def _save_config(self) -> None:
        data = {
            "date": self.date_var.get().strip(),
            "shift": self.shift_var.get().strip(),
            "process_name": self.process_name_var.get().strip(),
            "missing_type": self.missing_type_var.get().strip() or DEFAULT_MISSING_TYPE,
            "missing_input": self.missing_input_var.get().strip(),
            "all_orders": self.all_orders_var.get().strip(),
            "apparel_dir": (self.apparel_dir_var.get() or "").strip(),
            "logo_custom_single_dir": (self.logo_custom_single_dir_var.get() or "").strip(),
            "logo_custom_double_dir": (self.logo_custom_double_dir_var.get() or "").strip(),
            "logo_normal_dir": (self.logo_normal_dir_var.get() or "").strip(),
            "pdf_copy_dir": (self.pdf_copy_dir_var.get() or "").strip(),
            "excel_copy_dir": (self.excel_copy_dir_var.get() or "").strip(),
            "use_demo_images": self.use_demo_images_var.get(),
        }
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            MISSING_RUN_CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[missing run] config save failed ({MISSING_RUN_CONFIG}): {exc}", file=sys.stderr, flush=True)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill=BOTH, expand=True)

        footer = ttk.Frame(outer)
        footer.pack(side="bottom", fill="x")

        scroll_container, frm = make_scrollable_form(outer)
        scroll_container.pack(fill=BOTH, expand=True)

        ttk.Label(frm, text="Missing Run", style="Title.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 2)
        )
        ttk.Label(
            frm,
            text="Run a missing subset through the packing pipeline.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        def add_row(row: int, label: str, var: StringVar, browse_for_dir: bool | None) -> None:
            ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
            ttk.Entry(frm, textvariable=var, width=60).grid(row=row, column=1, sticky="we", pady=3)
            if browse_for_dir:
                ttk.Button(frm, text="Browse…", command=lambda v=var: self._browse_directory(v)).grid(row=row, column=2, padx=(8, 0), pady=3)

        ttk.Label(frm, text="Missing type:").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=3)
        type_frame = ttk.Frame(frm)
        type_frame.grid(row=2, column=1, columnspan=2, sticky="w", pady=3)
        ttk.Radiobutton(
            type_frame, text="Missing Logo", variable=self.missing_type_var, value="Missing Logo"
        ).pack(side="left", padx=(0, 16))
        ttk.Radiobutton(
            type_frame, text="Missing Apparel", variable=self.missing_type_var, value="Missing Apparel"
        ).pack(side="left")
        ttk.Label(frm, text="Date (DD-MM-YYYY):").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=3)
        ttk.Entry(frm, textvariable=self.date_var, width=25).grid(row=3, column=1, sticky="w", pady=3)
        ttk.Label(frm, text="Shift:").grid(row=4, column=0, sticky="w", padx=(0, 10), pady=3)
        self.shift_cb = ttk.Combobox(frm, textvariable=self.shift_var, values=["1st", "2nd", "3rd", "4th", "5th"], state="readonly", width=10)
        self.shift_cb.grid(row=4, column=1, sticky="w", pady=3)
        ttk.Label(frm, text="Process name:").grid(row=5, column=0, sticky="w", padx=(0, 10), pady=3)
        ttk.Entry(frm, textvariable=self.process_name_var, width=60).grid(row=5, column=1, sticky="we", pady=3, columnspan=2)
        ttk.Label(frm, text="Missing Input CSV:").grid(row=6, column=0, sticky="w", padx=(0, 10), pady=3)
        ttk.Entry(frm, textvariable=self.missing_input_var, width=60).grid(row=6, column=1, sticky="we", pady=3)
        ttk.Button(frm, text="Browse…", command=self._browse_missing_input).grid(row=6, column=2, padx=(8, 0), pady=3)
        ttk.Label(frm, text="All Orders CSV:").grid(row=7, column=0, sticky="w", padx=(0, 10), pady=3)
        ttk.Entry(frm, textvariable=self.all_orders_var, width=60).grid(row=7, column=1, sticky="we", pady=3)
        ttk.Button(frm, text="Browse…", command=self._browse_all_orders).grid(row=7, column=2, padx=(8, 0), pady=3)
        ttk.Label(frm, text="Use demo images:").grid(row=8, column=0, sticky="w", padx=(0, 10), pady=3)
        ttk.Checkbutton(
            frm,
            text="Offline testing — placeholders from Demo Images Database/",
            variable=self.use_demo_images_var,
        ).grid(row=8, column=1, columnspan=2, sticky="w", pady=3)
        add_row(9, "Apparel Image folder:", self.apparel_dir_var, browse_for_dir=True)
        add_row(10, "Normal Logo/Design folder:", self.logo_normal_dir_var, browse_for_dir=True)
        add_row(11, "Customise Single Position Logo/Design folder:", self.logo_custom_single_dir_var, browse_for_dir=True)
        add_row(12, "Customise Double Position Logo/Design folder:", self.logo_custom_double_dir_var, browse_for_dir=True)
        add_row(13, "PDF copy directory (optional):", self.pdf_copy_dir_var, browse_for_dir=True)
        ttk.Label(
            frm,
            text="PDFs copy into {PDF copy dir}/Missing Logo or …/Missing Apparel when set.",
            style="Muted.TLabel",
        ).grid(row=14, column=1, columnspan=2, sticky="w", pady=(0, 3))
        add_row(15, "Excel copy directory (optional):", self.excel_copy_dir_var, browse_for_dir=True)
        frm.columnconfigure(1, weight=1)

        self.run_btn = ttk.Button(footer, text="Run missing pipeline", style="Accent.TButton", command=self._on_run)
        self.run_btn.pack(anchor="w", pady=(8, 6))
        self.log = make_log_text(footer, height=10)
        self.log.insert(END, "Set Date, Shift, Process name, and CSV paths, then click 'Run missing pipeline'.")

    def _browse_missing_input(self) -> None:
        path = filedialog.askopenfilename(title="Select Missing Input CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.missing_input_var.set(path)

    def _browse_all_orders(self) -> None:
        path = filedialog.askopenfilename(title="Select All Orders CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.all_orders_var.set(path)

    def _browse_directory(self, var: StringVar) -> None:
        dirname = filedialog.askdirectory()
        if dirname:
            var.set(dirname)

    def _append_log_ui(self, msg: str) -> None:
        self.log.configure(state=NORMAL)
        self.log.insert(END, "\n" + msg)
        self.log.see(END)
        self.log.configure(state=DISABLED)

    def _replace_log_step(self, msg: str) -> None:
        self.log.configure(state=NORMAL)
        self.log.delete("1.0", END)
        self.log.insert(END, msg)
        self.log.see(END)
        self.log.configure(state=DISABLED)

    def _drain_log_queue(self) -> bool:
        if self._log_queue is None:
            return False
        last_step: str | None = None
        while True:
            try:
                msg = self._log_queue.get_nowait()
            except queue.Empty:
                if last_step is not None:
                    self._replace_log_step(last_step)
                return False
            if msg is None:
                if last_step is not None:
                    self._replace_log_step(last_step)
                return True
            last_step = msg

    def _poll_log_queue(self) -> None:
        if self._drain_log_queue():
            return
        self.root.after(200, self._poll_log_queue)

    def _on_closing(self) -> None:
        self._save_config()
        self.root.destroy()

    def _on_run(self) -> None:
        date_str = self.date_var.get().strip()
        process_name = self.process_name_var.get().strip()
        if not date_str or not process_name:
            messagebox.showerror("Error", "Date and Process name are required.")
            return
        missing_input = Path(self.missing_input_var.get().strip() or "")
        all_orders = Path(self.all_orders_var.get().strip() or "")
        if not missing_input.is_file():
            messagebox.showerror("Error", f"Missing Input CSV not found:\n{missing_input}")
            return
        if not all_orders.is_file():
            messagebox.showerror("Error", f"All Orders CSV not found:\n{all_orders}")
            return
        if not self.shift_var.get().strip():
            messagebox.showerror("Error", "Please select a shift.")
            return
        if not self.use_demo_images_var.get() and not (self.apparel_dir_var.get() or "").strip() and not (self.logo_normal_dir_var.get() or "").strip() and not (self.logo_custom_single_dir_var.get() or "").strip() and not (self.logo_custom_double_dir_var.get() or "").strip():
            messagebox.showwarning("No image directories", "Apparel/Logo folders are empty. PDFs will show placeholders.")

        shift = self.shift_var.get().strip()
        missing_type = self.missing_type_var.get().strip() or DEFAULT_MISSING_TYPE
        if missing_type not in MISSING_PDF_SUBDIRS:
            messagebox.showerror("Error", "Please choose Missing Logo or Missing Apparel.")
            return
        apparel_dir = (self.apparel_dir_var.get() or "").strip() or None
        logo_custom_single_dir = (self.logo_custom_single_dir_var.get() or "").strip() or None
        logo_custom_double_dir = (self.logo_custom_double_dir_var.get() or "").strip() or None
        logo_normal_dir = (self.logo_normal_dir_var.get() or "").strip() or None
        pdf_copy_dir = resolve_missing_pdf_copy_dir(
            (self.pdf_copy_dir_var.get() or "").strip() or None,
            missing_type,
        )
        excel_copy_dir = (self.excel_copy_dir_var.get() or "").strip() or None

        self.run_btn.configure(state=DISABLED)
        self._replace_log_step(f"Running missing pipeline for {date_str}, {process_name} ({missing_type})...")
        self._log_queue = queue.Queue()
        self.root.after(200, self._poll_log_queue)

        def worker() -> None:
            logs_root = logs_directory()
            logs_root.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            safe = _sanitize_process_for_filename(process_name)
            log_path = (logs_root / f"{safe}_{ts}.log").resolve()
            fp = open(log_path, "a", encoding="utf-8", buffering=1)

            def detail_fn(msg: str) -> None:
                now = datetime.now()
                line = f"{now:%Y-%m-%d %H:%M:%S},{now.microsecond // 1000:03d} | INFO | {msg}"
                try:
                    fp.write(line + "\n")
                    fp.flush()
                except OSError as exc:
                    print(f"[pipeline log] write failed ({log_path}): {exc}", file=sys.stderr, flush=True)
                print(line, flush=True)

            def on_step(msg: str) -> None:
                if self._log_queue is not None:
                    self._log_queue.put(msg)

            pl = PipelineLog(detail_fn, on_step)
            try:
                pl.detail(f"Full pipeline transcript (this run): {log_path}")
                if pdf_copy_dir:
                    pl.detail(f"PDF copy directory: {pdf_copy_dir}")
                output_root = run_missing_run_from_all_orders(
                    missing_input_path=missing_input,
                    all_orders_path=all_orders,
                    process_name=process_name,
                    date_dd_mm_yyyy=date_str,
                    shift=shift,
                    output_dir=PROJECT_ROOT / "Output",
                    apparel_dir=apparel_dir,
                    logo_custom_single_dir=logo_custom_single_dir,
                    logo_custom_double_dir=logo_custom_double_dir,
                    logo_normal_dir=logo_normal_dir,
                    pdf_copy_dir=pdf_copy_dir,
                    excel_copy_dir=excel_copy_dir,
                    log=pl,
                    use_demo_images=self.use_demo_images_var.get(),
                )
                self._run_output_root = output_root
                if self._log_queue is not None:
                    self._log_queue.put(None)
                self.root.after(0, self._on_run_success)
            except Exception as exc:
                if self._log_queue is not None:
                    self._log_queue.put(None)
                self.root.after(0, self._on_run_error, str(exc))
            finally:
                try:
                    fp.close()
                except OSError:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def _on_run_success(self) -> None:
        self._drain_log_queue()
        output_root = self._run_output_root
        self._append_log_ui(f"Done. Outputs written to:\n  {output_root}")
        self.run_btn.configure(state=NORMAL)
        self._save_config()
        messagebox.showinfo("Finished", f"Missing run completed successfully.\n\nOutputs written to:\n  {output_root}")

    def _on_run_error(self, message: str) -> None:
        self._drain_log_queue()
        self._append_log_ui(f"Error: {message}")
        self.run_btn.configure(state=NORMAL)
        self._save_config()
        messagebox.showerror("Error", message)


def launch_gui() -> None:
    root = Tk()
    apply_theme(root)
    MissingRunApp(root)
    root.deiconify()
    root.state("zoomed")
    root.lift()
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))
    root.focus_force()
    root.mainloop()
