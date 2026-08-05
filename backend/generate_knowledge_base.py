from pathlib import Path


BASE_PATH = Path("knowledge_base")


knowledge_documents = {

"scam_types/investment_scam.md": """
# Scam Type: Investment Scam

## Category
Financial Scam

## Description
Investment scam is a fraud where criminals attract victims by offering fake investment opportunities, unrealistic profits, or guaranteed returns.

## Common Attack Methods
- Fake investment platforms
- Cryptocurrency scams
- Social media investment groups
- Fake financial advisors

## Common Keywords
- Guaranteed profit
- High return
- Risk-free investment
- Limited opportunity
- Earn money quickly
- Crypto investment

## Common Indicators
- Promises unrealistic returns
- Pressure to invest immediately
- Unknown investment companies
- Fake testimonials

## Prevention
- Verify investment companies
- Avoid guaranteed profit promises
- Do research before investing
- Do not transfer money to unknown platforms
""",


"scam_types/job_scam.md": """
# Scam Type: Job Scam

## Category
Employment Scam

## Description
Job scams involve criminals creating fake job opportunities to steal personal information or money from job seekers.

## Common Attack Methods
- Fake recruitment messages
- Fake interview offers
- Requests for registration fees
- Fake work-from-home jobs

## Common Keywords
- Easy money
- Work from home
- High salary
- No experience required
- Registration fee

## Common Indicators
- Unrealistic salary
- No proper interview process
- Requests for payment
- Unknown company information

## Prevention
- Verify company information
- Do not pay recruitment fees
- Check official job platforms
""",


"scam_types/romance_scam.md": """
# Scam Type: Romance Scam

## Category
Social Engineering Scam

## Description
Romance scams involve criminals building fake relationships with victims to gain trust and request money.

## Common Attack Methods
- Fake social media profiles
- Long-distance relationship manipulation
- Emergency money requests

## Common Keywords
- Love
- Emergency
- Need money
- Help me
- Investment opportunity

## Common Indicators
- Avoids video calls
- Requests financial help
- Creates emotional pressure

## Prevention
- Do not send money to online strangers
- Verify identity
- Avoid sharing personal information
""",


"scam_types/loan_scam.md": """
# Scam Type: Loan Scam

## Category
Financial Scam

## Description
Loan scams trick victims by offering fake loans and requesting upfront payments or personal information.

## Common Keywords
- Fast approval
- Low interest
- Instant loan
- No documents required

## Common Indicators
- Requires upfront payment
- Requests personal information
- Unverified lenders

## Prevention
- Verify financial institutions
- Avoid paying processing fees to unknown parties
""",


"scam_types/otp_scam.md": """
# Scam Type: OTP Scam

## Category
Authentication Scam

## Description
OTP scams attempt to steal one-time passwords to access victims' accounts.

## Common Keywords
- OTP
- Verification code
- Security code
- Login verification

## Common Indicators
- Requests OTP sharing
- Fake bank representatives
- Urgent account verification

## Prevention
- Never share OTP
- Banks will not request OTP
""",


"scam_types/qr_scam.md": """
# Scam Type: QR Scam

## Category
Payment Scam

## Description
QR scams use fake QR codes to redirect victims to malicious websites or payment requests.

## Common Keywords
- Scan QR
- Payment
- Discount
- Reward

## Common Indicators
- Unknown QR codes
- Suspicious payment requests

## Prevention
- Verify QR source
- Do not scan unknown QR codes
""",


"phishing/phishing_url.md": """
# Phishing URL Knowledge

## Description
Phishing URLs are malicious links designed to imitate legitimate websites to steal user information.

## Common Characteristics
- Fake login pages
- Suspicious domains
- Shortened URLs
- Random characters

## Indicators
- Unknown domain
- Misspelled brand names
- Urgent messages containing links

## Prevention
- Check website domain
- Avoid clicking unknown links
""",


"phishing/fake_login_page.md": """
# Fake Login Page

## Description
Fake login pages imitate legitimate services to steal usernames, passwords, and banking information.

## Indicators
- Strange domain names
- Incorrect website design
- Requests sensitive information

## Prevention
- Access websites through official apps
- Verify URL before login
""",


"sms_patterns/fake_bank_sms.md": """
# Fake Bank SMS Pattern

## Example
Your account has been suspended. Click the link to verify.

## Scam Indicators
- Account suspension warning
- Urgent action request
- Suspicious URL

## Prevention
- Do not click the link
- Contact bank officially
""",


"sms_patterns/fake_delivery_sms.md": """
# Fake Delivery SMS Pattern

## Example
Your parcel cannot be delivered. Pay RM2 delivery fee.

## Indicators
- Unexpected parcel notification
- Payment request
- Fake tracking link

## Prevention
- Verify courier information
- Avoid unknown links
""",


"prevention/general_prevention.md": """
# General Scam Prevention

## Safety Rules

- Never share OTP or passwords
- Do not click suspicious links
- Verify information through official channels
- Enable multi-factor authentication
- Report suspicious activities
""",

}


for file_path, content in knowledge_documents.items():

    path = BASE_PATH / file_path

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        content.strip(),
        encoding="utf-8"
    )

    print(f"Created: {path}")


print("Knowledge Base generation completed.")