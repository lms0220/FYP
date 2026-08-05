import requests
import json
import os


# Ollama runs on the Windows host, never as a Docker service. Docker Desktop
# resolves host.docker.internal to the Windows host gateway.
OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434/api/generate",
)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "true").lower() == "true"
OLLAMA_CONNECT_TIMEOUT = float(os.getenv("OLLAMA_CONNECT_TIMEOUT", "3"))
OLLAMA_READ_TIMEOUT = float(os.getenv("OLLAMA_READ_TIMEOUT", "120"))


def generate_explanation(prompt):
    """Call host Ollama with a short timeout; callers provide a safe fallback."""
    if not OLLAMA_ENABLED:
        return {"error": "LLM disabled"}

    result = ""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "10m",
                "options": {"temperature": 0},
            },
            timeout=(OLLAMA_CONNECT_TIMEOUT, OLLAMA_READ_TIMEOUT),
        )
        response.raise_for_status()
        result = response.json().get("response", "")
        return json.loads(result)
    except requests.RequestException as error:
        return {"error": "LLM connection failed", "details": str(error)}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON returned by LLM", "raw_response": result}


def generate_scam_explanation(user_input, retrieved_context):
    """Generate a grounded JSON explanation using retrieved Markdown chunks."""
    references = sorted({item["source"] for item in retrieved_context})
    knowledge = "\n\n".join(
        f"Source: {item['source']}\nContent: {item['content']}"
        for item in retrieved_context
    ) or "No matching knowledge-base content was retrieved."

    prompt = f"""
You are a cybersecurity scam detection assistant. Explain the user's message
using only the relevant scam knowledge provided below. Do not claim certainty
or invent sources. Return ONLY a valid JSON object, with no Markdown.

Use exactly this schema:
{{
  "explanation": "",
  "scam_type": "",
  "risk_level": "Low|Medium|High",
  "recommendation": [""],
  "references": [""]
}}

User message:
{user_input}

Relevant scam knowledge:
{knowledge}

Allowed references:
{json.dumps(references)}
"""
    response = generate_explanation(prompt)
    if isinstance(response, dict) and not response.get("error"):
        response["references"] = [
            reference for reference in response.get("references", [])
            if reference in references
        ] or references
    return response


def analyze_sms(message):

    prompt = f"""
You are a cybersecurity scam detection assistant.

Analyze the SMS below.

Your response MUST be a valid JSON object.

Rules:
- Return ONLY JSON.
- Do not include markdown.
- Do not include explanations outside JSON.
- Do not wrap the JSON in code fences.

Use this exact JSON format:

{{
  "threat_type": "",
  "target_organization": "",
  "risk_level": "",
  "explanation": "",
  "recommendation": ""
}}

Requirements:
- threat_type must be one of:
  Bank Phishing,
  Investment Scam,
  Job Scam,
  Parcel Scam,
  Romance Scam,
  Prize Scam,
  Account Takeover,
  Other.

- risk_level must be one of:
  Low,
  Medium,
  High.

If the SMS is not a scam:
- threat_type = "None"
- target_organization = "Unknown"
- risk_level = "Low"
- explanation = "No phishing or scam indicators were identified."
- recommendation = "No action required."


SMS:

{message}

"""


    return generate_explanation(prompt)


def analyze_url(url, risk_factors):
    """Return a concise, structured phishing explanation for a URL."""
    prompt = f"""
You are a cybersecurity URL-phishing analyst. Analyze the URL and the
deterministic risk factors below. Return ONLY valid JSON, with no markdown.

Use exactly this format:
{{
  "threat_type": "",
  "target_organization": "",
  "risk_level": "Low|Medium|High",
  "explanation": "",
  "recommendation": ""
}}

Do not claim that a site is confirmed malicious. Explain the observed signs
and use cautious language such as "appears to" when appropriate.

URL or message containing URL:
{url}

Detected risk factors:
{json.dumps(risk_factors)}
"""

    return generate_explanation(prompt)
