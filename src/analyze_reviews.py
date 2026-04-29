import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
import pandas as pd
from tqdm import tqdm

from src.utils import load_env, safe_json_parse

INPUT_PATH = "data/raw_reviews.csv"
OUTPUT_PATH = "data/classified_reviews.csv"
PROMPT_PATH = "prompts/classify_reviews.txt"
MODEL = "claude-opus-4-7"
BATCH_SIZE = 20
MAX_RETRIES = 3
BATCH_DELAY = 1.0

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FALLBACK = {"theme": "Unknown", "subtheme": "Unknown", "sentiment": "Unknown"}


def _load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def _build_batch_message(system_prompt: str, batch: list[str]) -> str:
    numbered = "\n\n".join(f"Review {i + 1}: {text}" for i, text in enumerate(batch))
    return (
        f"{system_prompt}\n\n"
        f"Below are {len(batch)} app reviews. Classify each one.\n\n"
        f"{numbered}\n\n"
        f"Return ONLY a JSON array with exactly {len(batch)} objects, one per review, in the same order:\n"
        f'[{{"theme": "...", "subtheme": "...", "sentiment": "..."}}, ...]'
    )


def _classify_batch(client: anthropic.Anthropic, prompt: str, batch: list[str]) -> list[dict]:
    message_text = _build_batch_message(prompt, batch)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": message_text}],
            )
            raw = response.content[0].text
            parsed = safe_json_parse(raw)

            if isinstance(parsed, list) and len(parsed) == len(batch):
                return parsed, raw

            logger.warning(
                f"Attempt {attempt}: expected list of {len(batch)}, got {type(parsed).__name__} "
                f"len={len(parsed) if isinstance(parsed, list) else 'N/A'}"
            )
        except Exception as e:
            logger.warning(f"Attempt {attempt} API error: {e}")

        if attempt < MAX_RETRIES:
            time.sleep(2 ** attempt)

    logger.error(f"All {MAX_RETRIES} attempts failed for a batch of {len(batch)}. Using fallback.")
    return [FALLBACK.copy() for _ in batch], ""


def analyze() -> None:
    load_env()
    print(f"\n[2/3] Classifying reviews with {MODEL} ...")

    df = pd.read_csv(INPUT_PATH)
    texts = df["review_text"].tolist()
    prompt = _load_prompt()
    client = anthropic.Anthropic()

    themes, subthemes, sentiments, raw_outputs = [], [], [], []

    batches = [texts[i : i + BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]

    for batch in tqdm(batches, desc="  Batches", unit="batch"):
        results, raw = _classify_batch(client, prompt, batch)
        for item in results:
            themes.append(item.get("theme", FALLBACK["theme"]))
            subthemes.append(item.get("subtheme", FALLBACK["subtheme"]))
            sentiments.append(item.get("sentiment", FALLBACK["sentiment"]))
            raw_outputs.append(raw)
        time.sleep(BATCH_DELAY)

    df["theme"] = themes
    df["subtheme"] = subthemes
    df["sentiment"] = sentiments
    df["llm_raw_output"] = raw_outputs

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"  Classified {len(df)} reviews → {OUTPUT_PATH}")


if __name__ == "__main__":
    analyze()
