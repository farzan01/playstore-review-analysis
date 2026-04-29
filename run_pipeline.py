import os
import time

from dotenv import load_dotenv

from src.scrape_reviews import scrape
from src.analyze_reviews import analyze
from src.aggregate import aggregate

BANNER = "=" * 55


def main() -> None:
    load_dotenv()
    app_name = os.environ.get("APP_NAME", os.environ.get("APP_ID", "App"))

    print(BANNER)
    print(f"  {app_name} — Play Store Review Analysis Pipeline")
    print(BANNER)

    start_total = time.time()

    t0 = time.time()
    scrape()
    print(f"  Done in {time.time() - t0:.1f}s\n")

    t0 = time.time()
    analyze()
    print(f"  Done in {time.time() - t0:.1f}s\n")

    t0 = time.time()
    aggregate()
    print(f"  Done in {time.time() - t0:.1f}s\n")

    print(BANNER)
    print(f"  Pipeline complete in {time.time() - start_total:.1f}s")
    print(BANNER)
    print("\nOutputs:")
    print("  data/raw_reviews.csv        — scraped reviews")
    print("  data/classified_reviews.csv — LLM-enriched reviews")
    print("  data/review_analysis.xlsx   — Excel report")


if __name__ == "__main__":
    main()
