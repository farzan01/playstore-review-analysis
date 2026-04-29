# Play Store Review Analysis

A production-ready pipeline that scrapes Google Play Store reviews for **any app**, classifies them into themes using Claude Opus 4.7, and produces a structured Excel report for product and support teams.

---

## How It Works

```
Play Store  →  raw_reviews.csv  →  classified_reviews.csv  →  review_analysis.xlsx
               (scrape)             (Claude LLM)               (Excel report)
```

1. **Scrape** — fetches the latest N reviews (newest-first) for any app ID
2. **Classify** — sends reviews to Claude Opus 4.7 in batches of 20; assigns theme, subtheme, and sentiment
3. **Aggregate** — groups results into a two-sheet Excel report

---

## Project Structure

```
playstore-review-analysis/
├── data/                        # generated at runtime (git-ignored)
│   ├── raw_reviews.csv
│   ├── classified_reviews.csv
│   └── review_analysis.xlsx
├── src/
│   ├── scrape_reviews.py        # Step 1 — scrape Play Store
│   ├── analyze_reviews.py       # Step 2 — classify with Claude
│   ├── aggregate.py             # Step 3 — aggregate to Excel
│   └── utils.py                 # shared helpers
├── prompts/
│   └── classify_reviews.txt     # classification prompt
├── run_pipeline.py              # pipeline orchestrator
├── requirements.txt
├── .env.example                 # copy → .env and fill in
└── .gitignore
```

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/<your-org>/playstore-review-analysis.git
cd playstore-review-analysis

python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the app and API key

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Find APP_ID in the Play Store URL:
#   https://play.google.com/store/apps/details?id=<APP_ID>
APP_ID=com.example.app
APP_NAME=My App
APP_LANG=en
APP_COUNTRY=us
REVIEW_COUNT=500

ANTHROPIC_API_KEY=your_key_here
```

---

## Running the Pipeline

```bash
python run_pipeline.py
```

**Example — scraping a food delivery app:**

```env
APP_ID=com.ubereats
APP_NAME=Uber Eats
APP_LANG=en
APP_COUNTRY=us
REVIEW_COUNT=500
```

You can also run each step individually:

```bash
python -m src.scrape_reviews
python -m src.analyze_reviews
python -m src.aggregate
```

---

## Expected Outputs

### `data/raw_reviews.csv`

| Column | Description |
|--------|-------------|
| `review_text` | Original review text (UTF-8) |
| `rating` | Star rating (1–5) |
| `date` | Review date (YYYY-MM-DD HH:MM:SS) |
| `helpful_count` | Upvotes on the review |
| `replied` | Whether the developer replied |

> Exact duplicates (same wording) are removed. Play Store often returns the same short review from multiple users.

### `data/classified_reviews.csv`

All columns from `raw_reviews.csv` plus:

| Column | Description |
|--------|-------------|
| `theme` | Primary theme (e.g. Payments, UX, Bugs, KYC) |
| `subtheme` | Specific subtheme (e.g. transfer delay, OTP issues) |
| `sentiment` | Positive / Negative / Neutral |
| `llm_raw_output` | Raw JSON response from Claude |

### `data/review_analysis.xlsx`

| Sheet | Purpose |
|-------|---------|
| `theme_summary` | Grouped by theme + subtheme; count + avg rating; sorted by volume |
| `review_details` | Verbatim reviews with labels — for manual inspection |

---

## Classification Themes

The LLM is instructed to use reusable buckets appropriate for consumer/fintech apps:

> Payments · UX · Bugs · KYC · Performance · Offers · Customer Support · General

Subthemes are specific (e.g. `transfer delay`, `OTP loop issue`, `cashback reduced`). You can customise the prompt at `prompts/classify_reviews.txt`.

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ID` | *(required)* | Play Store app package name |
| `APP_NAME` | same as `APP_ID` | Human-readable name for logs |
| `APP_LANG` | `en` | Review language |
| `APP_COUNTRY` | `us` | Country store to scrape |
| `REVIEW_COUNT` | `500` | Number of reviews to fetch |
| `ANTHROPIC_API_KEY` | *(required)* | Anthropic API key |

---

## Sample Use Case

A product manager wants to understand why ratings dropped last quarter. They point the pipeline at their app, run it, and immediately see in `theme_summary` that **"Payments → transfer delay"** accounts for 18 reviews with an average rating of 1.9★ — the top issue by volume. They drill into `review_details` to read exact user quotes before filing an incident report.
