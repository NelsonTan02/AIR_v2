import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage


load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
 
 
def is_email_configured() -> bool:
    """Check whether Gmail credentials are present in the environment."""
    return bool(GMAIL_ADDRESS and GMAIL_APP_PASSWORD)
 
 
def send_email(to_address: str, subject: str, body: str) -> None:
    """
    Send a plain-text email via Gmail SMTP.
 
    Raises RuntimeError with a readable message if credentials are
    missing or the send fails, so the caller can show it in the UI.
    """
 
    if not is_email_configured():
        raise RuntimeError(
            "Email is not configured. Add GMAIL_ADDRESS and "
            "GMAIL_APP_PASSWORD to your .env file."
        )
 
    if not to_address or "@" not in to_address:
        raise RuntimeError(f"Invalid recipient address: {to_address!r}")
 
    message = EmailMessage()
    message["From"] = GMAIL_ADDRESS
    message["To"] = to_address
    message["Subject"] = subject
    message.set_content(body)
 
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(message)
 
    except smtplib.SMTPAuthenticationError as e:
        raise RuntimeError(
            "Gmail rejected the login. Make sure GMAIL_APP_PASSWORD is an "
            "app password (not your normal Google password) and that "
            "2-Step Verification is enabled on the account."
        ) from e
 
    except (smtplib.SMTPException, OSError) as e:
        raise RuntimeError(f"Failed to send email: {e}") from e
 