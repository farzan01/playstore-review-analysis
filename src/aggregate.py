import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from openpyxl.utils import get_column_letter

from src.utils import ensure_dirs

INPUT_PATH = "data/classified_reviews.csv"
OUTPUT_PATH = "data/review_analysis.xlsx"


def _auto_fit_columns(worksheet) -> None:
    for col in worksheet.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        adjusted = min(max_len + 4, 80)
        worksheet.column_dimensions[col_letter].width = adjusted


def aggregate() -> None:
    ensure_dirs()
    print(f"\n[3/3] Aggregating results → {OUTPUT_PATH} ...")

    df = pd.read_csv(INPUT_PATH)

    # Sheet 1: theme_summary
    summary = (
        df.groupby(["theme", "subtheme"], as_index=False)
        .agg(count=("review_text", "count"), avg_rating=("rating", "mean"))
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )
    summary["avg_rating"] = summary["avg_rating"].round(2)

    # Sheet 2: review_details
    details = df[["review_text", "theme", "subtheme", "rating"]].copy()

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="theme_summary", index=False)
        details.to_excel(writer, sheet_name="review_details", index=False)

        _auto_fit_columns(writer.sheets["theme_summary"])
        _auto_fit_columns(writer.sheets["review_details"])

    print(f"  theme_summary  : {len(summary)} rows")
    print(f"  review_details : {len(details)} rows")
    print(f"  Saved to       : {OUTPUT_PATH}")


if __name__ == "__main__":
    aggregate()
