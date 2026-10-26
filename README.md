# AI-Driven Scam and Phishing Detection System

An AI-powered cybersecurity system designed to detect suspicious SMS messages and phishing URLs using Machine Learning, Rule-Based Analysis, Large Language Models (LLM), and Retrieval-Augmented Generation (RAG).

The system analyzes potential scam content, identifies malicious patterns, provides explainable security insights, and recommends preventive actions to help users avoid online scams.

---

# Features

## 1. SMS Scam Detection

* Classifies SMS messages into:

  * Safe
  * Malicious

* Uses Natural Language Processing (NLP) techniques:

  * Text preprocessing
  * TF-IDF feature extraction
  * Machine Learning classification

* Detects common scam patterns:

  * Fake bank messages
  * OTP scams
  * Delivery scams
  * Urgent action scams

---

## 2. Phishing URL Detection

The system analyzes suspicious URLs using multiple detection layers:

* Machine Learning URL classification
* Domain pattern analysis
* Rule-based phishing indicators
* Risk scoring mechanism

Detection factors include:

* Suspicious domain names
* Brand impersonation
* Credential harvesting keywords
* Suspicious URL structures
* Social engineering indicators

---

## 3. Explainable AI Security Analysis

Instead of only returning a prediction, the system generates human-readable explanations.

Example:

Prediction:

```
MALICIOUS
Confidence: 88%
```

AI explanation:

```
The URL mimics a legitimate banking website through domain impersonation
and contains credential harvesting patterns.
```

The system provides:

* Threat category
* Risk level
* Explanation
* Recommended actions

---

# 4. Retrieval-Augmented Generation (RAG)

The system integrates RAG to improve LLM reliability by grounding AI explanations with a local cybersecurity knowledge base.

## RAG Pipeline

```
User Input
    |
    ↓
Scam Detection Model
    |
    ↓
Knowledge Retrieval
    |
    ↓
Relevant Security Documents
    |
    ↓
LLM Generation
    |
    ↓
Explainable Scam Analysis
```

The knowledge base contains cybersecurity information including:

* Scam types
* Phishing techniques
* SMS scam patterns
* URL security indicators
* Prevention guidelines
* Official security sources

Vector similarity search is implemented using:

* Sentence Transformers
* FAISS Vector Database

---

# System Architecture

```
Frontend (React)
        |
        |
        ↓
Flask REST API Backend
        |
        |
        ├── SMS Detection Model
        |
        ├── URL Detection Model
        |
        ├── Rule Engine
        |
        ├── Fusion Risk Engine
        |
        ├── RAG Retrieval Service
        |
        ├── LLM Explanation Service
        |
        ↓
MySQL Database
```

---

# Technology Stack

## Frontend

* React.js
* Tailwind CSS

## Backend

* Python
* Flask REST API
* Flask-SQLAlchemy

## Machine Learning

* Scikit-learn
* TF-IDF Vectorizer
* Multinomial Naive Bayes
* Linear SVM / Random Forest

## Generative AI

* Large Language Model (LLM)
* Retrieval-Augmented Generation (RAG)
* LangChain
* Sentence Transformers
* FAISS Vector Database

## Database

* MySQL

## Deployment

* Docker
* Docker Compose

---

# Project Structure

```
FYP
│
├── backend
│   │
│   ├── app.py
│   ├── models
│   ├── services
│   │   ├── rag_service.py
│   │   └── llm_service.py
│   │
│   ├── knowledge_base
│   │   ├── scam_types
│   │   ├── phishing
│   │   ├── sms_patterns
│   │   └── prevention
│   │
│   ├── create_vector_db.py
│   ├── test_rag.py
│   └── requirements.txt
│
├── frontend
│
└── README.md
```

---

# Installation

## Prerequisites

* Docker and Docker Compose
* [Ollama](https://ollama.com) running on the host machine with the Qwen model pulled (the backend container reaches it via `host.docker.internal:11434`):

```bash
ollama pull qwen3:8b
```

## 1. Clone Repository

```bash
git clone https://github.com/lms0220/FYP.git

cd FYP
```

---

# Quick Start (Docker)

```bash
docker compose up --build
```

| Service  | URL                     |
| -------- | ----------------------- |
| Frontend | http://localhost:5173   |
| Backend  | http://localhost:5000   |
| MySQL    | localhost:3307 (root, no password, DB `scam_detection`) |

The MySQL credentials above are for local development only.

LLM settings are controlled by environment variables in `docker-compose.yml`:

| Variable                | Default / compose value                           | Purpose                          |
| ----------------------- | ------------------------------------------------- | -------------------------------- |
| `OLLAMA_URL`            | `http://host.docker.internal:11434/api/generate`  | Ollama endpoint                  |
| `OLLAMA_MODEL`          | `qwen3:8b`                                        | Model used for explanations      |
| `OLLAMA_ENABLED`        | `true`                                            | Set `false` to skip LLM analysis |
| `OLLAMA_CONNECT_TIMEOUT`| `5` (compose)                                     | Connect timeout (seconds)        |
| `OLLAMA_READ_TIMEOUT`   | `60` (compose)                                    | Read timeout (seconds)           |

---

# Manual Setup (without Docker)

Backend:

```bash
cd backend
pip install -r requirements.txt
python create_vector_db.py   # build FAISS index from knowledge_base/
python test_rag.py           # optional: verify the RAG pipeline
python app.py                # http://localhost:5000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

---

# API Endpoint

## Scam Prediction

### POST

```
/predict
```

Request:

```json
{
    "text": "Your bank account has been suspended. Verify immediately."
}
```

Response:

```json
{
    "prediction": "MALICIOUS",
    "score": 88,
    "risk_level": "High",
    "llm_analysis": {
        "explanation": "...",
        "recommendation": "..."
    },
    "rag_analysis": {
        "references": [
            "bank_scam.md"
        ]
    }
}
```

---

## Other Endpoints

| Method | Path                | Purpose                      |
| ------ | ------------------- | ---------------------------- |
| POST   | `/register`         | Create an account            |
| POST   | `/login`            | Log in                       |
| GET    | `/logout`           | Log out                      |
| GET    | `/me`               | Current user                 |
| GET    | `/api/history`      | Scan history                 |
| POST   | `/history/delete`   | Delete history entries       |
| GET    | `/api/dashboard`    | Dashboard statistics         |

---

# Future Improvements

* Real-time scam detection browser extension
* Larger cybersecurity knowledge base
* Multi-language scam detection
* Cloud deployment
* Continuous learning from new scam reports

---

# Author

Final Year Project
AI-Driven Scam and Phishing Detection System
