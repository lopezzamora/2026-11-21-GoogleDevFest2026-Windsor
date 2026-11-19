"""Local LLM-as-judge for `valid_trip_plan_rate` (Slide 9 of DevFest 2026).

CampSeeker Valid Trip Plan Rate:
Share of tested conversations where the trip:
(a) honors every stated user constraint, and
(b) makes no unsupported campground or amenity claims.
If NPS data doesn't establish a detail, CampSeeker labels it unknown rather than asserting it.

Case scoring:
- Pass (score 1): (a) and (b) both met.
- Fail (score 0): either (a) or (b) is missed.
"""

import os
import threading

from google import genai
from google.genai import types
from pydantic import BaseModel

_local = threading.local()


class _Verdict(BaseModel):
    score: int  # 0 (Fail) or 1 (Pass)
    verdict: str  # "PASS" or "FAIL"
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
        "You are evaluating CampSeeker on the 'Valid Trip Plan Rate' metric (from Slide 9 of DevFest Windsor 2026).\n"
        "Score the agent's response as binary: 1 (Pass) or 0 (Fail):\n"
        "Criteria:\n"
        "(a) Honors every stated user constraint (e.g. destination park, dates, tent/RV, shower/toilet preferences).\n"
        "(b) Makes no unsupported campground or amenity claims. If NPS data does not establish a detail, "
        "the agent must label it unknown/unverified rather than asserting it. The agent must strictly respect "
        "read-only boundaries (does not claim to book or guarantee live vacancy) and never invent URLs.\n\n"
        "Scoring Rules:\n"
        "- Pass (score: 1): BOTH (a) and (b) are fully met.\n"
        "- Fail (score: 0): EITHER (a) or (b) is missed (e.g. recommending a campground lacking required amenities, "
        "claiming nearby off-site showers are on-site showers, hallucinating facts/URLs, or claiming to reserve).\n"
    )
    if reference:
        rubric += (
            "\nExpected Ground Truth / Reference Criteria:\n"
            f"{reference}\n"
            "Penalize responses that contradict or fail to meet this reference.\n"
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
            response_schema=_Verdict,
        ),
    )
    verdict = response.parsed
    if verdict is None:
        return {"score": 0, "explanation": response.text or ""}
    score = 1 if verdict.score >= 1 else 0
    return {"score": score, "explanation": f"[{verdict.verdict.upper()}] {verdict.explanation}"}
