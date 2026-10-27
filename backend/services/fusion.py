"""Combine a base detector score (ML or rules) with the LLM+RAG assessment."""

from services.llm_detector import llm_scam_probability

MALICIOUS_THRESHOLD = 50
# Chosen from eval_llm.py: 0.5/0.5 had no false positives and the best F1 of
# the weightings tried, while 0.3/0.7 let a single LLM mistake flip results.
LLM_WEIGHT = 0.5
DISAGREEMENT_GAP = 30


def risk_level_for(score):
    return "High" if score >= 70 else "Medium" if score >= 40 else "Low"


def fuse_scores(base_score, assessment, weight=LLM_WEIGHT):
    """Return the final score, label and a breakdown the UI can display.

    `assessment` is None when the LLM is unavailable; the base score is then
    used unchanged, so detection never depends on Ollama being up.
    """
    base_score = float(base_score)
    if assessment is None:
        score, llm_probability = base_score, None
    else:
        llm_probability = llm_scam_probability(assessment)
        score = (1 - weight) * base_score + weight * llm_probability

    score = round(max(0.0, min(100.0, score)), 2)
    needs_review = (
        llm_probability is not None
        and assessment["verdict"] != "SUSPICIOUS"
        and (base_score >= MALICIOUS_THRESHOLD) != (llm_probability >= MALICIOUS_THRESHOLD)
        and abs(base_score - llm_probability) >= DISAGREEMENT_GAP
    )
    return {
        "score": score,
        "label": "MALICIOUS" if score >= MALICIOUS_THRESHOLD else "SAFE",
        "risk_level": risk_level_for(score),
        "needs_review": needs_review,
        "breakdown": {
            "base_score": round(base_score, 2),
            "llm_probability": None if llm_probability is None else round(llm_probability, 2),
            "llm_verdict": assessment["verdict"] if assessment else None,
            "llm_confidence": assessment["confidence"] if assessment else None,
            "llm_weight": weight if assessment else 0,
            "final_risk_score": score,
        },
    }
