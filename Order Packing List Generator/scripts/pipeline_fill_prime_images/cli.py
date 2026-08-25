import sys
from pathlib import Path

from .config import DEFAULT_OUTPUT_DIR
from .service import _token_from_step2_stem, fill_packing_columns


def main() -> None:
    """
    CLI entrypoint.

    Usage:
        python scripts/fill_prime_and_images.py <step2_csv> [output_csv]

    - step2_csv is required (output from step 2).
    - output_csv is optional; defaults to Output/3_fill_prime_and_images_{token}.csv.
    """
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/fill_prime_and_images.py <step2_csv> [output_csv]",
            file=sys.stderr,
        )
        raise SystemExit(1)

    step2_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        stem = step2_path.stem
        token = _token_from_step2_stem(stem)
        output_path = DEFAULT_OUTPUT_DIR / f"3_fill_prime_and_images_{token}.csv"

    df = fill_packing_columns(step2_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Filled {len(df)} rows -> {output_path}")

