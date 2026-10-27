import os
import secrets
from flask import Flask, json, request, jsonify, session
from flask_cors import CORS

from db_models import db, User, AnalysisResult, Submission
from datetime import datetime
import uuid
from werkzeug.security import check_password_hash, generate_password_hash

from services.rag_service import retrieve_context
from services.fusion import fuse_scores, MALICIOUS_THRESHOLD
from services.llm_detector import llm_assess, llm_scam_probability
from services.zh_detection import analyze_chinese_sms, extract_link, is_chinese
import time
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import inspect, text as sql_text

app = Flask(__name__)

# Never ship a known signing key: anyone who knows it can forge login sessions.
# Without SECRET_KEY a random one is generated, so sessions reset on restart.
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
if not os.getenv("SECRET_KEY"):
    print("WARNING: SECRET_KEY is not set; using a random key (sessions reset on restart).")
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


app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "mysql+pymysql://root:@localhost:3306/scam_detection"
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




from services.detection import (
    extract_url,
    sms_model,
    sms_vectorizer,
    detect_input_type,
    fusion_engine,
    fallback_url_analysis,
)

# =========================
# API ROUTE
# =========================
def llm_second_opinion(text, kind, signals):
    """RAG retrieval + LLM verdict. Returns (assessment or None, context)."""
    try:
        context = retrieve_context(text, k=3)
    except Exception as error:
        app.logger.warning("RAG retrieval unavailable: %s", error)
        context = []
    return llm_assess(text, kind=kind, context=context, signals=signals), context


