"""
Notifications System for NEXAweb
Telegram and Email notifications with proper error handling and formatting
"""

import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict, Any


def send_telegram_message(message: str, parse_mode: str = 'HTML') -> bool:
    """
    Send a message to Telegram bot
    
    Args:
        message (str): Message to send (supports HTML formatting)
        parse_mode (str): Parse mode ('HTML' or 'MarkdownV2')
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get Telegram configuration from environment variables
        bot_token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("❌ Telegram credentials not found in environment variables")
            print(f"   BOT_TOKEN: {'✓' if bot_token else '✗'}")
            print(f"   CHAT_ID: {'✓' if chat_id else '✗'}")
            return False
        
        # Telegram API URL
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Prepare the message
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        # Send the message
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Telegram message sent successfully")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Telegram request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Telegram request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in Telegram notification: {e}")
        return False


def notify_new_order(order_data: Dict[str, Any]) -> bool:
    """
    Send notification for new order
    
    Args:
        order_data (Dict): Order information
        
    Returns:
        bool: True if successful
    """
    try:
        customer_name = order_data.get('name', 'Unknown')
        project_type = order_data.get('project_type', 'Unknown')
        tracking_code = order_data.get('tracking_code', 'Unknown')
        
        message = f"""
📦 <b>NEW ORDER RECEIVED</b>

👤 <b>Customer:</b> {customer_name}
🏗️ <b>Project Type:</b> {project_type.title()}
🔍 <b>Tracking Code:</b> <code>{tracking_code}</code>
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔗 <b>Admin Panel:</b> <a href="http://localhost:5000/admin">View Orders</a>
        """
        
        return send_telegram_message(message)
        
    except Exception as e:
        print(f"❌ Error creating new order notification: {e}")
        return False


def notify_price_update(order_id: str, old_prices: Dict[str, float], new_prices: Dict[str, float]) -> bool:
    """
    Send notification for price update
    
    Args:
        order_id (str): Order ID
        old_prices (Dict): Previous prices
        new_prices (Dict): New prices
        
    Returns:
        bool: True if successful
    """
    try:
        old_total = old_prices.get('total_price', 0)
        old_deposit = old_prices.get('deposit_amount', 0)
        new_total = new_prices.get('total_price', 0)
        new_deposit = new_prices.get('deposit_amount', 0)
        new_remaining = new_prices.get('remaining_balance', 0)
        
        message = f"""
💰 <b>PRICE UPDATE ALERT</b>

🆔 <b>Order ID:</b> <code>{order_id}</code>

📊 <b>Price Changes:</b>
<b>Total:</b> <code>${old_total:.2f}</code> → <code>${new_total:.2f}</code>
<b>Deposit:</b> <code>${old_deposit:.2f}</code> → <code>${new_deposit:.2f}</code>
<b>Remaining:</b> <code>${new_remaining:.2f}</code>

⏰ <b>Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return send_telegram_message(message)
        
    except Exception as e:
        print(f"❌ Error creating price update notification: {e}")
        return False


def notify_security_alert(username: str, ip_address: str, user_agent: str = "") -> bool:
    """
    Send security notification for failed login attempt
    
    Args:
        username (str): Username used in attempt
        ip_address (str): IP address of attempt
        user_agent (str): User agent string
        
    Returns:
        bool: True if successful
    """
    try:
        # Truncate user agent if too long
        user_agent_display = user_agent[:100] + "..." if len(user_agent) > 100 else user_agent
        
        message = f"""
🚨 <b>SECURITY ALERT</b>

🔐 <b>Failed Login Attempt</b>

👤 <b>Username:</b> <code>{username}</code>
🌐 <b>IP Address:</b> <code>{ip_address}</code>
💻 <b>User Agent:</b> <code>{user_agent_display}</code>
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ <b>Action Required:</b> Review security logs
        """
        
        return send_telegram_message(message)
        
    except Exception as e:
        print(f"❌ Error creating security alert notification: {e}")
        return False


def notify_system_status(status: str, message: str) -> bool:
    """
    Send system status notification
    
    Args:
        status (str): Status type (INFO, WARNING, ERROR)
        message (str): Status message
        
    Returns:
        bool: True if successful
    """
    try:
        emoji_map = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'SUCCESS': '✅'
        }
        
        emoji = emoji_map.get(status, '📢')
        
        notification_message = f"""
{emoji} <b>{status} NOTIFICATION</b>

{message}

⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return send_telegram_message(notification_message)
        
    except Exception as e:
        print(f"❌ Error creating system status notification: {e}")
        return False


# Test function for development
def test_telegram_connection() -> bool:
    """
    Test Telegram bot connection
    
    Returns:
        bool: True if connection successful
    """
    test_message = """
🧪 <b>TELEGRAM CONNECTION TEST</b>

✅ <b>NEXAweb Notifications System</b>
⏰ <b>Test Time:</b> {}

🔧 <b>System Status:</b> <code>ONLINE</code>
📡 <b>Bot Status:</b> <code>CONNECTED</code>
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    return send_telegram_message(test_message)


def send_project_completion_email(customer_email: str, customer_name: str, tracking_code: str, project_type: str) -> bool:
    """
    Send project completion notification email to customer
    
    Args:
        customer_email (str): Customer's email address
        customer_name (str): Customer's name
        tracking_code (str): Order tracking code
        project_type (str): Type of project (web, mobile, other)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        sender_email = os.getenv('SENDER_EMAIL')
        
        if not all([smtp_server, smtp_username, smtp_password, sender_email]):
            print("❌ Email credentials not found in environment variables")
            print(f"   SMTP_SERVER: {'✓' if smtp_server else '✗'}")
            print(f"   SMTP_USERNAME: {'✓' if smtp_username else '✗'}")
            print(f"   SMTP_PASSWORD: {'✓' if smtp_password else '✗'}")
            print(f"   SENDER_EMAIL: {'✓' if sender_email else '✗'}")
            return False
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = f"NEXAweb <{sender_email}>"
        msg['To'] = customer_email
        msg['Subject'] = f"🎉 Your Project is Complete! - Order {tracking_code}"
        
        # Email body
        email_body = f"""
Dear {customer_name},

Great news! Your project has been completed successfully.

📋 Project Details:
• Tracking Code: {tracking_code}
• Project Type: {project_type.title()}
• Status: Completed

🎯 Next Steps:
1. Please check your order status page for final payment details
2. Complete the remaining payment to receive your project files
3. Once payment is confirmed, we'll deliver all project files to you

📱 Track Your Project:
Visit your order status page to view all details and complete the payment:
https://nexa-web.com/status/{tracking_code}

If you have any questions or need assistance, please don't hesitate to contact us.

Thank you for choosing NEXAweb!

Best regards,
The NEXAweb Team
        """
        
        msg.attach(MIMEText(email_body, 'plain'))
        
        # Send email
        print(f"📧 Sending project completion email to {customer_email}")
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        text = msg.as_string()
        server.sendmail(sender_email, customer_email, text)
        server.quit()
        
        print(f"✅ Project completion email sent successfully to {customer_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending project completion email: {e}")
        return False


if __name__ == "__main__":
    # Test the connection when run directly
    print("🧪 Testing Telegram connection...")
    if test_telegram_connection():
        print("✅ Telegram connection test successful!")
    else:
        print("❌ Telegram connection test failed!")
