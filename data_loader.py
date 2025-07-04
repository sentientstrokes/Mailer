"""
This module provides functions for loading email session data from various sources.
The intent is to keep data-loading isolated and extensible.
Currently, it supports loading data from Excel files.
Future plans include support for CRM and other data sources.
For any non-standard library used, Context7 MCP will be explored for best practices.
"""

import logging
from enum import Enum 
from typing import List, Optional
import secrets # Import secrets for UID generation

import pandas as pd
from pydantic import BaseModel, EmailStr, ValidationError, Field, model_validator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Mode(str, Enum):
    """
    Enum for the mode of mail.
    """
    CAMP = "camp"
    LEAD = "lead"
    CLIENT = "client"
    ADHOC = "adhoc"

class MailType(str, Enum):
    """
    Enum for the type of mail.
    """
    INTRO = "intro"
    FOLLOWUP = "followup"
    REPLY = "reply"

class MailSession(BaseModel):
    """
    Pydantic model for a mail session recipient.
    """
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    campaign_id: int = Field(..., description="Campaign ID, manually provided during initialization.")
    mail_type: MailType = Field(..., description="Type of mail, e.g., 'intro', 'followup'")
    mode: Mode = Field(Mode.CAMP, description="Mode of mail, e.g., 'camp', 'lead', 'adhoc'")
    uid: str = Field(default_factory=lambda: "", exclude=True, description="Unique identifier for the mail session, auto-generated")

    @model_validator(mode='after')
    def generate_uid(self) -> 'MailSession':
        """
        Generates a unique ID for the mail session upon initialization.
        UID format: {mode}{campaign_id:04}_{mail_type}_{short_hex}
        """
        if not self.uid: # Only generate if UID is not already set
            short_hex = secrets.token_hex(2) # Generates a 4-character hex string
            self.uid = f"{self.mode.value}{self.campaign_id:04d}_{self.mail_type.value}_{short_hex}"
        return self

def load_from_excel(path: str) -> List[MailSession]:
    """
    Loads mail session data from an Excel (.xlsx) file.

    Args:
        path (str): The path to the Excel file.

    Returns:
        List[MailSession]: A list of validated MailSession objects.
    """
    mail_sessions: List[MailSession] = []
    try:
        df = pd.read_excel(path)
        logger.info(f"Successfully loaded Excel file from {path}. Rows: {len(df)}")

        for index, row in df.iterrows():
            try:
                # Assuming 'recipient_email' and 'recipient_name' are column names in the Excel file
                # Adjust column names as per your Excel file structure
                session_data = {
                    "recipient_email": row.get("Email"),
                    "recipient_name": row.get("Name") if pd.notna(row.get("Name")) else None,
                    # mail_type is a required field | Options: INTRO, FOLLOWUP, REPLY
                    "mail_type": MailType.INTRO,
                    # mode has a default value (Mode.CAMP) | Options: CAMP, LEAD, CLIENT, ADHOC
                    "mode": Mode.CAMP,
                    # Hardcoded Campaign ID that will later be defined by AI
                    "campaign_id": 1001
                }
                mail_session = MailSession.model_validate(session_data)
                mail_sessions.append(mail_session)
            except ValidationError as e:
                logger.error(f"Skipping Row #{index + 1} due to validation error: {e} - Data: {row.to_dict()}")
            except Exception as e:
                logger.error(f"Skipping Row #{index + 1} due to unexpected error: {e} - Data: {row.to_dict()}")
    except FileNotFoundError:
        logger.error(f"Error: Excel file not found at {path}")
    except Exception as e:
        logger.error(f"Error loading Excel file {path}: {e}")
    return mail_sessions

def load_from_crm(api_key: str) -> List[MailSession]:
    """
    (Stub) Loads mail session data from a CRM system.

    Args:
        api_key (str): The API key for CRM authentication.

    Returns:
        List[MailSession]: A list of MailSession objects.
    """
    logger.info("CRM data loading is not yet implemented.")
    return []

def load_from_other_source(config: dict) -> List[MailSession]:
    """
    (Stub) Loads mail session data from another generic source.

    Args:
        config (dict): Configuration dictionary for the data source.

    Returns:
        List[MailSession]: A list of MailSession objects.
    """
    logger.info("Other data source loading is not yet implemented.")
    return []

if __name__ == "__main__":
    # Example usage:
    # Create a dummy Excel file for testing if you don't have one
    # import pandas as pd
    # dummy_data = {
    #     "recipient_email": ["test1@example.com", "invalid-email", "test2@example.com"],
    #     "recipient_name": ["John Doe", "Jane Doe", None]
    # }
    # dummy_df = pd.DataFrame(dummy_data)
    # dummy_excel_path = "dummy_recipients.xlsx"
    # dummy_df.to_excel(dummy_excel_path, index=False)
    # logger.info(f"Dummy Excel file created at {dummy_excel_path}")

    # Load data from the dummy Excel file
    sessions = load_from_excel("/Users/anshumanngupta/Documents/trialExcel.xlsx")
    for session in sessions:
        logger.info(f"Loaded session: {session.recipient_email}, {session.recipient_name}")

    # Example of calling stub functions
    # crm_sessions = load_from_crm("your_api_key")
    # other_sessions = load_from_other_source({"source": "some_db"})
    pass