from flask import Flask, request, jsonify, session
from flask_cors import CORS
import pickle
import re
import os
from urllib.parse import urlparse
from db_models import db, User, AnalysisResult, Submission
from datetime import datetime
import uuid
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)

app.secret_key = "scamshield_secret_key_2026"
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
    "mysql+pymysql://root:0220@localhost/scam_detection"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
with app.app_context():
    db.create_all()


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

SUSPICIOUS_TLDS = {".xyz", ".top", ".click", ".tk", ".ml", ".ga", ".cf"}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co"}
KEYWORDS = ["login", "verify", "secure", "update", "account"]

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
    parsed = urlparse(url if url.startswith("http") else "http://" + url)
    return parsed.netloc.lower()

# =========================
# RULE ENGINE
# =========================
def rule_engine(url):

    score = 0
    flags = []


    url_lower = url.lower()

    parsed = urlparse(
        url if url.startswith("http")
        else "http://" + url
    )


    domain = parsed.netloc.lower()
    path = parsed.path.lower()



    # IP address URL
    if re.search(
        r"\d+\.\d+\.\d+\.\d+",
        url_lower
    ):

        score += 25
        flags.append("ip_url")



    # HTTP without HTTPS
    if url_lower.startswith("http://"):

        score += 8
        flags.append("no_https")



    # Suspicious domain extension
    if any(
        domain.endswith(tld)
        for tld in SUSPICIOUS_TLDS
    ):

        score += 20
        flags.append("suspicious_tld")



    # URL shortener
    if any(
        s in domain
        for s in SHORTENERS
    ):

        score += 15
        flags.append("url_shortener")



    # Suspicious keywords
    if any(
        k in path
        for k in KEYWORDS
    ):

        score += 15
        flags.append("suspicious_keywords")



    return min(score,100), flags

# =========================
# TRUST ENGINE
# =========================
def trust_engine(url):
    domain = extract_domain(url)
    return 30 if domain in TRUSTED_DOMAINS else 0

# =========================
# ML ENGINE
# =========================
def ml_engine(url):
    vec = url_vectorizer.transform([url])
    prob = url_model.predict_proba(vec)[0]
    idx = list(url_model.classes_).index("phishing")
    return prob[idx] * 100

# =========================
# FUSION ENGINE
# =========================
def fusion_engine(url):
    rule_score, flags = rule_engine(url)
    trust_score = trust_engine(url)
    ml_score = ml_engine(url)

    final_score = (
        rule_score * 0.6 +
        ml_score * 0.4 -
        trust_score
    )

    final_score = max(0, min(100, final_score))

    if final_score >= 70:
        label = "HIGH_RISK"
    elif final_score >= 40:
        label = "SUSPICIOUS"
    else:
        label = "SAFE"

    return {
        "url": url,
        "final_score": round(final_score, 2),
        "label": label,
        "rule_score": rule_score,
        "ml_score": round(ml_score, 2),
        "trust_score": trust_score,
        "flags": flags
    }

# =========================
# API ROUTE
# =========================
@app.route("/predict", methods=["POST"])
def predict():

    data = request.get_json() or {}

    text = data.get("text", "").strip()


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



        if prediction_value == 1:

            prediction = "SCAM"

        else:

            prediction = "SAFE"



        flags = []


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


    submission = Submission(

        submission_id="S" + str(uuid.uuid4())[:8],

        user_id=user_id,

        type=input_type,

        content=text,

        status="COMPLETED"

    )


    db.session.add(submission)

    db.session.commit()



    # Create analysis result

    db_result = AnalysisResult(

        result_id="R" + str(uuid.uuid4())[:8],

        submission_id=submission.submission_id,

        classification=prediction,

        confidence_score=float(score),

        created_at=datetime.now()

    )


    db.session.add(db_result)

    db.session.commit()


    return jsonify({

    "type": response_type,

    "prediction": prediction,

    "score": float(score),

    "flags": flags,

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
    print("LOGIN SESSION:", session)

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
        host="localhost",
        port=5000,
        debug=True
    )
