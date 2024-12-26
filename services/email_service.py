from config.email import email_settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Dict, List, Tuple
import ssl
import time

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.host = email_settings.smtp_host
        self.port = email_settings.smtp_port
        self.username = email_settings.smtp_username
        self.password = email_settings.smtp_password
        self.from_email = email_settings.smtp_from_email
        self.from_name = email_settings.smtp_from_name
        self.max_retries = 3
        self.retry_delay = 5  # seconds

    def test_connection(self) -> bool:
        """Test the SMTP connection and credentials."""
        try:
            logger.info("Testing SMTP connection...")
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                logger.info("SMTP connection test successful")
                return True
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Please check your credentials.")
            return False
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False

    def send_email(self, to_email: str, subject: str, content: str, retry_count: int = 0) -> bool:
        """Send an email with retry logic."""
        try:
            message = MIMEMultipart()
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject

            message.attach(MIMEText(content, "html"))

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(message)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError) as e:
            if retry_count < self.max_retries:
                logger.warning(f"Connection error, retrying... ({retry_count + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
                return self.send_email(to_email, subject, content, retry_count + 1)
            logger.error(f"Failed to send email to {to_email} after {self.max_retries} retries: {str(e)}")
            return False

        except smtplib.SMTPRecipientsRefused:
            logger.error(f"Invalid recipient: {to_email}")
            return False

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_bulk_emails(self, recipients: List[Dict[str, str]], subject: str, content_template: str) -> Tuple[List[str], List[str]]:
        """
        Send emails to multiple recipients with tracking.
        Returns tuple of (successful_emails, failed_emails)
        """
        successful_emails = []
        failed_emails = []

        for recipient in recipients:
            try:
                # Replace placeholders in content
                personalized_content = content_template
                for key, value in recipient.items():
                    if key != 'email':
                        personalized_content = personalized_content.replace(f"{{{key}}}", value)

                if self.send_email(recipient['email'], subject, personalized_content):
                    successful_emails.append(recipient['email'])
                else:
                    failed_emails.append(recipient['email'])

                # Add a small delay between sends to avoid rate limiting
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing recipient {recipient['email']}: {str(e)}")
                failed_emails.append(recipient['email'])

        return successful_emails, failed_emails

email_service = EmailService() 