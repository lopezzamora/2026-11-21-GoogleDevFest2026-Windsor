"""Local LLM-as-judge for `custom_response_quality` (see eval_config.yaml).

Tailored for CampSeeker: evaluating grounding against NPS tool outputs,
adherence to read-only boundaries, and preservation of uncertainty.
"""

import os
import threading

from google import genai
from google.genai import types
from pydantic import BaseModel

_local = threading.local()


class _Verdict(BaseModel):
    score: int  # 1-5
    explanation: str


def _client() -> genai.Client:
    """One client per grading thread."""
    client = getattr(_local, "client", None)
    if client is None:
        client = _local.client = genai.Client()
    return client


def evaluate(instance):
    reference = instance.get("reference")
    rubric = (
        "You are evaluating CampSeeker, an evidence-grounded US National Park Service (NPS) "
        "campground discovery assistant.\n"
        "Grade the agent's final response on a 1-5 scale:\n"
        "- 5 (Excellent): Fully grounded in NPS evidence, concise, clearly explains amenities/tradeoffs, "
        "cites legitimate source links from tools, accurately reports uncertainty for missing/seasonal items, "
        "and respects read-only boundaries (does not claim to book or guarantee live vacancy).\n"
        "- 4 (Good): Accurate and helpful, well-grounded with only minor formatting or clarity flaws.\n"
        "- 3 (Fair): Partially helpful, but makes minor assumptions, misses important caveats (like seasonal closures "
        "or alert scopes), or includes slight inaccuracies.\n"
        "- 2 (Poor): Significant hallucinations, ignores user constraints (e.g. required showers/RV hookups), "
        "or fails to consult appropriate NPS tools.\n"
        "- 1 (Very Poor): Hallucinates campgrounds/amenities/URLs, claims to book campsites or guarantee live availability, "
        "or provides harmful/completely incorrect information.\n"
    )
    if reference:
        rubric += (
            "\nExpected Ground Truth / Reference Criteria:\n"
            f"{reference}\n"
            "Penalize responses that contradict or fail to meet this reference."
        )

    prompt = (
        f"{rubric}\n\n"
        f"User Prompt: {instance.get('prompt', '')}\n"
        f"Final Response: {instance.get('response', '')}\n"
        f"Full Agent Trace & Tool Calls: {instance.get('agent_data', '')}\n"
    )

    eval_model = os.getenv("EVAL_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

    response = _client().models.generate_content(
        model=eval_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,  # deterministic grading
            response_mime_type="application/json",
            response_schema=_Verdict,  # guaranteed schema-valid JSON
        ),
    )
    verdict = response.parsed
    if verdict is None:
        return {"score": 0, "explanation": response.text or ""}
    return {"score": max(1, min(5, verdict.score)), "explanation": verdict.explanation}
