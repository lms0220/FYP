import pytest

from services.detection import (
    detect_input_type,
    extract_domain,
    extract_url,
    fusion_engine,
    rule_engine,
    sms_model,
    sms_vectorizer,
    trust_engine,
)


def codes(factors):
    return {factor["code"] for factor in factors}


@pytest.mark.parametrize(
    "text, expected",
    [
        ("https://example.com/login", "url"),
        ("www.example.org", "url"),
        ("Your parcel is held, pay a fee", "sms"),
        ("Call me back when free", "sms"),
    ],
)
def test_detect_input_type(text, expected):
    assert detect_input_type(text) == expected


def test_extract_url_strips_trailing_punctuation():
    assert extract_url("Visit http://bit.ly/abc, now!") == "http://bit.ly/abc"


def test_extract_domain_drops_port_and_scheme():
    assert extract_domain("http://Example.com:8080/path") == "example.com"


def test_rule_engine_flags_ip_and_http():
    score, factors = rule_engine("http://192.168.0.1/verify")
    assert {"ip_url", "no_https", "credential_request"} <= codes(factors)
    assert score == sum(f["points"] for f in factors)


def test_rule_engine_flags_brand_impersonation():
    _, factors = rule_engine("http://paypa1-secure.xyz/login")
    assert "brand_impersonation" in codes(factors)


def test_rule_engine_score_is_capped_at_100():
    score, _ = rule_engine("http://192.168.0.1/login-verify-secure-account-password-update-urgent-suspended-immediately-" + "a" * 90)
    assert score <= 100


def test_trust_engine_trusts_subdomain_of_allowlisted_domain():
    assert trust_engine("https://mail.google.com") > 0
    assert trust_engine("https://evil-google.xyz") == 0


def test_fusion_flags_obvious_phishing_as_malicious():
    result = fusion_engine("http://paypa1-login-verify.xyz/account/update")
    assert result["label"] == "MALICIOUS"
    assert result["risk_level"] in {"Medium", "High"}


def test_fusion_keeps_trusted_domain_safe():
    result = fusion_engine("https://www.google.com")
    assert result["label"] == "SAFE"


def test_fusion_score_equals_sum_of_factors():
    result = fusion_engine("http://bit.ly/verify-account")
    total = sum(f["points"] for f in result["risk_factors"])
    assert result["final_score"] == max(0, min(100, total))


def test_sms_model_separates_clear_spam_from_ham():
    spam = "WINNER!! You have won a 1000 prize. Call 09061701461 now to claim, text STOP to end"
    ham = "Ok see you at lunch tomorrow, I'll bring the notes"
    preds = sms_model.predict(sms_vectorizer.transform([spam, ham]))
    assert str(preds[0]).lower() in {"spam", "1", "malicious"}
    assert str(preds[1]).lower() in {"ham", "0", "safe"}
