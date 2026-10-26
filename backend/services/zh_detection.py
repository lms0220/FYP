"""Rule-based scam detection for Chinese (Simplified and Traditional) messages.

The English SMS model and the English knowledge base cannot read Chinese, so
Chinese text is scored by weighted scam-pattern categories instead. There is no
labelled Chinese training data in this project; treat scores as heuristic.
"""

import re

MALICIOUS_THRESHOLD = 50

_CJK = re.compile(r"[一-鿿]")
_LETTER = re.compile(r"[A-Za-z一-鿿]")
_LINK = re.compile(r"https?://|www\.|[a-z0-9-]+\.(?:com|cn|top|xyz|cc|vip|net|me|icu|club)\b", re.I)
# Legitimate OTP texts warn the reader not to share the code.
_OTP_WARNING = re.compile(r"(请|請)?(勿|不要|切勿|千万别|千萬別).{0,8}(泄露|泄漏|透露|告知|转告|轉告|分享|告诉|告訴)")

# (code, title, detail, points, all-of regex groups)
_CATEGORIES = [
    ("authority_impersonation", "冒充公检法", "自称公安、检察院或法院，并提到涉案、洗钱或安全账户，是典型的冒充公检法诈骗。", 50,
     [r"公安|警方|警察|检察院|檢察院|法院|法官|通缉|通緝", r"涉嫌|涉案|洗钱|洗錢|冻结|凍結|安全账户|安全賬戶|传唤|傳喚|犯罪"]),
    ("account_freeze", "账户异常/冻结", "声称账户被冻结、异常或存在风险，诱导用户操作，常见于假银行或假支付平台短信。", 35,
     [r"账户|賬戶|账号|賬號|银行卡|銀行卡|支付宝|支付寶|微信支付|信用卡", r"冻结|凍結|异常|異常|暂停|暫停|停用|风险|風險|限制|封停|失效|升级|升級"]),
    ("otp_request", "索取验证码", "要求提供、转发或回复验证码，获得验证码即可盗用账户或转走资金。", 40,
     [r"(提供|告知|告诉|告訴|发给|發給|发送|發送|回复|回覆|转发|轉發|转告|轉告|报给|報給).{0,8}(验证码|驗證碼|动态码|動態碼|校验码)"
      r"|(验证码|驗證碼|动态码|動態碼|校验码).{0,8}(发送给|發送給|发给|發給|告诉|告訴|告知|转发给|轉發給|提供给|提供給|报给|報給)"]),
    ("parcel_fee", "快递/包裹诈骗", "以包裹派送失败、地址有误或需补缴费用为由，诱导点击链接或付款。", 35,
     [r"快递|快遞|包裹|物流|派送|海关|海關", r"失败|失敗|退回|补缴|補繳|补交|運費|运费|关税|關稅|地址有误|地址有誤|重新预约|重新預約|重新派送|滞留|滯留"]),
    ("loan_offer", "贷款诈骗", "宣称低息、免息、无抵押或快速放款，常要求先交手续费或保证金。", 30,
     [r"贷款|貸款|额度|額度|放款|借款", r"免息|低息|无抵押|無抵押|秒到|快速|当天|當天|征信|徵信|手续费|手續費|保证金|保證金|无需|無需"]),
    ("investment_scam", "投资理财诈骗", "承诺高回报、内幕消息或带单，诱导加群、入金或购买虚拟货币。", 35,
     [r"投资|投資|理财|理財|股票|荐股|薦股|牛股|带单|帶單|虚拟币|虛擬幣|比特币|比特幣|USDT|数字货币|數字貨幣", r"高回报|高回報|稳赚|穩賺|内幕|內幕|导师|導師|老师|老師|加群|入群|翻倍|日赚|日賺|收益|保本"]),
    ("job_scam", "刷单/兼职诈骗", "以兼职、刷单、日结高佣为饵，要求垫付资金，是常见的刷单返利骗局。", 40,
     [r"刷单|刷單|兼职|兼職|招聘|日结|日結|在家赚钱|在家賺錢|点赞|點贊|做任务|做任務", r"垫付|墊付|返利|返现|返現|佣金|日赚|日賺|日入|高薪|刷单|刷單|先付|充值"]),
    ("prize_scam", "中奖/领奖诈骗", "声称中奖或获得奖金，要求先缴纳费用或提供个人信息才能领取。", 35,
     [r"中奖|中獎|恭喜|获奖|獲獎|抽中|幸运|幸運", r"领取|領取|奖金|獎金|礼品|禮品|奖品|獎品|红包|紅包|兑换|兌換"]),
]

