"""Packing List GUI: workbook / image path rows and run options."""

from __future__ import annotations

from tkinter import ttk


def add_path_and_option_rows(app, frm, add_row) -> None:
    """Rows 11–22: workbook, CL CSV, image dirs, logo-id / missing-logo options."""
    add_row(11, "Workbook path:", app.workbook_var, browse_dir=False)
    ttk.Label(frm, text="Custom Label Database (CSV):").grid(
        row=12, column=0, sticky="w", padx=(0, 10), pady=3
    )
    ttk.Entry(frm, textvariable=app.cl_csv_var, width=55).grid(
        row=12, column=1, sticky="we", pady=3
    )
    ttk.Button(frm, text="Browse…", command=app._browse_cl_csv).grid(
        row=12, column=2, padx=(8, 0), pady=3
    )

    add_row(13, "Output directory:", app.output_dir_var, browse_dir=True)
    add_row(14, "Apparel Image folder:", app.apparel_dir_var, browse_dir=True)
    add_row(15, "Normal Design folder:", app.logo_normal_dir_var, browse_dir=True)
    add_row(
        16,
        "Customise Single Position Design folder:",
        app.logo_custom_single_dir_var,
        browse_dir=True,
    )
    add_row(
        17,
        "Customise Double Position Design folder:",
        app.logo_custom_double_dir_var,
        browse_dir=True,
    )
    add_row(18, "PDF copy directory (optional):", app.pdf_copy_dir_var, browse_dir=True)
    add_row(19, "Excel copy directory (optional):", app.excel_copy_dir_var, browse_dir=True)

    ttk.Label(frm, text="Separate by Logo ID:").grid(
        row=20, column=0, sticky="w", padx=(0, 10), pady=3
    )
    ttk.Checkbutton(frm, text="Enable", variable=app.separate_by_logo_id_var).grid(
        row=20, column=1, sticky="w", pady=3
    )

    ttk.Label(frm, text="Logo ID threshold:").grid(
        row=21, column=0, sticky="w", padx=(0, 10), pady=3
    )
    app.logo_id_threshold_entry = ttk.Entry(frm, textvariable=app.logo_id_threshold_var, width=8)
    app.logo_id_threshold_entry.grid(row=21, column=1, sticky="w", pady=3)

    ttk.Label(frm, text="Re-run pipeline:").grid(row=22, column=0, sticky="w", padx=(0, 10), pady=3)
    app.run_missing_logo_cb = ttk.Checkbutton(
        frm, text="Enable", variable=app.run_missing_logo_pipeline_var
    )
    app.run_missing_logo_cb.grid(row=22, column=1, sticky="w", pady=3)
