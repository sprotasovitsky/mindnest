"""Email service using Resend API."""

import logging

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Send transactional emails via Resend."""

    RESEND_API_URL = "https://api.resend.com/emails"

    @classmethod
    async def send_verification_email(cls, to_email: str, name: str, token: str) -> bool:
        """Send email verification link.

        Args:
            to_email: Recipient email address
            name: User's name for personalization
            token: Verification token to include in link

        Returns:
            True if email was sent successfully
        """
        settings = get_settings()
        verify_url = f"{settings.frontend_url}/verify-email?token={token}"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #1a1a1a;">Welcome to MindNest, {name}!</h2>
    <p>Please verify your email address by clicking the button below:</p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{verify_url}"
           style="background-color: #6366f1; color: white; padding: 14px 28px;
                  text-decoration: none; border-radius: 8px; display: inline-block;
                  font-weight: 500;">
            Verify Email
        </a>
    </p>
    <p style="color: #666; font-size: 14px;">This link expires in 24 hours.</p>
    <p style="color: #666; font-size: 14px;">If you didn't create this account, you can ignore this email.</p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
    <p style="color: #999; font-size: 12px;">The MindNest Team</p>
</body>
</html>
"""

        return await cls._send_email(
            to_email,
            "Verify your MindNest email",
            html,
        )

    @classmethod
    async def send_password_reset_code(cls, to_email: str, name: str, code: str) -> bool:
        """Send password reset code.

        Args:
            to_email: Recipient email address
            name: User's name for personalization
            code: 6-digit reset code

        Returns:
            True if email was sent successfully
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <h2 style="color: #1a1a1a;">Reset your password</h2>
    <p>Hi {name},</p>
    <p>We received a request to reset your password. Use this code to complete the reset:</p>
    <p style="text-align: center; margin: 30px 0;">
        <span style="background-color: #f3f4f6; padding: 16px 32px; border-radius: 8px;
                     font-size: 32px; font-weight: bold; letter-spacing: 8px; font-family: monospace;">
            {code}
        </span>
    </p>
    <p style="color: #666; font-size: 14px;">This code expires in 10 minutes.</p>
    <p style="color: #666; font-size: 14px;">If you didn't request this, you can ignore this email.</p>
    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
    <p style="color: #999; font-size: 12px;">The MindNest Team</p>
</body>
</html>
"""

        return await cls._send_email(
            to_email,
            "Your MindNest password reset code",
            html,
        )

    @classmethod
    async def _send_email(cls, to_email: str, subject: str, html: str) -> bool:
        """Send an email via Resend API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html: HTML content

        Returns:
            True if email was sent successfully
        """
        settings = get_settings()

        if not settings.resend_api_key:
            logger.warning("Resend API key not configured, skipping email to %s***", to_email[:3])
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    cls.RESEND_API_URL,
                    headers={
                        "Authorization": f"Bearer {settings.resend_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": settings.email_from,
                        "to": [to_email],
                        "subject": subject,
                        "html": html,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    logger.info("Email sent successfully to %s***", to_email[:3])
                    return True
                else:
                    logger.error(
                        "Failed to send email: %d - %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False

        except httpx.TimeoutException:
            logger.error("Email send timeout for %s***", to_email[:3])
            return False
        except Exception as e:
            logger.error("Email send error: %s", str(e)[:100])
            return False
