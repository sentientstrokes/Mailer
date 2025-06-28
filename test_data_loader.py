import pytest
import pandas as pd
import io
import logging
from data_loader import MailSession, load_from_excel, load_from_crm, load_from_other_source
from pydantic import ValidationError

# Configure logging for tests to capture messages
@pytest.fixture(autouse=True)
def setup_logging(caplog):
    caplog.set_level(logging.INFO)
    caplog.set_level(logging.ERROR)

def create_excel_file(data: dict) -> io.BytesIO:
    """
    Helper function to create an in-memory Excel file from a dictionary.
    """
    df = pd.DataFrame(data)
    excel_file = io.BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)
    return excel_file

def test_load_from_excel_success(caplog):
    """
    Tests the successful loading of data from an Excel file.
    """
    try:
        data = {
            "recipient_email": ["test1@example.com", "test2@example.com"],
            "recipient_name": ["John Doe", "Jane Smith"]
        }
        excel_file = create_excel_file(data)
        
        # Mock pd.read_excel to use the in-memory file
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(pd, "read_excel", lambda x: pd.read_excel(excel_file))
            
            sessions = load_from_excel("dummy_path.xlsx") # Path doesn't matter due to mocking
            
            assert len(sessions) == 2
            assert sessions[0].recipient_email == "test1@example.com"
            assert sessions[0].recipient_name == "John Doe"
            assert sessions[1].recipient_email == "test2@example.com"
            assert sessions[1].recipient_name == "Jane Smith"
            
            assert "Successfully loaded Excel file" in caplog.text
            assert "Skipping row" not in caplog.text
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}", pytrace=True)
    else:
        pass # All assertions passed

def test_load_from_excel_failure_corrupt_columns(caplog):
    """
    Tests loading from an Excel file with corrupt/missing columns.
    """
    try:
        data = {
            "email": ["invalid-email", "test3@example.com"], # Missing 'recipient_email'
            "name": ["Corrupt User", "Valid User"]
        }
        excel_file = create_excel_file(data)

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(pd, "read_excel", lambda x: pd.read_excel(excel_file))
            
            sessions = load_from_excel("dummy_path.xlsx")
            
            assert len(sessions) == 0
            assert "Skipping row" in caplog.text
            assert "validation error" in caplog.text
            assert "Successfully loaded Excel file" in caplog.text
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}", pytrace=True)
    else:
        pass

def test_load_from_excel_invalid_email(caplog):
    """
    Tests loading from an Excel file with an invalid email format.
    """
    try:
        data = {
            "recipient_email": ["invalid-email-format", "test4@example.com"],
            "recipient_name": ["User A", "User B"]
        }
        excel_file = create_excel_file(data)

        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(pd, "read_excel", lambda x: pd.read_excel(excel_file))
            
            sessions = load_from_excel("dummy_path.xlsx")
            
            assert len(sessions) == 1
            assert sessions[0].recipient_email == "test4@example.com"
            assert "Skipping row 1 due to validation error" in caplog.text
            assert "value is not a valid email address" in caplog.text
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}", pytrace=True)
    else:
        pass

def test_load_from_excel_file_not_found(caplog):
    """
    Tests the case where the Excel file does not exist.
    """
    try:
        sessions = load_from_excel("non_existent_file.xlsx")
        assert len(sessions) == 0
        assert "Error: Excel file not found at non_existent_file.xlsx" in caplog.text
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}", pytrace=True)
    else:
        pass

@pytest.mark.skip(reason="Not implemented yet")
def test_load_from_crm_stub():
    """
    Stub test for load_from_crm.
    """
    try:
        sessions = load_from_crm("dummy_api_key")
        assert len(sessions) == 0
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}", pytrace=True)
    else:
        pass

@pytest.mark.skip(reason="Not implemented yet")
def test_load_from_other_source_stub():
    """
    Stub test for load_from_other_source.
    """
    try:
        sessions = load_from_other_source({"key": "value"})
        assert len(sessions) == 0
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}", pytrace=True)
    else:
        pass