_URGENCY = r"立即|马上|馬上|尽快|盡快|今日|今天内|今天內|24小时|24小時|限时|限時|否则|否則|逾期|过期|過期|即将|即將|最后|最後"
_LINK_ACTION = r"点击|點擊|点开|點開|登录|登錄|登入|验证|驗證|扫码|掃碼|下载|下載|填写|填寫|查看"
_CONTACT_REDIRECT = r"加微信|加我微信|加V|加v|加QQ|加qq|微信号|微信號|WhatsApp|whatsapp|Telegram|telegram|飞机|飛機|扫码|掃碼|添加好友"


def is_chinese(text):
    """True when CJK characters make up a meaningful share of the letters."""
    letters = _LETTER.findall(text)
    if not letters:
        return False
    cjk = len(_CJK.findall(text))
    return cjk >= 4 and cjk / len(letters) >= 0.3


def extract_link(text):
    match = re.search(r"https?://[^\s，。！？、)）]+|www\.[^\s，。！？、)）]+", text, re.I)
    return match.group(0).rstrip(".,!?") if match else None


def analyze_chinese_sms(text, link_result=None):
    """Score a Chinese message. `link_result` is an optional fusion_engine result
    for a link embedded in the message."""
    factors = []
    is_otp_notice = bool(_OTP_WARNING.search(text))

    for code, title, detail, points, groups in _CATEGORIES:
        if code == "otp_request" and is_otp_notice:
            continue
        if all(re.search(group, text, re.I) for group in groups):
            factors.append({"code": code, "title": title, "detail": detail, "points": points})

    has_link = bool(_LINK.search(text))
    if has_link and re.search(_LINK_ACTION, text):
        factors.append({"code": "link_action", "title": "诱导点击链接", "detail": "短信含链接并要求点击、登录或验证，可能指向钓鱼网站。", "points": 20})
    if link_result and link_result.get("label") == "MALICIOUS":
        factors.append({"code": "malicious_link", "title": "链接存在风险", "detail": "短信中的链接被网址检测判定为可疑。", "points": 40})
    if re.search(_URGENCY, text):
        factors.append({"code": "urgency", "title": "制造紧迫感", "detail": "使用“立即”“逾期”等措辞催促用户马上行动。", "points": 10})
    if re.search(_CONTACT_REDIRECT, text):
        factors.append({"code": "contact_redirect", "title": "引导至私人聊天", "detail": "要求添加微信、QQ 或 Telegram，诈骗常转到私人渠道继续操作。", "points": 15})

    score = min(sum(f["points"] for f in factors), 100)
    malicious = score >= MALICIOUS_THRESHOLD
    risk_level = "High" if score >= 70 else "Medium" if score >= 40 else "Low"

    main = max((f for f in factors if f["code"] in {c[0] for c in _CATEGORIES}), key=lambda f: f["points"], default=None)
    if malicious:
        explanation = " ".join(f["detail"] for f in factors)
        recommendation = "请勿点击链接、转账或提供验证码和个人信息。通过官方 App 或客服电话自行核实，并向警方或反诈平台举报。"
    else:
        explanation = "未发现明显的诈骗特征。" + ("" if not factors else " 注意：" + " ".join(f["detail"] for f in factors))
        recommendation = "对要求转账、提供验证码或点击陌生链接的信息保持警惕。"

    return {
        "prediction": "MALICIOUS" if malicious else "SAFE",
        "score": float(score),
        "risk_level": risk_level,
        "flags": [f["code"] for f in factors],
        "risk_factors": factors,
        "llm_analysis": {
            "threat_type": main["title"] if main and malicious else ("可疑信息" if malicious else "无"),
            "risk_level": risk_level,
            "explanation": explanation,
            "recommendation": recommendation,
        },
    }
