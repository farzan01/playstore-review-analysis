import hashlib
import json
import os
import re
from typing import Dict, List, Optional, Union

from dotenv import load_dotenv


def load_env() -> Optional[str]:
    load_dotenv()
    return os.environ.get("ANTHROPIC_API_KEY")


def ensure_dirs() -> None:
    os.makedirs("data", exist_ok=True)


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_json_parse(text: str) -> Optional[Union[List[Dict], Dict]]:
    """Extract JSON (array or object) from LLM output, handling markdown fences and surrounding text."""
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = text.replace("```", "").strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find a JSON array [...] in the text
    array_match = re.search(r"\[.*\]", text, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group())
        except json.JSONDecodeError:
            pass

    # Try to find a JSON object {...}
    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if obj_match:
        try:
            return json.loads(obj_match.group())
        except json.JSONDecodeError:
            pass

    return None
