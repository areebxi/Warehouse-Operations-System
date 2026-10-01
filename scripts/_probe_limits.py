from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import check_line_limit as cl
is_exempt, offenders, iter_sources, warehouse_root = (
    cl.is_exempt,
    cl.offenders,
    cl.iter_sources,
    cl.warehouse_root,
)

files = [
    "Order Packing List Generator/scripts/pipeline_generate_packing_list_pdf/draw_page_impl.py",
    "Order Packing List Generator/scripts/pipeline_generate_packing_list_pdf/runtime_api.py",
    "Order Packing List Generator/scripts/pipeline_runtime/runner_step8_pdf.py",
    "Order Packing List Generator/scripts/pipeline_runtime/runner_step6_outputs.py",
    "shared/supply_method.py",
    "scripts/check_line_limit.py",
    "Purchase Order Generator/scripts/run_script.py",
    "shared/areeb_taxonomy.py",
    "Order Packing List Generator/scripts/gui_theme.py",
]
for f in files:
    p = ROOT / f
    n = len(p.read_text(encoding="utf-8", errors="replace").splitlines()) if p.exists() else -1
    print(f"{n:5}  {f}")

print("archive exempt", is_exempt(ROOT / "Custom Label Database/docs/archive/maker/download-images.ps1"))
bad = offenders(iter_sources([warehouse_root()]))
print("offenders", len(bad))
for n, p in bad[:15]:
    try:
        rel = p.resolve().relative_to(ROOT)
    except Exception:
        rel = p
    print(f"{n}\t{rel.as_posix()}")
