# missing_run_app.py



GUI/CLI helper tool for rebuilding a subset from `Missing/All Orders.csv` using query rows from `Missing/Missing Input.csv`, then generating one CSV, three Excel files, and one PDF using the shared step-6-style output pipeline.



## Purpose



- Re-run a small subset without processing the full ShipStation input again.

- Use `Missing/Missing Input.csv` as a list of anchor queries: **Date**, **Process**, **Item Number**.

- For each matching anchor row, expand to **all rows in the same order** for that same date and process.

- Deduplicate repeated queries that resolve to the same **Order Number** within the same date and process.

- Write outputs in the same format as normal step-6-style outputs: one CSV, three Excel files, and one PDF.



## Selection rules



For each row in `Missing/Missing Input.csv`:



1. Find an exact anchor row in `Missing/All Orders.csv` by **Date + Process + Item Number**.

2. Read the anchor row's **Order Number**.

3. Pull **all rows** from `Missing/All Orders.csv` whose **Date**, **Process**, and **Order Number** match that anchor.

4. If another query row resolves to the same `(date, process, order_number)`, skip it so the order is only included once.



The final combined DataFrame is also deduped by **Date + Process and Item Number** before output generation as a safety check.



## Input files



- **`Missing/All Orders.csv`**: Persistent log populated by the main pipeline from step-6 outputs.

- **`Missing/Missing Input.csv`**: Query file with columns:

  - `Date`

  - `Process`

  - `Item Number`



### Date handling



- `Missing Input.csv` accepts both `DD-MM-YYYY` and `DD/MM/YYYY`.

- Dates are normalized internally to `DD-MM-YYYY` before matching.



## Output



The GUI requires **Shift**. Outputs are written to:



```text

Output/{date}/{Shift} Shift/{process_name}/

```



The folder contains:



- `{process_name}.csv`

- `{ProcessBase}-Picking.xlsx`

- `Orders Details-P{ProcessBase}.xlsx`

- `DTF Des-P{ProcessBase}.xlsx`

- `{process_name}.pdf` (or split PDF parts if large)



### PDF / Excel copy directories



If set in the GUI:

- **PDF** copies go **directly into the selected folder** (no `{Shift} Shift` child folder).
- **Excel** copies go under `{Excel copy dir}/{Shift} Shift/` (same as the main Packing List pipeline).



## Usage



### GUI



```bash

python missing_run_app.py

```

Opens maximized and uses the shared GUI theme (`scripts/gui_theme.py`).

In the GUI:



- Set **Date**, **Shift** (required), and **Process name**.

- Confirm the paths for **Missing Input CSV** and **All Orders CSV**.

- Optionally set **Apparel**, **Normal Logo/Design**, **Customise Single Position**, and **Customise Double Position** folders (same stem-map rules as the main pipeline) and PDF/Excel copy directories.

- Click **Run missing pipeline**.



Settings are saved to `config/missing_run_config.json`. Write failures are printed to **stderr**.



### CLI



```bash

python missing_run_app.py DD-MM-YYYY PROCESS_NAME --shift 3rd

```



Optional arguments:



- `--missing-input`: Path to `Missing/Missing Input.csv`

- `--all-orders`: Path to `Missing/All Orders.csv`

- `--shift`: Shift label (e.g. `1st`). Recommended so outputs land under `Output/{date}/{Shift} Shift/{process_name}/`.



## Example



If `Missing Input.csv` contains:



- `11-03-2026, 4000, 11`

- `11-03-2026, 4000, 14`



and both anchors belong to order `206-2909605-5789927`, the tool expands that order once only and includes `Process 4000 Item-11` through `Process 4000 Item-14` a single time in the generated output.



## Errors and edge cases



- If `Missing/All Orders.csv` or `Missing/Missing Input.csv` is missing, the tool raises a file-not-found error.

- If `Missing/All Orders.csv` does not contain `Date`, `Process`, `Item Number`, or `Order Number`, the tool raises a clear validation error.

- The GUI requires a **Shift** selection before run.

- The GUI opens maximized and uses the shared theme in `scripts/gui_theme.py`.

- Blank query rows are ignored.

- Query rows that do not find an anchor match are skipped.

- If no query row matches anything, the run stops with `No matching rows found for any query in Missing Input CSV.`

- PDF/Excel copy failures are logged; they do not abort the run.



## Where it fits



This is a helper tool outside the main 8-step ShipStation pipeline. It reuses the shared output writer from `scripts/pipeline_runtime/runner_step6_outputs.py` (same format as a normal pipeline run after step 6) so its CSV, Excel, and PDF outputs match the main app.


