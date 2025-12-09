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
    print("⚠️ SendGrid not installed. Install with: pip install sendgrid")

def test_sendgrid():
    """Test SendGrid configuration"""
    if not SENDGRID_AVAILABLE:
        return False
        
    print("\n🧪 Testing SendGrid Configuration...")
    
    sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('FROM_EMAIL', 'noreply@yourdomain.com')
    from_name = os.getenv('FROM_NAME', 'TechPulse Support')
    
    print(f"📧 From: {from_name} <{from_email}>")
    print(f"🔑 API Key: {'✅ Set' if sendgrid_api_key and sendgrid_api_key != 'your_sendgrid_api_key_here' else '❌ Not set'}")
    
    if not sendgrid_api_key or sendgrid_api_key == 'your_sendgrid_api_key_here':
        print("❌ SendGrid API key not configured!")
        print("Please set SENDGRID_API_KEY in your .env file")
        return False
    
    # Ask for test email
    test_email = input("\n📧 Enter your email address to send test to: ").strip()
    if not test_email:
        print("❌ No email provided")
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
                <h2 style="color: #007bff;">🎉 SendGrid Test Successful!</h2>
                <p>Hi there!</p>
                <p>This is a test email from your TechPulse application using <strong>SendGrid</strong>.</p>
                <div style="background: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                    <p><strong>✅ Your SendGrid configuration is working correctly!</strong></p>
                </div>
                <p>Your password reset feature is ready to use.</p>
                <p>Best regards,<br>TechPulse Team</p>
            </body>
            </html>
            """,
            plain_text_content="""
SendGrid Test Successful! 🎉

Hi there!

This is a test email from your TechPulse application using SendGrid.

✅ Your SendGrid configuration is working correctly!

Your password reset feature is ready to use.

Best regards,
TechPulse Team
            """
        )
        
        # Send email
        print("📤 Sending test email via SendGrid...")
        sg = SendGridAPIClient(api_key=sendgrid_api_key)
        response = sg.send(message)
        
        print(f"✅ SendGrid Success! Status: {response.status_code}")
        print(f"📧 Test email sent to: {test_email}")
        print("Check your inbox (and spam folder) for the test email.")
        return True
        
    except Exception as e:
        print(f"❌ SendGrid Error: {e}")
        return False

def test_smtp():
    """Test SMTP configuration"""
    print("\n🧪 Testing SMTP Configuration...")
    
    # Get email settings from environment
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL', smtp_username)
    from_name = os.getenv('FROM_NAME', 'TechPulse')
    
    print(f"📧 SMTP Server: {smtp_server}:{smtp_port}")
    print(f"📧 Username: {smtp_username}")
    print(f"📧 From: {from_name} <{from_email}>")
    
    # Check if credentials are configured
    if not smtp_username or not smtp_password:
        print("❌ Error: SMTP credentials not configured!")
        print("Please set SMTP_USERNAME and SMTP_PASSWORD in your .env file")
        return False
        
    if smtp_password == "your_app_password_here":
        print("❌ Error: Please replace 'your_app_password_here' with your actual app password")
        return False
    
    # Ask for test email
    test_email = input("\n📧 Enter your email address to send test to: ").strip()
    if not test_email:
        test_email = smtp_username  # Fallback to sender
    
    try:
        # Create test email
        msg = MIMEMultipart()
        msg['From'] = f"{from_name} <{from_email}>" if from_name else from_email
        msg['To'] = test_email
        msg['Subject'] = "TechPulse SMTP Test"
        
        body = """
Hi there!

This is a test email from your TechPulse application using SMTP.

✅ Your SMTP configuration is working correctly!

Your password reset feature is ready to use.

Best regards,
TechPulse Team
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print("📤 Sending test email via SMTP...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(from_email, test_email, text)
        
        print(f"✅ SMTP Success! Test email sent to: {test_email}")
        print("Check your inbox (and spam folder) for the test email.")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed!")
        print("Please check your SMTP_USERNAME and SMTP_PASSWORD")
        print("For Gmail, make sure you're using an App Password, not your regular password")
        return False
        
    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        return False

def main():
    print("🔧 TechPulse Email Configuration Test")
    print("=" * 50)
    
    sendgrid_success = test_sendgrid()
    smtp_success = test_smtp()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"SendGrid: {'✅ Working' if sendgrid_success else '❌ Failed'}")
    print(f"SMTP:     {'✅ Working' if smtp_success else '❌ Failed'}")
    
    if sendgrid_success:
        print("\n🎉 Recommended: Use SendGrid for production (better deliverability)")
    elif smtp_success:
        print("\n✅ SMTP working - good for development and small-scale production")
    else:
        print("\n❌ No email method is working. Please check your configuration.")

if __name__ == "__main__":
    main()