# Email Sender Script Plan

This document outlines the plan for creating a Python script to send HTML emails asynchronously using Gmail's SMTP server.

## 1. Project Setup and Dependencies:

*   **Main Script:** `mailer.py`
*   **HTML Template:** `BNI Shoe Perfume.html`
*   **Environment Variables:** `.env` (will contain `GMAIL_APP_PASS` and `From_Mail`)

**Dependencies to be installed:**

*   `python-dotenv`: For loading environment variables.
*   `aiosmtplib`: For asynchronous SMTP communication.

## 2. Core Functionality Breakdown:

*   **`load_environment_variables()` function:**
    *   **Purpose:** To load the necessary environment variables from the `.env` file.
    *   **Implementation:**
        *   Call `load_dotenv()` from the `dotenv` package.
        *   Retrieve `GMAIL_APP_PASS` and `From_Mail` using `os.getenv()`.
        *   Perform basic validation to ensure these variables are loaded.
        *   Return `(from_email, gmail_app_pass)`.

*   **`load_html_template(filepath)` function:**
    *   **Purpose:** To read the HTML content from the specified file.
    *   **Implementation:**
        *   Open the `filepath` in read mode (`'r'`) with `utf-8` encoding.
        *   Read the entire content of the file.
        *   Return the HTML content as a string.
        *   Include error handling for `FileNotFoundError`.

*   **`create_email(from_email, to_email, subject, html_content, attachment_path=None)` function:**
    *   **Purpose:** To construct a `MIMEMultipart` email message with HTML content and an optional attachment.
    *   **Implementation:**
        *   Create a `MIMEMultipart("alternative")` object.
        *   Set `From`, `To`, and `Subject` headers.
        *   Attach the `html_content` as `MIMEText(html_content, "html")`.
        *   **Optional Attachment:**
            *   If `attachment_path` is provided:
                *   Determine the MIME type of the attachment using `mimetypes.guess_type()`.
                *   Read the attachment file in binary mode (`'rb'`).
                *   Create a `MIMEBase` object and add the attachment.
                *   Encode the payload in Base64.
                *   Add `Content-Disposition` header.
                *   Attach the `MIMEBase` object to the message.
        *   Return the constructed `MIMEMultipart` message.

*   **`send_emails(recipients, subject, html_content, attachment_path=None, max_emails_per_session=None)` function:**
    *   **Purpose:** To establish an asynchronous SMTP connection, log in, and send emails to multiple recipients with throttling and error handling.
    *   **Implementation:**
        *   Load `from_email` and `gmail_app_pass` using `load_environment_variables()`.
        *   Initialize `aiosmtplib.SMTP(hostname="smtp.gmail.com", port=587, use_tls=True)`.
        *   `await smtp.connect()`
        *   `await smtp.starttls()`
        *   `await smtp.login(from_email, gmail_app_pass)`
        *   Initialize a counter for sent emails.
        *   Loop through `recipients`:
            *   Check if `max_emails_per_session` is set and if the limit has been reached. If so, `break` the loop.
            *   Inside the loop, use a `try-except` block:
                *   Call `create_email()` to get the message for the current recipient.
                *   `await smtp.send_message(message)`.
                *   Print a success message.
                *   Increment the sent email counter.
            *   `except Exception as e`:
                *   Print a failure message with the error.
                *   Continue to the next recipient.
        *   `await smtp.quit()` to close the connection.

*   **Main Execution Block (`if __name__ == "__main__":`)**
    *   Define `RECIPIENTS` list.
    *   Define `EMAIL_SUBJECT` as "TesterMail".
    *   Define `ATTACHMENT_FILE` (optional, set to `None` if no attachment).
    *   Define `MAX_EMAILS_PER_SESSION` (strictly optional, set to `None` for no throttling).
    *   Call `load_html_template()` with `BNI Shoe Perfume.html`.
    *   Use `asyncio.run(send_emails(...))` to start the asynchronous process.

## 3. High-Level Flow Diagram:

```mermaid
graph TD
    A[Start] --> B{Load Environment Variables};
    B --> C{Load HTML Template};
    C --> D{Define Recipients, Subject, Attachment, Throttling};
    D --> E[asyncio.run(send_emails)];

    E --> F[send_emails Function];
    F --> G{Initialize & Connect SMTP Client};
    G --> H{Login to SMTP Server};
    H --> I{Loop through Recipients};
    I -- For each recipient --> J{Check Throttling Limit};
    J -- Limit not reached --> K{Create Email Message};
    K --> L{Try Sending Email};
    L -- Success --> M[Log Success];
    L -- Failure --> N[Log Failure & Continue];
    I -- End of recipients or throttling limit --> O[Close SMTP Connection];
    O --> P[End send_emails];
    P --> Q[End Script];