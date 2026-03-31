import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "mayapreneur64@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")
MAIL_TO = os.getenv("MAIL_TO", "mayapreneur64@gmail.com")


def send_email(name: str, email: str, phone: str, message: str) -> bool:
    has_message = bool(message.strip())

    if has_message:
        subject = "New Contact Enquiry – MayaPreneur"
        body = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333">
        <h2 style="color:#2e7d32">Contact Enquiry</h2>
        <table cellpadding="8" style="border-collapse:collapse;width:100%">
          <tr><td><strong>Name</strong></td><td>{name}</td></tr>
          <tr><td><strong>Email</strong></td><td>{email}</td></tr>
          <tr><td><strong>Phone</strong></td><td>{phone}</td></tr>
          <tr><td><strong>Message</strong></td><td>{message.replace(chr(10), '<br>')}</td></tr>
        </table>
        </body></html>
        """
    else:
        subject = "New Subscription – MayaPreneur"
        body = f"""
        <html><body style="font-family:Arial,sans-serif;color:#333">
        <h2 style="color:#1565c0">New Subscriber</h2>
        <table cellpadding="8" style="border-collapse:collapse;width:100%">
          <tr><td><strong>Name</strong></td><td>{name}</td></tr>
          <tr><td><strong>Email</strong></td><td>{email}</td></tr>
          <tr><td><strong>Phone</strong></td><td>{phone}</td></tr>
        </table>
        </body></html>
        """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    msg["Reply-To"] = email
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, MAIL_TO, msg.as_string())
        return True
    except Exception as e:
        app.logger.error("Email send failed: %s", e)
        return False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/gallery")
def gallery():
    return render_template("gallery.html")


@app.route("/reviews")
def reviews():
    return render_template("reviews.html")


@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


@app.route("/thank-you")
def thank_you():
    status = request.args.get("status", "")
    return render_template("thank-you.html", status=status)


@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy.html")


@app.route("/refund-policy")
def refund_policy():
    return render_template("refund-policy.html")


@app.route("/terms-of-use")
def terms_of_use():
    return render_template("terms-of-use.html")


@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not phone:
        return redirect(url_for("index") + "?error=missing_fields#Contact-Us")

    success = send_email(name, email, phone, message)
    if success:
        return redirect(url_for("thank_you") + "?status=success")
    else:
        return redirect(url_for("index") + "?error=email_failed#Contact-Us")


if __name__ == "__main__":
    app.run(debug=True)
