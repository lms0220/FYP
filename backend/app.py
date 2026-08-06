from flask import Flask, json, request, jsonify, session
from flask_cors import CORS
import pickle
import re
import os
from urllib.parse import urlparse
from difflib import SequenceMatcher

from db_models import db, User, AnalysisResult, Submission
from datetime import datetime
import uuid
from werkzeug.security import check_password_hash, generate_password_hash
from services.llm_service import analyze_url, generate_scam_explanation
from services.rag_service import retrieve_context
import time
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import inspect, text as sql_text

app = Flask(__name__)

app.secret_key = "scamshield_secret_key_2026"
# Do not reuse Flask's default "session" cookie.  Older local deployments
# can leave a cookie with that name under a different domain/path, causing the
# browser to keep sending its stale user ID even after a successful login.
app.config["SESSION_COOKIE_NAME"] = "scamshield_session"
# The frontend and backend use localhost on different ports, which is still
# same-site.  "None" requires the Secure flag in modern browsers; using it
# with local HTTP makes browsers reject the login Set-Cookie header and retain
# a stale session.  Use Lax locally; set None + Secure only behind HTTPS.
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]
)


app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://root:@localhost:3306/scam_detection"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def wait_for_database():

    attempts = 10

    while attempts > 0:

        try:
            with app.app_context():
                db.create_all()
                migrate_analysis_result_schema()

            print("Database connected successfully")
            return

        except OperationalError as e:

            print("Database not ready, waiting...")
            print(e)

            attempts -= 1
            time.sleep(5)


    raise Exception("Database connection failed")


def migrate_analysis_result_schema():
    """Add additive columns for existing Docker/MySQL volumes.

    create_all() creates missing tables but intentionally does not modify a
    table that already exists, so this keeps local development data usable.
    """
    existing_columns = {
        column["name"] for column in inspect(db.engine).get_columns("analysis_results")
    }
    additions = {
        "detected_threats": "TEXT NULL",
        "risk_level": "VARCHAR(20) NULL",
    }
    for name, definition in additions.items():
        if name not in existing_columns:
            db.session.execute(sql_text(
                f"ALTER TABLE analysis_results ADD COLUMN {name} {definition}"
            ))
    db.session.commit()


wait_for_database()


@app.route("/api/dashboard")
def dashboard():
    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "message": "Please login first"
        }), 401

    results = AnalysisResult.query.join(Submission).filter(
        Submission.user_id == user_id
    ).order_by(
        AnalysisResult.created_at.desc()
    ).all()

    return jsonify([
        r.to_dict()
        for r in results
    ])

@app.route("/api/history")
def history():
    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "message": "Please login first"
        }), 401

    rows = db.session.query(AnalysisResult, Submission).join(
        Submission,
        AnalysisResult.submission_id == Submission.submission_id
    ).filter(
        Submission.user_id == user_id
    ).order_by(
        AnalysisResult.created_at.desc()
    ).all()

    return jsonify([
        {
            "result_id": result.result_id,
            "submission_id": submission.submission_id,
            "type": submission.type,
            "content": submission.content,
            "status": submission.status,
            "classification": result.classification,
            "confidence_score": float(result.confidence_score),
            "created_at": result.created_at.isoformat()
        }
        for result, submission in rows
    ])

@app.route("/history/delete", methods=["POST"])
def delete_history():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first"
        }), 401


    data = request.get_json()

    result_ids = data.get("result_ids", [])


    if not result_ids:
        return jsonify({
            "message": "No records selected"
        }), 400


    for result_id in result_ids:

        result = AnalysisResult.query.filter_by(
            result_id=result_id
        ).first()


        if result:

            submission = Submission.query.filter_by(
                submission_id=result.submission_id,
                user_id=user_id
            ).first()


            if submission:

                db.session.delete(result)
                db.session.delete(submission)


    db.session.commit()


    return jsonify({
        "message": "Deleted successfully"
    })

@app.route("/")
def home():

    return "Backend Connected"




