from flask import url_for
from flask_mail import Message

from backend import mail


def send_verification_email(user):
    """
    Send an email verification link to the user.
    """

    # ========================================================
    # CREATE VERIFICATION LINK
    # ========================================================

    verification_link = url_for(
        "auth.verify_email_web",
        token=user.verification_token,
        _external=True
    )

    # ========================================================
    # CREATE EMAIL
    # ========================================================

    message = Message(
        subject="Verify Your SmartAttend Account",
        recipients=[user.email]
    )

    # ========================================================
    # PLAIN TEXT EMAIL
    # ========================================================

    message.body = f"""
Hello {user.name},

Thank you for registering with SmartAttend.

Please verify your email address by opening the link below:

{verification_link}

This verification link will expire in 24 hours.

If you did not create this account, please ignore this email.

Regards,
SmartAttend Team
"""

    # ========================================================
    # HTML EMAIL
    # ========================================================

    message.html = f"""
<!DOCTYPE html>

<html>

<head>

    <meta charset="UTF-8">

    <title>
        Verify SmartAttend Account
    </title>

</head>

<body style="
    margin:0;
    padding:0;
    background:#f4f6f9;
    font-family:Arial,Helvetica,sans-serif;
">

    <div style="
        max-width:600px;
        margin:40px auto;
        background:#ffffff;
        padding:35px;
        border-radius:12px;
        box-shadow:0 4px 15px rgba(0,0,0,0.08);
    ">

        <h1 style="
            color:#0d6efd;
            margin-bottom:10px;
        ">
            SmartAttend
        </h1>

        <h2>
            Welcome, {user.name}!
        </h2>

        <p>
            Thank you for creating your SmartAttend account.
        </p>

        <p>
            Please verify your email address to activate
            your account.
        </p>

        <div style="
            text-align:center;
            margin:30px 0;
        ">

            <a
                href="{verification_link}"
                style="
                    display:inline-block;
                    padding:14px 25px;
                    background:#0d6efd;
                    color:#ffffff;
                    text-decoration:none;
                    border-radius:7px;
                    font-weight:bold;
                "
            >
                Verify My Email
            </a>

        </div>

        <p>
            This verification link will expire in
            <strong>24 hours</strong>.
        </p>

        <p style="
            color:#666666;
            font-size:14px;
        ">
            If you did not create this account,
            you can safely ignore this email.
        </p>

        <hr style="
            border:0;
            border-top:1px solid #eeeeee;
            margin:30px 0;
        ">

        <p style="
            color:#777777;
            font-size:14px;
        ">
            Regards,<br>
            <strong>SmartAttend Team</strong>
        </p>

    </div>

</body>

</html>
"""

    # ========================================================
    # SEND EMAIL
    # ========================================================

    mail.send(message)


# ============================================================
# PASSWORD RESET EMAIL
# ============================================================

def send_password_reset_email(user):
    """
    Send a password reset link to the user.
    """

    reset_link = url_for(
        "auth.reset_password",
        token=user.reset_token,
        _external=True
    )

    message = Message(
        subject="Reset Your SmartAttend Password",
        recipients=[user.email]
    )

    message.body = f"""
Hello {user.name},

We received a request to reset your SmartAttend password.

Click the link below to choose a new password:

{reset_link}

This link will expire in 1 hour.

If you did not request this, you can safely ignore this email.

Regards,
SmartAttend Team
"""

    message.html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reset SmartAttend Password</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:600px;margin:40px auto;background:#ffffff;padding:35px;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.08);">
        <h1 style="color:#fd7e14;margin-bottom:10px;">SmartAttend</h1>
        <h2>Password Reset Request</h2>
        <p>Hello {user.name},</p>
        <p>We received a request to reset your password. Click below to choose a new one.</p>
        <div style="text-align:center;margin:30px 0;">
            <a href="{reset_link}" style="display:inline-block;padding:14px 25px;background:#fd7e14;color:#ffffff;text-decoration:none;border-radius:7px;font-weight:bold;">
                Reset My Password
            </a>
        </div>
        <p>This link will expire in <strong>1 hour</strong>.</p>
        <p style="color:#666666;font-size:14px;">If you did not request this, you can safely ignore this email.</p>
        <hr style="border:0;border-top:1px solid #eeeeee;margin:30px 0;">
        <p style="color:#777777;font-size:14px;">Regards,<br><strong>SmartAttend Team</strong></p>
    </div>
</body>
</html>
"""

    mail.send(message)