"""Email notification support for deployment events."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Send email notifications for deployment events."""

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: str = "vm-tool@localhost",
        use_tls: bool = True,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.use_tls = use_tls

    def send_email(
        self, to_emails: List[str], subject: str, body: str, html: bool = False
    ) -> bool:
        """Send email notification.

        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Email body
            html: If True, send as HTML email

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = ", ".join(to_emails)
            msg["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Connect to SMTP server
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            # Login if credentials provided
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)

            # Send email
            server.sendmail(self.from_email, to_emails, msg.as_string())
            server.quit()

            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def deployment_success(
        self, to_emails: List[str], host: str, duration: float, **kwargs
    ):
        """Send deployment success notification."""
        subject = f"✅ Deployment Successful - {host}"
        body = f"""
Deployment completed successfully!

Host: {host}
Duration: {duration:.2f} seconds
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Additional Details:
{self._format_kwargs(kwargs)}
"""
        return self.send_email(to_emails, subject, body)

    def deployment_failed(self, to_emails: List[str], host: str, error: str, **kwargs):
        """Send deployment failure notification."""
        subject = f"❌ Deployment Failed - {host}"
        body = f"""
Deployment failed!

Host: {host}
Error: {error}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Additional Details:
{self._format_kwargs(kwargs)}

Please check the logs for more information.
"""
        return self.send_email(to_emails, subject, body)

    def rollback_success(self, to_emails: List[str], host: str, **kwargs):
        """Send rollback success notification."""
        subject = f"🔄 Rollback Successful - {host}"
        body = f"""
Rollback completed successfully!

Host: {host}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Additional Details:
{self._format_kwargs(kwargs)}
"""
        return self.send_email(to_emails, subject, body)

    def health_check_failed(
        self, to_emails: List[str], host: str, check_type: str, **kwargs
    ):
        """Send health check failure notification."""
        subject = f"⚠️ Health Check Failed - {host}"
        body = f"""
Health check failed!

Host: {host}
Check Type: {check_type}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Additional Details:
{self._format_kwargs(kwargs)}

Please investigate immediately.
"""
        return self.send_email(to_emails, subject, body)

    @staticmethod
    def _format_kwargs(kwargs: dict) -> str:
        """Format kwargs as readable string."""
        if not kwargs:
            return "None"
        return "\n".join(f"  {k}: {v}" for k, v in kwargs.items())
