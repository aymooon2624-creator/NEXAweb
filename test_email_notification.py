#!/usr/bin/env python3
"""
Test script for email notification system
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import the email notification function
from utils.notifications import send_project_completion_email

def test_email_notification():
    """Test the email notification system"""
    try:
        print("🧪 Testing email notification system...")
        
        # Check environment variables
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        sender_email = os.getenv('SENDER_EMAIL')
        
        print(f"📧 Email Configuration Status:")
        print(f"   SMTP_SERVER: {'✓' if smtp_server else '✗'}")
        print(f"   SMTP_USERNAME: {'✓' if smtp_username else '✗'}")
        print(f"   SMTP_PASSWORD: {'✓' if smtp_password else '✗'}")
        print(f"   SENDER_EMAIL: {'✓' if sender_email else '✗'}")
        
        if not all([smtp_server, smtp_username, smtp_password, sender_email]):
            print("\n❌ Email credentials not configured. Please set the following environment variables:")
            print("   - SMTP_SERVER")
            print("   - SMTP_USERNAME")
            print("   - SMTP_PASSWORD")
            print("   - SENDER_EMAIL")
            return False
        
        # Test email (you can change this to your email for testing)
        test_email = input("Enter email address for testing (or press Enter to skip): ").strip()
        
        if not test_email:
            print("⏭️ Email test skipped (no email provided)")
            return True
        
        print(f"\n📧 Sending test email to {test_email}...")
        
        success = send_project_completion_email(
            customer_email=test_email,
            customer_name="Test User",
            tracking_code="TEST123",
            project_type="web"
        )
        
        if success:
            print("✅ Email notification test successful!")
            return True
        else:
            print("❌ Email notification test failed!")
            return False
        
    except Exception as e:
        print(f"❌ Error testing email notification: {e}")
        return False

if __name__ == "__main__":
    print("🚀 NEXAweb Email Notification Test")
    print("=" * 40)
    
    success = test_email_notification()
    
    if success:
        print("\n🎉 Email notification system is ready!")
    else:
        print("\n⚠️ Email notification system needs configuration.")
