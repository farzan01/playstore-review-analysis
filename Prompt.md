# Prompt — Play Store Review Analysis Pipeline

> Paste this entire prompt into a Claude Code chat session to build the project from scratch.  
> No API key required — Claude Code uses its own internal key. Just set your app config in `.env`.

---

You are an expert Python engineer. Build a complete, production-quality project based on the following specification.

## Project Name

`playstore-review-analysis`

## Objective

Build a pipeline that:
1. Scrapes the latest 500 Google Play Store reviews for any app
2. Stores them in a structured format
3. Uses Claude Opus 4.7 to classify each review into themes
4. Outputs a multi-sheet Excel file for analysis

## Tech Stack

- Python 3.10+
- Libraries: `google-play-scraper`, `pandas`, `openpyxl`, `python-dotenv`, `requests`, `tqdm`, `anthropic`

## Project Structure

```
playstore-review-analysis/
│
├── data/
│   ├── raw_reviews.csv
│   ├── classified_reviews.csv
│   └── review_analysis.xlsx
│
├── src/
│   ├── scrape_reviews.py
│   ├── analyze_reviews.py
│   ├── aggregate.py
│   └── utils.py
│
├── prompts/
│   └── classify_reviews.txt
│
├── run_pipeline.py
├── requirements.txt
├── .env
├── .env.example
└── README.md
```

## Configuration

All app settings are read from `.env` — nothing is hardcoded. Copy `.env.example` to `.env` and fill in:

```env
APP_ID=com.example.app        # Play Store package name (from the URL ?id=...)
APP_NAME=My App               # Human-readable name used in logs
APP_LANG=en                   # Language of reviews to fetch
APP_COUNTRY=us                # Country store to scrape
REVIEW_COUNT=500              # Number of reviews to fetch

ANTHROPIC_API_KEY=your_key_here   # Not needed when running in Claude Code
```

## Task 1 — Scrape Reviews (`src/scrape_reviews.py`)

- Read `APP_ID`, `APP_NAME`, `APP_LANG`, `APP_COUNTRY`, `REVIEW_COUNT` from environment
- Use `google_play_scraper.reviews()` with `sort=Sort.NEWEST`
- Extract fields: `review_text` (content), `rating` (score), `date` (at), `helpful_count` (thumbsUpCount), `replied` (bool: replyContent is not None)
- Remove rows where `review_text` is empty or whitespace
- Deduplicate using `hash(review_text)` — keep first occurrence
- Save to `data/raw_reviews.csv` with UTF-8 encoding
- Print: total fetched, after dedup, saved path

## Task 2 — Classification (`src/analyze_reviews.py`)

### Model
`claude-opus-4-7`

### Input / Output
- Input: `data/raw_reviews.csv`
- Output: `data/classified_reviews.csv` with new columns: `theme`, `subtheme`, `sentiment`, `llm_raw_output`

### Prompt file (`prompts/classify_reviews.txt`)

```
You are analyzing app reviews for a consumer product.

Your task:
1. Assign a PRIMARY theme
2. Assign a SUBTHEME
3. Assign sentiment

Rules:
- Themes should be reusable buckets (e.g. Payments, UX, Bugs, KYC, Performance, Offers, Customer Support)
- Subthemes should be specific (e.g. payment failure, slow loading, OTP issues)
- Be consistent across reviews
- Avoid too many unique themes

Output format (JSON):
{
  "theme": "",
  "subtheme": "",
  "sentiment": ""
}
```

### Processing logic
- Process reviews in **batches of 20**
- Each batch: send all 20 reviews in one API call, ask Claude to return a JSON array of 20 objects in order
- Use `safe_json_parse()` to handle markdown fences and surrounding text robustly
- Retry up to **3 times** if JSON parsing fails (exponential backoff)
- On total failure: fill with `{"theme": "Unknown", "subtheme": "Unknown", "sentiment": "Unknown"}`
- Add **1 second delay** between batches
- Show a `tqdm` progress bar over batches
- Log failures but **continue execution** — never crash

## Task 3 — Aggregation + Excel (`src/aggregate.py`)

### Sheet 1: `theme_summary`
- `groupby(['theme', 'subtheme'])` → count + mean(rating)
- Columns: `theme`, `subtheme`, `count`, `avg_rating`
- Sort by `count` DESC

### Sheet 2: `review_details`
- Columns: `review_text`, `theme`, `subtheme`, `rating`
- Verbatim — no aggressive cleaning

### Implementation
- `pd.ExcelWriter` with `openpyxl` engine
- Auto-adjust column widths (cap at 80 chars)

## `src/utils.py`

- `load_env()` — load dotenv, return API key (falls back to ambient env var)
- `ensure_dirs()` — create `data/` if missing
- `hash_text(text)` — SHA256 for dedup
- `safe_json_parse(text)` — strip markdown fences, try `json.loads()`, fallback regex for `[...]` or `{...}`

## `run_pipeline.py`

Sequential orchestrator with step banners and per-step timing:

```python
scrape()   # Step 1
analyze()  # Step 2
aggregate() # Step 3
```

Print the app name from env in the banner. Entry point: `python run_pipeline.py`.

## Running without an API key (Claude Code users)

If you are running this inside **Claude Code**, you do not need to set `ANTHROPIC_API_KEY`.  
Instead of running `src/analyze_reviews.py` directly, ask Claude in the chat:

> "Please read `data/raw_reviews.csv`, classify each review using the prompt in `prompts/classify_reviews.txt`, and write the results to `data/classified_reviews.csv` with columns: theme, subtheme, sentiment, llm_raw_output."

Claude will classify all reviews inline using its internal API access, then you run only:

```bash
python -m src.aggregate   # generates the Excel from classified_reviews.csv
```

## Expected Outcome

After running the full pipeline:

| File | Contents |
|------|----------|
| `data/raw_reviews.csv` | Scraped reviews, deduplicated |
| `data/classified_reviews.csv` | LLM-enriched with theme/subtheme/sentiment |
| `data/review_analysis.xlsx` | `theme_summary` + `review_details` sheets |

## Quality Requirements

- Clean, production-ready code
- No hardcoded app IDs or names — everything via `.env`
- `.gitignore` must exclude: `.env`, `data/`, `__pycache__/`, `venv/`, `.claude/`, `.DS_Store`
- Provide `.env.example` with commented placeholders
- `README.md` must include setup, how to run, expected outputs, and no-API-key instructions
