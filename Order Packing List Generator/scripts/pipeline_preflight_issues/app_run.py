import queue
import threading
from datetime import datetime
from pathlib import Path
from tkinter import DISABLED, END, NORMAL, messagebox

from pipeline_runtime.runner_utils import _FILENAME_UNSAFE, _shift_subdir_name
from pipeline_shipstation.orders_to_csv import fetch_tag_orders_to_csv
from pipeline_shipstation.sync_tags_xlsx import DEFAULT_XLSX_PATH
from pipeline_shipstation.tags_process_lookup import resolve_tag_list_processes

from .config import DEFAULT_CL_CSV, NO_ISSUES, PROJECT_ROOT
from .service import PreflightResult, run_preflight_audit


class PreflightRunMixin:

    def _append_log_ui(self, msg: str) -> None:
        self.log.insert(END, msg + "\n")
        self.log.see(END)


    def _enqueue_log(self, msg: str) -> None:
        if self._log_queue is not None:
            self._log_queue.put(msg)


    def _drain_log_queue(self) -> bool:
        if self._log_queue is None:
            return False
        while True:
            try:
                msg = self._log_queue.get_nowait()
            except queue.Empty:
                return False
            if msg is None:
                return True
            self._append_log_ui(msg)


    def _poll_log_queue(self) -> None:
        if self._drain_log_queue():
            return
        self.root.after(80, self._poll_log_queue)


    def _on_run(self) -> None:
        tag_mode = self.is_tag_mode()
        tags = self.selected_shipstation_tags() if tag_mode else []
        if tag_mode:
            if not tags:
                messagebox.showwarning("No tag", "Please select at least one ShipStation tag.")
                return
        elif not self.input_paths:
            messagebox.showwarning(
                "No input",
                "Add at least one input CSV file (or switch Input source to ShipStation tag(s)).",
            )
            return
        workbook_path = Path(self.workbook_var.get())
        if not workbook_path.is_file():
            messagebox.showerror("Workbook missing", f"Workbook not found:\n{workbook_path}")
            return
        cl_csv_path = Path((self.cl_csv_var.get() or "").strip() or str(DEFAULT_CL_CSV))
        if not cl_csv_path.is_file():
            messagebox.showerror(
                "Custom Label Database missing",
                f"Custom Label Database CSV not found:\n{cl_csv_path}",
            )
            return
        if not self._validate_image_folders():
            return

        output_dir = Path(self.output_dir_var.get())
        input_paths = list(self.input_paths)
        resolved_tags: list[tuple[int, str, str]] = []
        multi_tags = False
        gui_at_resolve = ""

        date_str = (self.date_var.get() or "").strip()
        shift_str = (self.shift_var.get() or "").strip()
        try:
            datetime.strptime(date_str, "%d-%m-%Y")
        except Exception:
            messagebox.showerror("Error", "Date must be in DD-MM-YYYY format.")
            return
        if not shift_str:
            messagebox.showerror("Error", "Please select a shift.")
            return
        # Nest issues output under {date}/{shift} Shift/ (file and tag modes)
        output_dir = output_dir / date_str / _shift_subdir_name(shift_str)

        if tag_mode:
            multi_tags = len(tags) > 1
            gui_at_resolve = "" if multi_tags else (self.process_number_var.get() or "").strip()
            resolved_tags, err = resolve_tag_list_processes(
                tags,
                shift_label=shift_str,
                gui_value=gui_at_resolve,
            )
            if err or not resolved_tags:
                messagebox.showerror("Error", err or "Could not resolve process numbers.")
                return
            for _tag_id, _tag_name, process_name in resolved_tags:
                if _FILENAME_UNSAFE.search(process_name):
                    messagebox.showerror(
                        "Error", 'Process number cannot contain / \\ : * ? " < > |'
                    )
                    return
            if len(resolved_tags) == 1 and not gui_at_resolve:
                self.process_number_var.set(resolved_tags[0][2])

        self.log.delete("1.0", END)
        self.run_btn.config(state=DISABLED)
        self._log_queue = queue.Queue()
        self.root.after(80, self._poll_log_queue)

        apparel_dir = self._optional_dir(self.apparel_dir_var)
        logo_normal_dir = self._optional_dir(self.logo_normal_dir_var)
        logo_custom_single_dir = self._optional_dir(self.logo_custom_single_dir_var)
        logo_custom_double_dir = self._optional_dir(self.logo_custom_double_dir_var)

        def worker() -> None:
            try:
                paths = input_paths
                if resolved_tags:
                    paths = []
                    for tag_id, tag_name, process_name in resolved_tags:
                        prefix = f"[{process_name}] " if multi_tags else ""
                        self._enqueue_log(
                            f"{prefix}Fetching ShipStation orders for tag '{tag_name}' "
                            f"(awaiting_shipment)…"
                        )
                        if multi_tags or not gui_at_resolve:
                            self._enqueue_log(
                                f"{prefix}Using process {process_name} from "
                                f"{DEFAULT_XLSX_PATH.name} for tag '{tag_name}' / "
                                f"shift '{shift_str}'."
                            )
                        csv_path = fetch_tag_orders_to_csv(
                            tag_id=int(tag_id),
                            tag_name=str(tag_name or ""),
                            date_dd_mm_yyyy=str(date_str),
                            shift_label=str(shift_str),
                            process_number=str(process_name),
                            input_root=PROJECT_ROOT / "Input",
                            log=self._enqueue_log,
                        )
                        paths.append(csv_path)
                out = run_preflight_audit(
                    paths,
                    workbook_path,
                    output_dir,
                    log_callback=self._enqueue_log,
                    cl_csv_path=cl_csv_path,
                    apparel_dir=apparel_dir,
                    logo_normal_dir=logo_normal_dir,
                    logo_custom_single_dir=logo_custom_single_dir,
                    logo_custom_double_dir=logo_custom_double_dir,
                    use_demo_images=self.use_demo_images_var.get(),
                )
                self._run_result = out
                if self._log_queue is not None:
                    self._log_queue.put(None)
                self.root.after(0, self._on_run_success)
            except Exception as exc:
                if self._log_queue is not None:
                    self._log_queue.put(None)
                self.root.after(0, self._on_run_error, str(exc))

        threading.Thread(target=worker, daemon=True).start()


    def _on_run_success(self) -> None:
        self._drain_log_queue()
        out = self._run_result
        self.run_btn.config(state=NORMAL)
        self._save_config()
        if out is NO_ISSUES:
            messagebox.showinfo("Done", "No preflight issues found.")
        elif isinstance(out, PreflightResult):
            messagebox.showinfo(
                "Done",
                f"Preflight issues written to:\n{out.path}\n\n"
                f"Unmatched SKU: {out.unmatched_count}\n"
                f"Missing Logo: {out.missing_logo_count}\n"
                f"Missing Apparel: {out.missing_apparel_count}\n"
                f"Issue rows written: {out.issue_row_count}",
            )
        elif out is None:
            messagebox.showerror("Error", "Preflight failed. See the log for details.")


    def _on_run_error(self, message: str) -> None:
        self._drain_log_queue()
        self._append_log_ui(f"Error: {message}")
        self.run_btn.config(state=NORMAL)
        messagebox.showerror("Error", message)

