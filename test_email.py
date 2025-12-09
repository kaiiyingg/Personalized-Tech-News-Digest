"""
Test script for email configuration (SendGrid + SMTP)
Run this to verify your email settings work before testing the full forgot password flow
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import SendGrid
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("WARNING: SendGrid not installed. Install with: pip install sendgrid")

def test_sendgrid():
    """Test SendGrid configuration"""
    if not SENDGRID_AVAILABLE:
        return False
        
    print("\nTesting SendGrid Configuration...")
    
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('FROM_EMAIL', 'noreply@yourdomain.com')
    from_name = os.getenv('FROM_NAME', 'TechPulse Support')
    
    print(f"From: {from_name} <{from_email}>")
    print(f"API Key: {'Set' if sendgrid_api_key and sendgrid_api_key != 'your_sendgrid_api_key_here' else 'Not set'}")
    
    if not sendgrid_api_key or sendgrid_api_key == 'your_sendgrid_api_key_here':
        print("ERROR: SendGrid API key not configured!")
        print("Please set SENDGRID_API_KEY in your .env file")
        return False
    
    # Ask for test email
    test_email = input("\nEnter your email address to send test to: ").strip()
    if not test_email:
        print("ERROR: No email provided")
        return False
    
    try:
        # Create test email
        message = Mail(
            from_email=(from_email, from_name),
            to_emails=test_email,
            subject="TechPulse SendGrid Test",
            html_content="""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #007bff;">SendGrid Test Successful!</h2>
                <p>Hi there!</p>
                <p>This is a test email from your TechPulse application using <strong>SendGrid</strong>.</p>
                <div style="background: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                    <p><strong>Your SendGrid configuration is working correctly!</strong></p>
                </div>
                <p>Your password reset feature is ready to use.</p>
                <p>Best regards,<br>TechPulse Team</p>
            </body>
            </html>
            """,
            plain_text_content="""
SendGrid Test Successful! 

Hi there!

This is a test email from your TechPulse application using SendGrid.

Your SendGrid configuration is working correctly!

Your password reset feature is ready to use.

Best regards,
TechPulse Team
            """
        )
        
        # Send email
        print("Sending test email via SendGrid...")
        sg = SendGridAPIClient(api_key=sendgrid_api_key)
        response = sg.send(message)
        
        print(f"SendGrid Success! Status: {response.status_code}")
        print(f"Test email sent to: {test_email}")
        print("Check your inbox (and spam folder) for the test email.")
        return True
        
    except Exception as e:
        print(f"SendGrid Error: {e}")
        return False

def main():
    print("TechPulse Email Configuration Test")
    print("=" * 50)
    
    sendgrid_success = test_sendgrid()
    smtp_success = test_smtp()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"SendGrid: {'Working' if sendgrid_success else 'Failed'}")
    print(f"SMTP:     {'Working' if smtp_success else 'Failed'}")
    
    if sendgrid_success:
        print("\nRecommended: Use SendGrid for production (better deliverability)")
    elif smtp_success:
        print("\nSMTP working - good for development and small-scale production")
    else:
        print("\nNo email method is working. Please check your configuration.")

if __name__ == "__main__":
    main()