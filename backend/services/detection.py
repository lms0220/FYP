"""URL/SMS detection engines: model loading, rule engine, trust and fusion scoring."""

import os
import pickle
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse


# =========================
# LOAD MODELS
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

sms_model = pickle.load(open(os.path.join(MODEL_DIR, "sms_model.pkl"), "rb"))
sms_vectorizer = pickle.load(open(os.path.join(MODEL_DIR, "sms_vectorizer.pkl"), "rb"))

url_model = pickle.load(open(os.path.join(MODEL_DIR, "url_ml_model.pkl"), "rb"))
url_vectorizer = pickle.load(open(os.path.join(MODEL_DIR, "url_tfidf.pkl"), "rb"))
# =========================
# CONFIG
# =========================
TRUSTED_DOMAINS = {
    "google.com", "facebook.com", "amazon.com",
    "microsoft.com", "apple.com", "paypal.com"
}

SUSPICIOUS_TLDS = {".xyz", ".top", ".click", ".tk", ".ml", ".ga", ".cf", ".ru", ".gq", ".work", ".zip", ".country"}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co"}
SUSPICIOUS_KEYWORDS = {"login", "verify", "secure", "update", "account", "password", "signin", "wallet", "confirm"}
URGENCY_KEYWORDS = {"urgent", "suspended", "immediately", "alert", "limited", "expire", "locked", "action required"}
# The URL model reaches ~0.9 F1 on its own, so it must be able to move the score;
# well-known sites are protected by the top-domain allowlist below instead.
ML_MAX_POINTS = 50
ML_POINTS_PER_PERCENT = 0.5
TOP_DOMAIN_TRUST = 50
BARE_HOST_ML_MAX_POINTS = 10


def _load_top_domains():
    path = os.path.join(BASE_DIR, "data", "top_domains.txt")
    try:
        with open(path, encoding="utf-8") as handle:
            return {line.strip() for line in handle if line.strip()}
    except OSError:
        return set()


# Tranco top ~10k registrable domains (shorteners and shared hosts removed).
# Matched exactly (optionally with www.) because subdomains of big sites can
# host user content, e.g. sites.google.com.
TOP_DOMAINS = _load_top_domains()

BRANDS = {"amazon", "apple", "microsoft", "google", "paypal", "facebook", "netflix", "bank"}

# ===================================
# INPUT TYPE DETECTION
# ===================================

def detect_input_type(text):

    text = text.strip().lower()

    url_pattern = (
        r"https?://|"
        r"www\.|"
        r"\.com|"
        r"\.net|"
        r"\.org|"
        r"\.xyz|"
        r"\.top|"
        r"\.click|"
        r"\.io|"
        r"\.co"
    )

    if re.search(url_pattern, text):
        return "url"

    return "sms"

# =========================
# HELPERS
# =========================
def extract_domain(url):
    candidate = extract_url(url)
    parsed = urlparse(candidate if candidate.startswith("http") else "http://" + candidate)
    return parsed.netloc.lower().split(":")[0]


def extract_url(text):
    match = re.search(r"https?://[^\s]+|www\.[^\s]+", text, re.IGNORECASE)
    return match.group(0).rstrip(".,!?)]") if match else text.strip()


def add_factor(factors, code, title, detail, points):
    factors.append({"code": code, "title": title, "detail": detail, "points": points})

# =========================
# RULE ENGINE
# =========================
def rule_engine(url):
    text_lower = url.lower()
    candidate = extract_url(url)
    parsed = urlparse(candidate if candidate.startswith("http") else "http://" + candidate)
    domain = parsed.netloc.lower().split(":")[0]
    path = parsed.path.lower()
    factors = []

    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", domain):
        add_factor(factors, "ip_url", "IP-address URL", "Uses an IP address instead of a registered domain.", 20)
    if candidate.lower().startswith("http://"):
        add_factor(factors, "no_https", "Unsecured HTTP connection", "The link uses HTTP rather than encrypted HTTPS.", 10)
    if domain in SHORTENERS or any(domain.endswith("." + shortener) for shortener in SHORTENERS):
        add_factor(factors, "url_shortener", "Shortened URL", "A URL shortener hides the final destination.", 12)

    normalized_domain = domain.replace("0", "o").replace("1", "l").replace("3", "e").replace("@", "a")
    for brand in BRANDS:
        if domain in TRUSTED_DOMAINS or is_top_domain(domain):
            continue
        similarity = SequenceMatcher(None, normalized_domain.split(".")[0], brand).ratio()
        if brand in normalized_domain or similarity >= 0.78:
            add_factor(factors, "brand_impersonation", "Brand impersonation detected", f'The domain "{domain}" uses a lookalike spelling to imitate {brand.title()}, not its official domain.', 30)
            break

    keyword_hits = sorted({keyword for keyword in SUSPICIOUS_KEYWORDS if keyword in f"{domain} {path}"})
    if keyword_hits:
        add_factor(factors, "credential_request", "Credential-harvesting pattern", f"Login or verification terms detected: {', '.join(keyword_hits)}.", 20)
    urgency_hits = sorted({keyword for keyword in URGENCY_KEYWORDS if keyword in text_lower})
    if urgency_hits:
        add_factor(factors, "social_engineering", "Social engineering", f"Urgency language attempts to pressure the user: {', '.join(urgency_hits)}.", 20)
    if any(domain.endswith(tld) for tld in SUSPICIOUS_TLDS):
        tld = next(tld for tld in SUSPICIOUS_TLDS if domain.endswith(tld))
        phishing_context = any(factor["code"] in {"brand_impersonation", "credential_request"} for factor in factors)
        detail = (
            f"The foreign TLD ({tld}) is combined with brand impersonation or login behaviour, increasing phishing risk."
            if phishing_context
            else f"The {tld} TLD should be verified together with other URL signals; it is not malicious by itself."
        )
        add_factor(factors, "contextual_tld", "Contextual domain risk", detail, 5)
    if len(candidate) > 90 or candidate.count(".") >= 4 or candidate.count("-") >= 3:
        add_factor(factors, "suspicious_structure", "Suspicious URL structure", "The URL has an unusually complex structure.", 8)

    return min(sum(factor["points"] for factor in factors), 100), factors

