import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Environment, BaseLoader
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class EmailTemplates:
    """
    Email templates for InstantIn.me platform.
    Contains HTML and text templates for various email types.
    """
    
    # Email verification template
    EMAIL_VERIFICATION_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Email - InstantIn.me</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .logo { font-size: 28px; font-weight: bold; color: #6366f1; }
            .content { line-height: 1.6; color: #374151; }
            .button { display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 14px; color: #6b7280; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">InstantIn.me</div>
                <h1>Verify Your Email Address</h1>
            </div>
            <div class="content">
                <p>Hello{{ " " + first_name if first_name else "" }},</p>
                <p>Welcome to InstantIn.me! To complete your registration and start building your link-in-bio page, please verify your email address.</p>
                <p>Click the button below to verify your email:</p>
                <p style="text-align: center;">
                    <a href="{{ verification_url }}" class="button">Verify Email Address</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background-color: #f9fafb; padding: 10px; border-radius: 4px;">{{ verification_url }}</p>
                <p><strong>This verification link will expire in 24 hours.</strong></p>
                <p>If you didn't create an account with InstantIn.me, you can safely ignore this email.</p>
            </div>
            <div class="footer">
                <p>Best regards,<br>The InstantIn.me Team</p>
                <p>Need help? Contact us at support@instantin.me</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    EMAIL_VERIFICATION_TEXT = """
    InstantIn.me - Verify Your Email Address
    
    Hello{{ " " + first_name if first_name else "" }},
    
    Welcome to InstantIn.me! To complete your registration and start building your link-in-bio page, please verify your email address.
    
    Click this link to verify your email:
    {{ verification_url }}
    
    This verification link will expire in 24 hours.
    
    If you didn't create an account with InstantIn.me, you can safely ignore this email.
    
    Best regards,
    The InstantIn.me Team
    
    Need help? Contact us at support@instantin.me
    """
    
    # Password reset template
    PASSWORD_RESET_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Password - InstantIn.me</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .logo { font-size: 28px; font-weight: bold; color: #6366f1; }
            .content { line-height: 1.6; color: #374151; }
            .button { display: inline-block; padding: 12px 24px; background-color: #dc2626; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 14px; color: #6b7280; }
            .warning { background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">InstantIn.me</div>
                <h1>Reset Your Password</h1>
            </div>
            <div class="content">
                <p>Hello{{ " " + first_name if first_name else "" }},</p>
                <p>We received a request to reset your password for your InstantIn.me account.</p>
                <p>Click the button below to reset your password:</p>
                <p style="text-align: center;">
                    <a href="{{ reset_url }}" class="button">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background-color: #f9fafb; padding: 10px; border-radius: 4px;">{{ reset_url }}</p>
                <div class="warning">
                    <p><strong>Important:</strong></p>
                    <ul>
                        <li>This password reset link will expire in 1 hour for security reasons.</li>
                        <li>If you didn't request a password reset, you can safely ignore this email.</li>
                        <li>Your password will not be changed unless you click the link above and create a new one.</li>
                    </ul>
                </div>
            </div>
            <div class="footer">
                <p>Best regards,<br>The InstantIn.me Team</p>
                <p>Need help? Contact us at support@instantin.me</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    PASSWORD_RESET_TEXT = """
    InstantIn.me - Reset Your Password
    
    Hello{{ " " + first_name if first_name else "" }},
    
    We received a request to reset your password for your InstantIn.me account.
    
    Click this link to reset your password:
    {{ reset_url }}
    
    IMPORTANT:
    - This password reset link will expire in 1 hour for security reasons.
    - If you didn't request a password reset, you can safely ignore this email.
    - Your password will not be changed unless you click the link above and create a new one.
    
    Best regards,
    The InstantIn.me Team
    
    Need help? Contact us at support@instantin.me
    """
    
    # Welcome email template
    WELCOME_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to InstantIn.me!</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; }
            .logo { font-size: 28px; font-weight: bold; color: #6366f1; }
            .content { line-height: 1.6; color: #374151; }
            .button { display: inline-block; padding: 12px 24px; background-color: #10b981; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; }
            .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 14px; color: #6b7280; }
            .features { background-color: #f9fafb; padding: 20px; border-radius: 6px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">InstantIn.me</div>
                <h1>Welcome to the Future of Link-in-Bio!</h1>
            </div>
            <div class="content">
                <p>Hello {{ first_name or "there" }},</p>
                <p>🎉 Congratulations! Your email has been verified and your InstantIn.me account is ready to go.</p>
                <p>You're now part of a platform that's revolutionizing the link-in-bio space with AI-powered page building, seamless migrations, and collaborative drops.</p>
                
                <div class="features">
                    <h3>Here's what you can do next:</h3>
                    <ul>
                        <li>🎨 <strong>Build your page</strong> - Use our AI page builder for instant, beautiful designs</li>
                        <li>🛒 <strong>Add products</strong> - Start selling digital products and services</li>
                        <li>💰 <strong>Connect payments</strong> - Set up Stripe or PayPal to receive payments</li>
                        <li>📱 <strong>Migrate easily</strong> - Import from Linktree, Stan.store, or Beacons.ai</li>
                        <li>🤝 <strong>Collaborate</strong> - Create collaborative drops with other creators</li>
                    </ul>
                </div>
                
                <p style="text-align: center;">
                    <a href="{{ dashboard_url }}" class="button">Start Building Now</a>
                </p>
                
                <p>Need inspiration? Check out our <a href="{{ examples_url }}">showcase of amazing creator pages</a>.</p>
            </div>
            <div class="footer">
                <p>Ready to build your empire?<br>The InstantIn.me Team</p>
                <p>Questions? Reply to this email or visit our <a href="{{ support_url }}">help center</a></p>
            </div>
        </div>
    </body>
    </html>
    """


class EmailService:
    """
    Email service for InstantIn.me platform.
    Handles sending transactional and notification emails.
    """
    
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_username or "noreply@instantin.me"
        self.from_name = "InstantIn.me"
        
        # Jinja2 environment for template rendering
        self.jinja_env = Environment(loader=BaseLoader())
    
    def _render_template(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render email template with context variables.
        
        Args:
            template_string: Template string with Jinja2 syntax
            context: Variables to inject into template
            
        Returns:
            Rendered template string
        """
        try:
            template = self.jinja_env.from_string(template_string)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            raise ValueError(f"Failed to render email template: {e}")
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Send email using SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            attachments: Optional list of attachments
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    self._add_attachment(message, attachment)
            
            # Send email
            if settings.is_development:
                # In development, log the email instead of sending
                logger.info(f"📧 [DEV] Email would be sent to: {to_email}")
                logger.info(f"📧 [DEV] Subject: {subject}")
                logger.info(f"📧 [DEV] Content: {text_content[:200]}...")
                return True
            else:
                # Production email sending
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password,
                    use_tls=True
                )
                logger.info(f"✅ Email sent successfully to: {to_email}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """
        Add attachment to email message.
        
        Args:
            message: Email message object
            attachment: Dict with 'filename', 'content', and 'content_type'
        """
        try:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment['content'])
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment["filename"]}'
            )
            message.attach(part)
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.get('filename', 'unknown')}: {e}")
    
    def _get_base_url(self) -> str:
        """Get base URL for links in emails."""
        if settings.is_development:
            return "http://localhost:3000"
        return "https://instantin.me"
    
    async def send_email_verification(
        self,
        email: str,
        verification_token: str,
        first_name: Optional[str] = None
    ) -> bool:
        """
        Send email verification email.
        
        Args:
            email: User's email address
            verification_token: JWT verification token
            first_name: User's first name (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            base_url = self._get_base_url()
            verification_url = f"{base_url}/verify-email?token={verification_token}"
            
            context = {
                "first_name": first_name,
                "verification_url": verification_url,
                "email": email
            }
            
            html_content = self._render_template(EmailTemplates.EMAIL_VERIFICATION_HTML, context)
            text_content = self._render_template(EmailTemplates.EMAIL_VERIFICATION_TEXT, context)
            
            success = await self._send_email(
                to_email=email,
                subject="Verify Your Email - InstantIn.me",
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"📧 Email verification sent to: {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send email verification to {email}: {e}")
            return False
    
    async def send_password_reset(
        self,
        email: str,
        reset_token: str,
        first_name: Optional[str] = None
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            email: User's email address
            reset_token: JWT reset token
            first_name: User's first name (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            base_url = self._get_base_url()
            reset_url = f"{base_url}/reset-password?token={reset_token}"
            
            context = {
                "first_name": first_name,
                "reset_url": reset_url,
                "email": email
            }
            
            html_content = self._render_template(EmailTemplates.PASSWORD_RESET_HTML, context)
            text_content = self._render_template(EmailTemplates.PASSWORD_RESET_TEXT, context)
            
            success = await self._send_email(
                to_email=email,
                subject="Reset Your Password - InstantIn.me",
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"🔐 Password reset email sent to: {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send password reset to {email}: {e}")
            return False
    
    async def send_welcome_email(
        self,
        email: str,
        first_name: Optional[str] = None
    ) -> bool:
        """
        Send welcome email after email verification.
        
        Args:
            email: User's email address
            first_name: User's first name (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            base_url = self._get_base_url()
            
            context = {
                "first_name": first_name,
                "dashboard_url": f"{base_url}/dashboard",
                "examples_url": f"{base_url}/showcase",
                "support_url": f"{base_url}/help",
                "email": email
            }
            
            html_content = self._render_template(EmailTemplates.WELCOME_HTML, context)
            
            # Simple text version for welcome
            text_content = f"""
            Welcome to InstantIn.me!
            
            Hello {first_name or "there"},
            
            Congratulations! Your email has been verified and your InstantIn.me account is ready to go.
            
            Start building your link-in-bio page: {context['dashboard_url']}
            
            Best regards,
            The InstantIn.me Team
            """
            
            success = await self._send_email(
                to_email=email,
                subject="🎉 Welcome to InstantIn.me!",
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"🎉 Welcome email sent to: {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {e}")
            return False
    
    async def send_notification_email(
        self,
        email: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> bool:
        """
        Send custom notification email.
        
        Args:
            email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            success = await self._send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"📬 Notification email sent to: {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send notification email to {email}: {e}")
            return False
    
    async def test_email_connection(self) -> bool:
        """
        Test SMTP connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if settings.is_development:
                logger.info("📧 [DEV] Email connection test passed (development mode)")
                return True
            
            # Test SMTP connection
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            ) as smtp:
                await smtp.login(self.smtp_username, self.smtp_password)
                logger.info("✅ SMTP connection test successful")
                return True
                
        except Exception as e:
            logger.error(f"❌ SMTP connection test failed: {e}")
            return False


# Global email service instance
email_service = EmailService()


# Convenience functions
async def send_verification_email(
    email: str, 
    token: str, 
    first_name: Optional[str] = None
) -> bool:
    """Send email verification email."""
    return await email_service.send_email_verification(email, token, first_name)


async def send_password_reset_email(
    email: str, 
    token: str, 
    first_name: Optional[str] = None
) -> bool:
    """Send password reset email."""
    return await email_service.send_password_reset(email, token, first_name)


async def send_welcome_email(
    email: str, 
    first_name: Optional[str] = None
) -> bool:
    """Send welcome email."""
    return await email_service.send_welcome_email(email, first_name)


async def test_email_service() -> bool:
    """Test email service connection."""
    return await email_service.test_email_connection() 