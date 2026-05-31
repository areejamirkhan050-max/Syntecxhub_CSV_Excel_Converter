"""
Email Sender Bot
Syntecxhub Internship - Task 3, Project 3
"""

import smtplib
import csv
import logging
import sys
import time
import os
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("email_sender.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EmailSenderBot:
    def __init__(self, sender_email, app_password,
                 smtp_host="smtp.gmail.com", smtp_port=587):
        self.sender_email = sender_email
        self.app_password = app_password
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.send_log = []

    def connect(self):
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.ehlo()
            server.starttls()
            server.login(self.sender_email, self.app_password)
            logger.info("Connected to SMTP server successfully.")
            return server
        except smtplib.SMTPAuthenticationError:
            logger.error("Authentication failed. Check email and app password.")
            return None
        except Exception as e:
            logger.error(f"SMTP connection error: {e}")
            return None

    def build_message(self, recipient, name, subject, body_template, attachment_path=None):
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = recipient
        msg["Subject"] = subject
        body = body_template.replace("{name}", name).replace("{email}", recipient)
        msg.attach(MIMEText(body, "plain"))
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                filename = os.path.basename(attachment_path)
                part.add_header("Content-Disposition", f"attachment; filename={filename}")
                msg.attach(part)
                logger.info(f"Attached: {filename}")
            except Exception as e:
                logger.warning(f"Could not attach file: {e}")
        return msg

    def send_email(self, server, recipient, name, subject,
                   body_template, attachment_path=None, retries=3, delay=5):
        msg = self.build_message(recipient, name, subject, body_template, attachment_path)
        for attempt in range(1, retries + 1):
            try:
                server.sendmail(self.sender_email, recipient, msg.as_string())
                logger.info(f"Email sent to: {recipient} ({name})")
                self.send_log.append({
                    "name": name, "email": recipient,
                    "status": "SUCCESS",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "attempts": attempt
                })
                return True
            except smtplib.SMTPRecipientsRefused:
                logger.error(f"Recipient refused: {recipient}")
                break
            except smtplib.SMTPException as e:
                logger.warning(f"Attempt {attempt} failed: {e}")
                if attempt < retries:
                    time.sleep(delay)
        self.send_log.append({
            "name": name, "email": recipient,
            "status": "FAILED",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "attempts": retries
        })
        return False

    def send_bulk(self, csv_path, subject, body_template,
                  attachment_path=None, delay_between=2):
        if not os.path.exists(csv_path):
            logger.error(f"CSV not found: {csv_path}")
            return
        recipients = []
        try:
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name", "").strip()
                    email = row.get("email", "").strip()
                    if name and email and "@" in email:
                        recipients.append({"name": name, "email": email})
                    else:
                        logger.warning(f"Skipping invalid row: {row}")
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return
        if not recipients:
            logger.error("No valid recipients found.")
            return
        logger.info(f"Found {len(recipients)} recipients.")
        server = self.connect()
        if not server:
            return
        success = 0
        for i, r in enumerate(recipients, 1):
            logger.info(f"Sending {i}/{len(recipients)}: {r['email']}")
            if self.send_email(server, r["email"], r["name"],
                               subject, body_template, attachment_path):
                success += 1
            time.sleep(delay_between)
        server.quit()
        print("\n" + "="*50)
        print(f"  Total: {len(recipients)} | Success: {success} | Failed: {len(recipients)-success}")
        print("="*50)
        self.save_log()

    def save_log(self, log_path="send_status.csv"):
        if not self.send_log:
            return
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name","email","status","timestamp","attempts"])
            writer.writeheader()
            writer.writerows(self.send_log)
        logger.info(f"Log saved: {log_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Email Sender Bot | Syntecxhub Task 3 Project 3")
    parser.add_argument("--sender", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--subject", default="Automated Email from Syntecxhub Bot")
    parser.add_argument("--body", default="Hello {name},\n\nThis is an automated message.\n\nRegards,\nSyntecxhub Team")
    parser.add_argument("--attachment", default=None)
    parser.add_argument("--delay", type=int, default=2)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    logger.info("Email Sender Bot | Syntecxhub Task 3 Project 3")
    bot = EmailSenderBot(args.sender, args.password)
    bot.send_bulk(args.csv, args.subject, args.body, args.attachment, args.delay)