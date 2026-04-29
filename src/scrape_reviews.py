import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from google_play_scraper import reviews, Sort

from src.utils import ensure_dirs, hash_text, load_env

OUTPUT_PATH = "data/raw_reviews.csv"


def scrape() -> None:
    load_env()
    ensure_dirs()

    app_id = os.environ["APP_ID"]
    app_name = os.environ.get("APP_NAME", app_id)
    lang = os.environ.get("APP_LANG", "en")
    country = os.environ.get("APP_COUNTRY", "us")
    count = int(os.environ.get("REVIEW_COUNT", 500))

    print(f"\n[1/3] Scraping {count} reviews for {app_name} ({app_id}) ...")

    result, _ = reviews(
        app_id,
        lang=lang,
        country=country,
        sort=Sort.NEWEST,
        count=count,
    )

    print(f"  Fetched {len(result)} raw reviews")

    rows = []
    for r in result:
        text = (r.get("content") or "").strip()
        if not text:
            continue
        rows.append(
            {
                "review_text": text,
                "rating": r.get("score"),
                "date": r.get("at"),
                "helpful_count": r.get("thumbsUpCount", 0),
                "replied": r.get("replyContent") is not None,
                "_hash": hash_text(text),
            }
        )

    df = pd.DataFrame(rows)

    before_dedup = len(df)
    df = df.drop_duplicates(subset="_hash").drop(columns=["_hash"])
    after_dedup = len(df)

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print(f"  After removing empty : {before_dedup}")
    print(f"  After deduplication  : {after_dedup}")
    print(f"  Saved to             : {OUTPUT_PATH}")


if __name__ == "__main__":
    scrape()
