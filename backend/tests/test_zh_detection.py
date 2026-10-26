import pytest

from services.zh_detection import analyze_chinese_sms, is_chinese


@pytest.mark.parametrize(
    "text",
    [
        "您的账户存在异常已被冻结，请立即点击 http://icbc-verify.top 登录验证，否则将永久停用",
        "我是公安局民警，您涉嫌洗钱，请将资金转入安全账户配合调查",
        "兼职刷单，日结300元，先垫付后返利，加微信 abc123",
        "您的快递派送失败，地址有误，请点击 http://sf-post.xyz 补缴运费重新派送",
        "恭喜您中奖，奖金 8000 元，请回复并提供验证码领取",
        "【某某】请把收到的验证码发送给我们客服完成账户核实，立即处理",
    ],
)
def test_chinese_scams_are_malicious(text):
    assert analyze_chinese_sms(text)["prediction"] == "MALICIOUS"


@pytest.mark.parametrize(
    "text",
    [
        "您的验证码是 482913，5分钟内有效，请勿泄露给他人。",
        "【建设银行】您尾号1234的账户于10月26日支出500.00元，余额3200.50元。",
        "你好，明天下午三点开会，别忘了带上资料。",
        "您的快递已到达小区驿站，请凭取件码 6-2-1087 领取。",
    ],
)
def test_legitimate_chinese_messages_are_safe(text):
    assert analyze_chinese_sms(text)["prediction"] == "SAFE"


def test_traditional_characters_are_supported():
    text = "您的賬戶已被凍結，請立即點擊 http://bank-verify.top 登錄驗證"
    assert analyze_chinese_sms(text)["prediction"] == "MALICIOUS"


def test_malicious_link_result_raises_score():
    base = analyze_chinese_sms("您的包裹已发出，请点击 http://a.top 查看")
    boosted = analyze_chinese_sms("您的包裹已发出，请点击 http://a.top 查看", {"label": "MALICIOUS"})
    assert boosted["score"] > base["score"]


def test_is_chinese():
    assert is_chinese("您的账户存在异常")
    assert not is_chinese("Your account is locked")
    assert not is_chinese("Pay now 请")
    assert not is_chinese("")


def test_response_fields_match_predict_contract():
    result = analyze_chinese_sms("兼职刷单日结先垫付后返利")
    assert {"prediction", "score", "risk_level", "flags", "risk_factors", "llm_analysis"} <= result.keys()
    assert {"threat_type", "risk_level", "explanation", "recommendation"} <= result["llm_analysis"].keys()