# =========================
# LOAD MODELS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
        if domain in TRUSTED_DOMAINS:
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
def trust_engine(url):
    domain = extract_domain(url)
    return 25 if domain in TRUSTED_DOMAINS or any(domain.endswith("." + trusted) for trusted in TRUSTED_DOMAINS) else 0

# =========================
# ML ENGINE
# =========================
def ml_engine(url):
    vec = url_vectorizer.transform([url])
    prob = url_model.predict_proba(vec)[0]

    classes = list(url_model.classes_)

    if "phishing" in classes:
        idx = classes.index("phishing")

    elif "malicious" in classes:
        idx = classes.index("malicious")

    else:
        idx = 1

    return prob[idx] * 100

# =========================
# FUSION ENGINE
# =========================
def fusion_engine(url):
    rule_score, factors = rule_engine(url)
    trust_score = trust_engine(url)
    ml_score = ml_engine(url)

    # The ML probability is converted to a capped, visible contribution. This
    # makes the final risk score exactly equal to the displayed factor total.
    ml_points = min(10, max(0, round(ml_score / 10)))
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

# =========================
# API ROUTE
# =========================
@app.route("/predict", methods=["POST"])
def predict():

    data = request.get_json() or {}

    text = (
        data.get("text")
        or data.get("content")
        or ""
    ).strip()

    llm_analysis = None
    rag_analysis = None


    if not text:

        return jsonify({
            "error": "Input empty"
        }),400



    input_type = detect_input_type(text)



    # ======================
    # URL ANALYSIS
    # ======================

    if input_type == "url":


        result = fusion_engine(text)


        prediction = result["label"]

        score = result["final_score"]

        flags = result["flags"]

        risk_factors = result["risk_factors"]
        risk_level = result["risk_level"]
        score_breakdown = result["score_breakdown"]

        if prediction == "MALICIOUS":
            llm_analysis = analyze_url(text, risk_factors)
            if not isinstance(llm_analysis, dict) or llm_analysis.get("error"):
                llm_analysis = fallback_url_analysis(result)



        response_type = "url"



    # ======================
    # SMS ANALYSIS
    # ======================

    else:


        vector = sms_vectorizer.transform([text])


        prediction_value = sms_model.predict(vector)[0]


        probability = sms_model.predict_proba(vector)[0]


        score = round(
            max(probability) * 100,
            2
        )



        prediction = "MALICIOUS" if prediction_value == 1 else "SAFE"

        try:
            retrieved_context = retrieve_context(text, k=3)
            rag_analysis = generate_scam_explanation(text, retrieved_context)
            if rag_analysis.get("error"):
                raise RuntimeError(rag_analysis["error"])

            # Preserve the existing UI contract while the API exposes the
            # richer RAG payload separately.
            llm_analysis = {
                "threat_type": rag_analysis.get("scam_type", "Other"),
                "risk_level": rag_analysis.get(
                    "risk_level", "High" if prediction == "MALICIOUS" else "Low"
                ),
                "explanation": rag_analysis.get("explanation", ""),
                "recommendation": " ".join(rag_analysis.get("recommendation", [])),
            }
        except Exception as error:
            app.logger.warning("RAG explanation unavailable: %s", error)
            rag_analysis = {
                "scam_type": "Other" if prediction == "MALICIOUS" else "None",
                "risk_level": "High" if prediction == "MALICIOUS" else "Low",
                "explanation": "Knowledge-base explanation is unavailable. Run python create_vector_db.py to build the local index.",
                "recommendation": ["Do not share personal information or OTPs."],
                "references": [],
            }



        flags = []
        risk_factors = []
        risk_level = "High" if prediction == "MALICIOUS" and score >= 70 else "Medium" if prediction == "MALICIOUS" else "Low"
        score_breakdown = {
            "ml_probability": float(score),
            "rule_score": 0,
            "trusted_domain_adjustment": 0,
        }


        response_type = "sms"





    # ======================
    # SAVE DATABASE
    # ======================


    # Create submission first
    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "message": "Please login first"
        }), 401

    # Flask stores the user ID in the signed client session cookie.  The
    # corresponding row can disappear when the database is reset/restored, so
    # do not trust the cookie alone before inserting a foreign-key child row.
    user = db.session.get(User, user_id)
    if user is None:
        session.clear()
        return jsonify({
            "message": "Your session is no longer valid. Please login again."
        }), 401


    submission = Submission(

        submission_id="S" + str(uuid.uuid4())[:8],

        user_id=user_id,

        type=input_type,

        content=text,

        status="COMPLETED"

    )


    # Create the result in the same transaction as its submission so a
    # partially saved prediction is never left behind if either insert fails.

    db_result = AnalysisResult(

        result_id="R" + str(uuid.uuid4())[:8],

        submission_id=submission.submission_id,

        classification=prediction,

        confidence_score=float(score),

        llm_analysis=json.dumps(llm_analysis),

        detected_threats=json.dumps(risk_factors),

        risk_level=risk_level,

        created_at=datetime.now()

    )


    try:
        # AnalysisResult has a database foreign key to Submission, but there
        # is no ORM relationship between these models for SQLAlchemy to infer
        # insert order from.  Flush the parent first without committing, then
        # insert its child in the same transaction.
        db.session.add(submission)
        db.session.flush()
        db.session.add(db_result)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        app.logger.exception("Database integrity error while saving prediction")

        # Covers the unlikely case where the account is deleted after the
        # existence check but before MySQL receives the insert.  Other
        # constraints are a server error, not an authentication failure.
        if db.session.get(User, user_id) is None:
            session.clear()
            return jsonify({
                "message": "Your session is no longer valid. Please login again."
            }), 401

        return jsonify({
            "message": "Unable to save the prediction. Please try again."
        }), 500

    print("LLM RESULT:", llm_analysis)

    return jsonify({

    "type": response_type,

    "prediction": prediction,

    "score": float(score),

    "flags": flags,

    "risk_factors": risk_factors,

    "risk_level": risk_level,

    "score_breakdown": score_breakdown,

    "llm_analysis": llm_analysis,

    "rag_analysis": rag_analysis,

    "message":"Analysis completed"

})

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json() or {}

    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password:

        return jsonify({
            "message":"Username, email, and password are required"
        }),400


    # check existing email
    existing = User.query.filter_by(email=email).first()


    if existing:

        return jsonify({
            "message":"Email already exists"
        }),400



    user = User(
        user_id="U" + str(uuid.uuid4())[:8],
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )


    db.session.add(user)

    db.session.commit()


    return jsonify({

        "message":"Register success",

        "user_id":user.user_id

    })

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()

    if not user:

        return jsonify({
            "message": "User not found"
        }), 404

    password_matches = (
        check_password_hash(user.password_hash, password)
        if user.password_hash.startswith("scrypt:")
        or user.password_hash.startswith("pbkdf2:")
        else user.password_hash == password
    )

    if not password_matches:

        return jsonify({
            "message": "Invalid password"
        }), 401

    session["user_id"] = user.user_id

    return jsonify({

        "message": "Login Success",

        "user_id": user.user_id,

        "username": user.username

    })

@app.route("/logout")
def logout():

    session.clear()

    return jsonify({
        "message": "Logout Success"
    })

@app.route("/me")
def me():

    user_id = session.get("user_id")

    if not user_id:

        return jsonify({
            "message": "Not logged in"
        }), 401

    # A session cookie alone is not authentication if its account was removed
    # or the database volume was replaced.
    if db.session.get(User, user_id) is None:
        session.clear()
        return jsonify({
            "message": "Your session is no longer valid. Please login again."
        }), 401

    return jsonify({
        "user_id": user_id
    })


# =========================
# RUN
# =========================
@app.route("/test")
def test():

    return jsonify({
        "message": "Backend OK"
    })

if __name__ == "__main__":
    print(app.url_map)
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