# =========================
# TRUST ENGINE
# =========================
def is_top_domain(domain):
    return (domain[4:] if domain.startswith("www.") else domain) in TOP_DOMAINS


def trust_engine(url):
    domain = extract_domain(url)
    if is_top_domain(domain):
        return TOP_DOMAIN_TRUST
    return 25 if domain in TRUSTED_DOMAINS or any(domain.endswith("." + trusted) for trusted in TRUSTED_DOMAINS) else 0

# =========================
# ML ENGINE
# =========================
def normalize_url_for_model(url):
    """Strip scheme and leading www. before vectorising.

    The training CSV rarely has a scheme on benign URLs, so the model learned
    "https://" as a malicious signal and flagged nearly every real-world URL.
    """
    url = re.sub(r"^[a-z][a-z0-9+.-]*://", "", url.strip().lower())
    return re.sub(r"^www\d*\.", "", url).rstrip("/")


def ml_engine(url):
    vec = url_vectorizer.transform([normalize_url_for_model(url)])
    prob = url_model.predict_proba(vec)[0]

    classes = list(url_model.classes_)

    # Anything that is not "benign" (phishing, malware, defacement) is malicious.
    if "benign" in classes:
        return (1 - prob[classes.index("benign")]) * 100

    for name in ("phishing", "malicious"):
        if name in classes:
            return prob[classes.index(name)] * 100

    return prob[1] * 100

# =========================
# FUSION ENGINE
# =========================
def fusion_engine(url):
    rule_score, factors = rule_engine(url)
    trust_score = trust_engine(url)
    ml_score = ml_engine(url)

    # The ML probability is converted to a capped, visible contribution. This
    # makes the final risk score exactly equal to the displayed factor total.
    # Bare hostnames carry too little text for the char n-gram model: it scores
    # almost every unseen domain as malicious. Only trust it fully when the URL
    # has a path or query to inspect; otherwise keep it a minor signal.
    has_path = "/" in extract_url(url).split("://", 1)[-1].rstrip("/") or "?" in url
    ml_cap = ML_MAX_POINTS if has_path else BARE_HOST_ML_MAX_POINTS
    ml_points = min(ml_cap, max(0, round(ml_score * ML_POINTS_PER_PERCENT)))
    if ml_points:
        add_factor(
            factors,
            "ml_phishing_signal",
            "ML phishing signal",
            f"The URL model found phishing-like text and domain patterns ({ml_score:.1f}% raw model probability).",
            ml_points,
        )
    if trust_score:
        add_factor(
            factors,
            "trusted_domain_adjustment",
            "Known-domain adjustment",
            "The hostname matches a trusted-domain allowlist, reducing risk.",
            -trust_score,
        )

    final_score = max(0, min(100, sum(factor["points"] for factor in factors)))

    if final_score >= 50:
        label = "MALICIOUS"
    else:
        label = "SAFE"

    return {
        "url": url,
        "final_score": round(final_score, 2),
        "label": label,
        "rule_score": rule_score,
        "ml_score": round(ml_score, 2),
        "trust_score": trust_score,
        "risk_level": "High" if final_score >= 70 else "Medium" if final_score >= 40 else "Low",
        "flags": [factor["code"] for factor in factors if factor["points"] > 0],
        "risk_factors": factors,
        "score_breakdown": {
            "ml_probability": round(ml_score, 2),
            "ml_contribution": ml_points,
            "rule_score": rule_score,
            "trusted_domain_adjustment": -trust_score,
            "final_risk_score": round(final_score, 2),
        },
    }


def fallback_url_analysis(result):
    """Keep URL explanations useful when the optional local LLM is offline."""
    factors = result["risk_factors"]
    details = " ".join(factor["detail"] for factor in factors)
    brand_factor = next(
        (factor for factor in factors if factor["code"] == "brand_impersonation"),
        None,
    )
    return {
        "explanation": details or "The URL was assessed using its domain, structure, and phishing indicators.",
        "threat_type": "Brand impersonation phishing" if brand_factor else "Potential phishing URL",
        "target_organization": "Amazon" if brand_factor and "Amazon" in brand_factor["detail"] else "Unknown",
        "risk_level": result["risk_level"],
        "recommendation": "Do not open the URL or enter credentials. Access the organization through its official website and report the phishing page.",
    }
