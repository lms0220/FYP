from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()



class User(db.Model):

    __tablename__="users"


    user_id = db.Column(
        db.String(20),
        primary_key=True
    )


    username = db.Column(
        db.String(50),
        nullable=False
    )


    email = db.Column(
        db.String(100),
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    submissions = db.relationship(
        "Submission",
        backref="user"
    )






class Submission(db.Model):

    __tablename__="submissions"



    submission_id = db.Column(
        db.String(20),
        primary_key=True
    )


    user_id = db.Column(
        db.String(20),
        db.ForeignKey("users.user_id"),
        nullable=False
    )



    type = db.Column(
        db.String(10),
        nullable=False
    )



    content = db.Column(
        db.Text,
        nullable=False
    )



    status = db.Column(
        db.String(20),
        nullable=False
    )


    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )






class AnalysisResult(db.Model):

    __tablename__="analysis_results"



    result_id=db.Column(
        db.String(20),
        primary_key=True
    )



    submission_id=db.Column(
        db.String(20),
        db.ForeignKey(
            "submissions.submission_id"
        ),
        nullable=False
    )



    classification=db.Column(
        db.String(20),
        nullable=False
    )


    confidence_score=db.Column(
        db.Numeric(5,2),
        nullable=False
    )



    created_at=db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):

        return {

            "result_id": self.result_id,

            "submission_id": self.submission_id,

            "classification": self.classification,

            "confidence_score": float(
                self.confidence_score
            ),

            "created_at": self.created_at.isoformat()

        }