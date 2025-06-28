import asyncio
import os
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import aiosmtplib
import logging
from typing import List # Added import for List
from jinja2 import Environment, FileSystemLoader, TemplateError
from data_loader import load_from_excel, MailSession

# Configure logging for mailer.py
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#########################################
# Environment Configuration
#########################################
def load_environment_variables():
    """
    Loads environment variables from a .env file.

    Returns:
        tuple: A tuple containing the sender's email and Gmail app password.
    """
    load_dotenv(override=True)
    from_email = os.getenv("From_Mail")
    gmail_app_pass = os.getenv("GMAIL_APP_PASS")
    logger.info(f"Using: {from_email}") # Changed from print to logger.info

    if not from_email or not gmail_app_pass:
        raise ValueError("From_Mail and GMAIL_APP_PASS must be set in the .env file.")
    return from_email, gmail_app_pass


#########################################
# Jinja2 HTML Rendering
#########################################
def render_html(template_path: str, session: MailSession) -> str:
    """
    Renders an HTML template using Jinja2 with MailSession data.

    Args:
        template_path (str): The path to the HTML template file.
        session (MailSession): The MailSession object containing recipient data.

    Returns:
        str: The rendered HTML content.
    """
    try:
        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        
        # Render the template with recipient_name from MailSession
        # Use .model_dump() for Pydantic V2 or .dict() for Pydantic V1
        rendered_html = template.render(session.model_dump())
        return rendered_html
    except TemplateError as e:
        logger.error(f"Error rendering Jinja2 template {template_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during HTML rendering: {e}")
        raise

#########################################
# Email Message Creation
#########################################
def create_email(from_email: str,
                 to_email: str,
                 subject: str,
                 html_content: str,
                 attachment_path: str = None) -> MIMEMultipart:
    """
    Creates a MIMEMultipart('mixed') email with:
      1) multipart/alternative (plain-text + HTML)
      2) optional file attachment
    """
    # 1) Top-level “mixed” container to allow attachments
    msg = MIMEMultipart("mixed")
    msg["From"]    = from_email
    msg["To"]      = to_email
    msg["Subject"] = subject

    # 2) Create the alternative part (plain + HTML)
    alt = MIMEMultipart("alternative")

    # 2a) Plain-text fallback
    text_fallback = (
        "Hello,\n\n"
        "This email was sent in HTML format. "
        "Please view it in an email client that supports HTML.\n\n"
        "— Shemeka Industries"
    )
    alt.attach(MIMEText(text_fallback, "plain", _charset="utf-8"))

    # 2b) Your HTML content
    alt.attach(MIMEText(html_content, "html", _charset="utf-8"))

    # 3) Attach the alternative part into the mixed message
    msg.attach(alt)

    # 4) Now attach the file (if provided)
    if attachment_path:
        try:
            ctype, encoding = mimetypes.guess_type(attachment_path)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)

            with open(attachment_path, "rb") as f:
                attachment = MIMEBase(maintype, subtype)
                attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            msg.attach(attachment)
        except FileNotFoundError:
            logger.warning(f"Attachment not found at {attachment_path}. Skipping.") # Changed from print to logger.warning
        except Exception as e:
            logger.warning(f"Could not attach file {attachment_path}: {e}") # Changed from print to logger.warning

    return msg


#########################################
# Asynchronous Email Sending
#########################################
async def send_emails(sessions: List[MailSession], subject: str, template_path: str, attachment_path: str = None, max_emails_per_session: int = None):
    """
    Establishes an asynchronous SMTP connection, logs in, and sends personalized emails to multiple recipients.

    Args:
        sessions (List[MailSession]): A list of MailSession objects containing recipient data.
        subject (str): The subject of the email.
        template_path (str): The path to the HTML template file.
        attachment_path (str, optional): The path to an optional attachment file. Defaults to None.
        max_emails_per_session (int, optional): Maximum number of emails to send per session. Defaults to None (no limit).
    """
    from_email, gmail_app_pass = load_environment_variables()

    smtp = aiosmtplib.SMTP(hostname="smtp.gmail.com", port=587, start_tls=True)

    try:
        await smtp.connect()
        await smtp.login(from_email, gmail_app_pass)

        sent_count = 0
        for session in sessions:
            if max_emails_per_session is not None and sent_count >= max_emails_per_session:
                logger.info(f"Throttling limit reached. Sent {sent_count} emails. Stopping.")
                break

            try:
                # Render personalized HTML content
                personalized_html_content = render_html(template_path, session)
                
                msg = create_email(from_email, session.recipient_email, subject, personalized_html_content, attachment_path)
                await smtp.send_message(msg)
                logger.info(f"Successfully sent email to {session.recipient_email}")
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send email to {session.recipient_email}: {e}")
    except Exception as e:
        logger.error(f"An error occurred during SMTP connection or login: {e}")
    finally:
        if smtp.is_connected:
            try:
                await smtp.quit()
            except Exception as e:
                logger.error(f"Error during SMTP quit: {e}")


#########################################
# Main Execution
#########################################
if __name__ == "__main__":
    EMAIL_SUBJECT = "Great Opportunity for Shoe Manufacturers" # User's current subject
    HTML_TEMPLATE_PATH = "BNI Shoe Perfume.html"
    ATTACHMENT_FILE = None  # Set to "path/to/your/attachment.pdf" if you have an attachment
    MAX_EMAILS_PER_SESSION = None # Set to an integer (e.g., 5) to limit emails per session, or None for no limit

    # Load recipient data using data_loader
    # For demonstration, you might create a dummy Excel file or use a hardcoded list
    # Example: sessions = [MailSession(recipient_email="test@example.com", recipient_name="Test User")]
    
    # Assuming you have an Excel file named 'recipients.xlsx' with 'recipient_email' and 'recipient_name' columns
    # You might need to create a dummy Excel file for testing this part
    # For now, let's use a hardcoded list for demonstration
    
    # Example of loading from a dummy Excel file (uncomment and create file for actual testing)
    # from data_loader import load_from_excel
    # dummy_excel_path = "dummy_recipients.xlsx" # Make sure this file exists for testing
    # sessions = load_from_excel(dummy_excel_path)

    # Hardcoded sessions for initial testing if no Excel file is available
    sessions = [
        MailSession(recipient_email="princekumarpk1920@gmail.com", recipient_name="Prince"), # User's current recipient
        MailSession(recipient_email="vermakiwi17@gmail.com", recipient_name="Nisha is it working?"),
        MailSession(recipient_email="anshuman.iskcon@gmail.com") # No recipient name
    ]

    try:
        asyncio.run(send_emails(sessions, EMAIL_SUBJECT, HTML_TEMPLATE_PATH, ATTACHMENT_FILE, MAX_EMAILS_PER_SESSION))
    except Exception as e:
        logger.error(f"Script execution failed: {e}")