def assessment_to_analysis(assessment, fallback_level):
    """Shape an LLM assessment for the existing llm_analysis UI contract."""
    return {
        "threat_type": assessment["scam_type"],
        "risk_level": fallback_level,
        "explanation": assessment["explanation"],
        "recommendation": " ".join(assessment["recommendation"]),
        "evidence": assessment["evidence"],
    }


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
    detection = {"llm_used": False, "needs_review": False}


    if not text:

        return jsonify({
            "error": "Input empty"
        }),400



    # Chinese text goes through the Chinese rule-based analyser; the English
    # SMS model and knowledge base cannot read it.
    chinese = is_chinese(text)
    input_type = "sms" if chinese else detect_input_type(text)



    # ======================
    # URL ANALYSIS
    # ======================

    # A message that merely contains a link (e.g. "Win a free iPhone at http://...")
    # is an SMS with a link, not a bare URL; judging only the link would ignore
    # what the message asks the reader to do.
    link_in_text = extract_url(text) if input_type == "url" else None
    if link_in_text and len(text.replace(link_in_text, "").split()) >= 4:
        input_type = "sms"

    if input_type == "url":


        result = fusion_engine(text)


        prediction = result["label"]

        score = result["final_score"]

        flags = result["flags"]

        risk_factors = result["risk_factors"]
        risk_level = result["risk_level"]
        score_breakdown = result["score_breakdown"]

        # The URL verdict stays with the rule/ML engine, which is validated on
        # data. The LLM cannot check domain reputation, so it only explains the
        # result and flags disagreement for review.
        if prediction == "MALICIOUS" or score >= 30:
            assessment, context = llm_second_opinion(
                text, "URL",
                {"risk_factors": [factor["title"] for factor in risk_factors if factor["points"] > 0]},
            )
            if assessment:
                llm_analysis = assessment_to_analysis(assessment, risk_level)
                llm_probability = llm_scam_probability(assessment)
                detection = {
                    "llm_used": True,
                    "needs_review": (prediction == "MALICIOUS") != (llm_probability >= MALICIOUS_THRESHOLD)
                    and abs(score - llm_probability) >= 30,
                }
                score_breakdown = {**score_breakdown, "llm_verdict": assessment["verdict"], "llm_confidence": assessment["confidence"]}
                rag_analysis = {"references": assessment["references"]}
            elif prediction == "MALICIOUS":
                llm_analysis = fallback_url_analysis(result)



        response_type = "url"



    # ======================
    # SMS ANALYSIS
    # ======================

    elif chinese:

        link = extract_link(text)
        zh = analyze_chinese_sms(text, fusion_engine(link) if link else None)

        assessment, context = llm_second_opinion(text, "SMS message (Chinese)", {"rule_score": zh["score"], "rule_flags": zh["flags"]})
        fused = fuse_scores(zh["score"], assessment)

        prediction = fused["label"]
        score = fused["score"]
        risk_level = fused["risk_level"]
        flags = zh["flags"]
        risk_factors = zh["risk_factors"]
        score_breakdown = fused["breakdown"]
        detection = {"llm_used": assessment is not None, "needs_review": fused["needs_review"]}

        if assessment:
            llm_analysis = assessment_to_analysis(assessment, risk_level)
            rag_analysis = {
                "scam_type": assessment["scam_type"], "risk_level": risk_level,
                "explanation": assessment["explanation"], "recommendation": assessment["recommendation"],
                "references": assessment["references"],
            }
        else:
            llm_analysis = {**zh["llm_analysis"], "risk_level": risk_level}
            rag_analysis = None

        response_type = "sms"

    else:


        vector = sms_vectorizer.transform([text])

        # Probability of the scam class (the old code reported the winning
        # class's confidence, so a confident SAFE showed a score of ~98).
        spam_index = list(sms_model.classes_).index(1)
        ml_probability = float(sms_model.predict_proba(vector)[0][spam_index]) * 100

        # Take the worse of the text model and the embedded link's risk score.
        link = extract_link(text)
        if link:
            link_result = fusion_engine(link)
            ml_probability = max(ml_probability, float(link_result["final_score"]))

        assessment, context = llm_second_opinion(text, "SMS message", {"ml_scam_probability": round(ml_probability)})
        fused = fuse_scores(ml_probability, assessment)

        prediction = fused["label"]
        score = fused["score"]
        risk_level = fused["risk_level"]
        score_breakdown = {**fused["breakdown"], "ml_probability": round(ml_probability, 2)}
        detection = {"llm_used": assessment is not None, "needs_review": fused["needs_review"]}

        if assessment:
            llm_analysis = assessment_to_analysis(assessment, risk_level)
            rag_analysis = {
                "scam_type": assessment["scam_type"], "risk_level": risk_level,
                "explanation": assessment["explanation"], "recommendation": assessment["recommendation"],
                "references": assessment["references"],
            }
        else:
            app.logger.warning("LLM assessment unavailable; using the ML model alone")
            rag_analysis = {
                "scam_type": "Other" if prediction == "MALICIOUS" else "None",
                "risk_level": risk_level,
                "explanation": "AI explanation is unavailable (is Ollama running?). The verdict comes from the ML model alone.",
                "recommendation": ["Do not share personal information or OTPs."],
                "references": [],
            }
            llm_analysis = {
                "threat_type": rag_analysis["scam_type"], "risk_level": risk_level,
                "explanation": rag_analysis["explanation"], "recommendation": " ".join(rag_analysis["recommendation"]),
            }

        flags = []
        risk_factors = []

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

    "language": "zh" if chinese else "en",

    "detection": detection,

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
@app.route("/api/check-url", methods=["POST"])
def check_url():
    """Login-free URL check for the browser extension.

    Rules and ML only: it neither calls the LLM nor stores the URL.
    """
    url = ((request.get_json(silent=True) or {}).get("url") or "").strip()

    if not url or len(url) > 2048:
        return jsonify({"message": "A URL of at most 2048 characters is required"}), 400

    result = fusion_engine(url)

    return jsonify({
        "prediction": result["label"],
        "score": float(result["final_score"]),
        "risk_level": result["risk_level"],
        "flags": result["flags"],
        "risk_factors": result["risk_factors"],
    })


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
        # The Werkzeug debugger allows remote code execution; opt in locally only.
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )
