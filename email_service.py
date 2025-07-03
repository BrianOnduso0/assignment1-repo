import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmailService:
    def __init__(self):
        self.email_host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.email_port = int(os.getenv('EMAIL_PORT', 587))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_from = os.getenv('EMAIL_FROM', self.email_user)
        self.email_to = os.getenv('EMAIL_TO', self.email_user)  # Default recipient for contact forms
        
    def send_email(self, subject, message, sender_email=None, recipient=None, html_content=None):
        """
        Send an email with the given subject and message.
        
        Args:
            subject (str): Email subject
            message (str): Email body text
            sender_email (str, optional): Sender's email address for reply-to
            recipient (str, optional): Override default recipient
            html_content (str, optional): HTML version of the email
            
        Returns:
            dict: Result of the email sending operation
        """
        if not self.email_user or not self.email_password:
            print("Email credentials not configured")
            return {
                'success': False,
                'message': 'Email credentials not configured'
            }
            
        try:
            print(f"Attempting to send email to {recipient or self.email_to}")
            
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = recipient or self.email_to
            
            # Add Reply-To header if sender_email is provided
            if sender_email:
                msg['Reply-To'] = sender_email
                
            # Attach plain text version
            msg.attach(MIMEText(message, 'plain'))
            
            # Attach HTML version if provided
            if html_content:
                msg.attach(MIMEText(html_content, 'html'))
            
            # Connect to server and send email
            print(f"Connecting to SMTP server: {self.email_host}:{self.email_port}")
            with smtplib.SMTP(self.email_host, self.email_port) as server:
                server.set_debuglevel(1)  # Add debug output
                print("Starting TLS")
                server.starttls()  # Secure the connection
                print(f"Logging in with user: {self.email_user}")
                server.login(self.email_user, self.email_password)
                print("Sending email")
                server.send_message(msg)
                print("Email sent successfully")
            
            return {
                'success': True,
                'message': 'Email sent successfully'
            }
            
        except Exception as e:
            import traceback
            print(f"Error sending email: {str(e)}")
            print(traceback.format_exc())
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            }
            
    def send_contact_form(self, name, email, subject, message, phone=None):
        """
        Send a contact form submission as an email.
        
        Args:
            name (str): Sender's name
            email (str): Sender's email
            subject (str): Email subject
            message (str): Message content
            phone (str, optional): Sender's phone number
            
        Returns:
            dict: Result of the email sending operation
        """
        # Create email subject
        email_subject = f"Contact Form: {subject}"
        
        # Create plain text email body
        email_body = f"Name: {name}\n"
        email_body += f"Email: {email}\n"
        if phone:
            email_body += f"Phone: {phone}\n"
        email_body += f"\nMessage:\n{message}\n"
        
        # Create HTML email body with proper escaping
        html_body = f"""
<html>
<head></head>
<body>
  <h2>New Contact Form Submission</h2>
  <p><strong>Name:</strong> {name}</p>
  <p><strong>Email:</strong> {email}</p>
"""

        if phone:
            html_body += f"<p><strong>Phone:</strong> {phone}</p>"
        
        # Replace newlines with <br> tags for HTML
        formatted_message = message.replace("\n", "<br>")
        
        html_body += f"""
  <h3>Message:</h3>
  <p>{formatted_message}</p>
</body>
</html>
"""
        
        # Send the email
        return self.send_email(
            subject=email_subject,
            message=email_body,
            sender_email=email,
            html_content=html_body
        )

