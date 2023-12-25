import datetime
import jwt
from fastapi.background import BackgroundTasks
from fastapi import FastAPI, Request
from pydantic import EmailStr
from app.db import User
from fastapi_mail import (
    ConnectionConfig,
    MessageSchema,
    FastMail
)
import secret

conf = ConnectionConfig(
    MAIL_USERNAME="creola.nicolas@ethereal.email",
    MAIL_PASSWORD="9V4bh27eZK1rbnDDc4",
    MAIL_FROM="creola.nicolas@ethereal.email",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.ethereal.email",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False
)


async def send_email(email: EmailStr, token: str):
    link = f"{secret.site_url}/auth/verify?token={token}"

    # Send the verification email
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
</head>
<body>
    <div style="display: flex; align-items: center; flex-direction: column;">
        <h3>Account Verification</h3>

        <br>

        <p>
            Thank you for choosing us. Please click on the button below
            to verify your account.
        </p>

        <a style="display: margin-top: 1rem; padding: 1rem; border-radius: 0.5rem;
            font-size: 1rem; text-decoration: none; background: #0275d8; color: white;"
            href="{link}">
            Verify your email
        </a>
    </div>
</body>
</html>
"""

    message = MessageSchema(
        subject="Ashte account verification",
        recipients=email.email,  # List of recipients,
        body=template,
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
# not storing verification link and verification token



async def send_password_email(email: EmailStr, token: str):
    # Construct the link to reset the password
    link = f"{secret.forgot_pass_form_url}?token={token}"

    # Send the email with the link to reset the password
    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
</head>
<body>
  <div style="display: flex; align-items: center; flex-direction: column;">
    <h3>Reset Your Password</h3>

    <br>

    <p>
      Click on the button below to reset your password.
    </p>

    <a style="display: margin-top: 1rem; padding: 1rem; border-radius: 0.5rem;
      font-size: 1rem; text-decoration: none; background: #0275d8; color: white;"
      href="{link}">
      Reset Your Password
    </a>
  </div>
</body>
</html>
"""

    message = MessageSchema(
        subject="Ashte account Password Reset",
        recipients=email.email,  # List of recipients,
        body=template,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

async def order_success_email(email: EmailStr, order_id: int):
    # Create email template
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <div style="display: flex; align-items: center; flex-direction: column;">
            <h3>Your Order Has Been Placed Successfully!</h3>
            <p>Your payment has been processed, and your order with ID {order_id} is now being prepared for shipping.</p>
            <p>You can view your order history, including this order, by logging into your account.</p>
            <p>Thank you for choosing Ashte!</p>
        </div>
    </body>
    </html>
    """

    # Send the email
    message = MessageSchema(
        subject="Ashte Order Confirmation",
        recipients=email.email,
        body=template,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
