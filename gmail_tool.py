import os
import base64
import asyncio
from email.message import EmailMessage
from google.adk.tools import FunctionTool
import json
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.cloud import secretmanager

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_credentials(secret_name="gmail-token"):
    """
    Loads Gmail OAuth credentials from Google Secret Manager.
    The secret must contain a full JSON with refresh_token, client_id, client_secret, and token info.
    """
    try:
        # Automatically detect project ID from environment
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise EnvironmentError("Environment variable GOOGLE_CLOUD_PROJECT is not set")

        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        logging.debug(f"Accessing Gmail credentials from Secret Manager: {name}")

        # Access the secret
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(name=name)
        secret_data = response.payload.data.decode("utf-8")

        # Load credentials JSON
        creds_info = json.loads(secret_data)
        creds = Credentials.from_authorized_user_info(creds_info, GMAIL_SCOPES)

        logging.debug("✅ Successfully loaded Gmail credentials from Secret Manager")
        return creds

    except Exception as e:
        logging.error(f"❌ Failed to load Gmail credentials from Secret Manager: {e}")
        raise


def get_gmail_client():
    """Build and return a Gmail API client using credentials from Secret Manager."""
    creds = get_gmail_credentials()
    service = build("gmail", "v1", credentials=creds)
    logging.debug("📧 Gmail API client initialized successfully")
    return service



async def send_email(recipient_id: str, subject: str, message: str) -> dict:
    """Send an email using the authenticated Gmail account."""
    client = get_gmail_client()

    message_obj = EmailMessage()
    message_obj.set_content(message)
    message_obj["To"] = recipient_id
    message_obj["From"] = "me"
    message_obj["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message_obj.as_bytes()).decode()
    create_message = {"raw": encoded_message}

    send_message = await asyncio.to_thread(
        client.users().messages().send(userId="me", body=create_message).execute
    )

    return {"status": "success", "message_id": send_message["id"]}

send_email_tool = FunctionTool(send_email)

__all__ = ['send_email_tool']

