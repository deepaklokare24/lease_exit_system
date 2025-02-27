import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EmailSender:
    """Email utility for sending notifications"""
    
    def __init__(self):
        """Initialize the email sender"""
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL")
        
        if not all([self.smtp_host, self.smtp_username, self.smtp_password, self.from_email]):
            logger.warning("Email configuration is incomplete. Email sending will not work.")
    
    async def send_email(self, to_email: str, subject: str, message: str, 
                        attachments: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            message: Email message (HTML format is supported)
            attachments: Optional list of attachments
            
        Returns:
            Whether the email was sent successfully
        """
        if not all([self.smtp_host, self.smtp_username, self.smtp_password, self.from_email]):
            logger.error("Email configuration is incomplete. Cannot send email.")
            return False
        
        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Add the message body
        msg.attach(MIMEText(message, "html"))
        
        # Add attachments if any
        if attachments:
            for attachment in attachments:
                file_path = attachment.get("file_path")
                filename = attachment.get("filename") or os.path.basename(file_path)
                
                with open(file_path, "rb") as file:
                    part = MIMEApplication(file.read(), Name=filename)
                
                part["Content-Disposition"] = f'attachment; filename="{filename}"'
                msg.attach(part)
        
        try:
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            ) as smtp:
                await smtp.login(self.smtp_username, self.smtp_password)
                await smtp.send_message(msg)
                
                logger.info(f"Email sent successfully to {to_email}")
                return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    async def send_notification(self, to_email: str, notification_type: str, 
                               context: Dict[str, Any]) -> bool:
        """Send a notification email based on a template
        
        Args:
            to_email: Recipient email address
            notification_type: Type of notification
            context: Template context variables
            
        Returns:
            Whether the email was sent successfully
        """
        # Get the subject and message template based on notification type
        subject, message = self._get_notification_template(notification_type, context)
        
        # Send the email
        return await self.send_email(to_email, subject, message)
    
    def _get_notification_template(self, notification_type: str, 
                                  context: Dict[str, Any]) -> tuple:
        """Get the subject and message template for a notification type
        
        Args:
            notification_type: Type of notification
            context: Template context variables
            
        Returns:
            Tuple of (subject, message)
        """
        # Define templates for different notification types
        templates = {
            "initial_submission": (
                f"New Lease Exit Submission - {context.get('property_address', 'N/A')}",
                """
                <p>A new lease exit has been submitted.</p>
                <p><strong>Property:</strong> {property_address}</p>
                <p><strong>Lease ID:</strong> {lease_id}</p>
                <p><strong>Exit Date:</strong> {exit_date}</p>
                <p>Please review the details and complete your required forms.</p>
                <p>You can access the lease exit at: <a href="{url}">{url}</a></p>
                """
            ),
            "form_submission": (
                f"Form Submitted for Lease Exit - {context.get('property_address', 'N/A')}",
                """
                <p>A form has been submitted for lease exit at {property_address}.</p>
                <p><strong>Form Type:</strong> {form_type}</p>
                <p><strong>Submitted By:</strong> {submitted_by}</p>
                <p>Please review the updated information.</p>
                <p>You can access the lease exit at: <a href="{url}">{url}</a></p>
                """
            ),
            "approval_request": (
                f"Approval Required - {context.get('property_address', 'N/A')}",
                """
                <p>Your approval is required for lease exit at {property_address}.</p>
                <p>Please review the details and provide your approval decision.</p>
                <p>You can access the lease exit at: <a href="{url}">{url}</a></p>
                """
            ),
            "approval_complete": (
                f"Lease Exit Approved - {context.get('property_address', 'N/A')}",
                """
                <p>The lease exit for {property_address} has been approved by all stakeholders.</p>
                <p>The lease exit is now ready for execution.</p>
                <p>You can access the lease exit at: <a href="{url}">{url}</a></p>
                """
            ),
            "approval_rejected": (
                f"Lease Exit Rejected - {context.get('property_address', 'N/A')}",
                """
                <p>The lease exit for {property_address} has been rejected.</p>
                <p><strong>Rejected By:</strong> {rejected_by}</p>
                <p><strong>Comments:</strong> {comments}</p>
                <p>Please review the feedback and make necessary adjustments.</p>
                <p>You can access the lease exit at: <a href="{url}">{url}</a></p>
                """
            )
        }
        
        # Get the template for the notification type
        subject_template, message_template = templates.get(
            notification_type, 
            (
                "Lease Exit Update",
                """
                <p>There is an update for lease exit at {property_address}.</p>
                <p>You can access the lease exit at: <a href="{url}">{url}</a></p>
                """
            )
        )
        
        # Format the template with context variables
        message = message_template.format(**context)
        
        return subject_template, message
    
    async def send_bulk_emails(self, recipients: List[str], subject: str, 
                              message: str) -> Dict[str, bool]:
        """Send emails to multiple recipients
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            message: Email message
            
        Returns:
            Dictionary of email addresses and success status
        """
        results = {}
        for recipient in recipients:
            results[recipient] = await self.send_email(recipient, subject, message)
        return results

# Create a singleton instance
email_sender = EmailSender()
