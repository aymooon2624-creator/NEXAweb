"""
Telegram notifications for NEXAweb
Handles sending notifications to Telegram when new orders are created
"""

import os
import requests
from datetime import datetime

def send_telegram_notification(message):
    """
    Send a message to Telegram bot
    
    Args:
        message (str): Message to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get Telegram configuration from environment variables
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
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
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        # Send the message
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Telegram notification sent successfully")
            return True
        else:
            print(f"❌ Failed to send Telegram notification: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error sending Telegram notification: {e}")
        return False
    except Exception as e:
        print(f"❌ Error sending Telegram notification: {e}")
        return False

def send_new_order_notification(order_data):
    """
    Send notification when a new order is created
    
    Args:
        order_data (dict): Order information
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Format the message
        message = f"""
🆕 <b>New Order Received</b>

📋 <b>Order Details:</b>
👤 <b>Name:</b> {order_data.get('name', 'N/A')}
📧 <b>Email:</b> {order_data.get('email', 'N/A')}
📱 <b>Phone:</b> {order_data.get('phone', 'N/A')}
🏗️ <b>Project Type:</b> {order_data.get('project_type', 'N/A')}
🔖 <b>Tracking Code:</b> <code>{order_data.get('tracking_code', 'N/A')}</code>
📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 <b>Project Details:</b>
{order_data.get('details', 'N/A')[:200]}{'...' if len(order_data.get('details', '')) > 200 else ''}

⚡ <b>Status:</b> 🟡 New
🔗 <b>Track:</b> <a href="http://localhost:5000/status?tracking_code={order_data.get('tracking_code', '')}">View Order</a>
        """.strip()
        
        return send_telegram_notification(message)
        
    except Exception as e:
        print(f"❌ Error creating new order notification: {e}")
        return False

def send_order_status_update_notification(order_data, old_status, new_status):
    """
    Send notification when order status is updated
    
    Args:
        order_data (dict): Order information
        old_status (str): Previous status
        new_status (str): New status
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Status emojis
        status_emojis = {
            'new': '🟡',
            'analyzing': '🔍',
            'coding': '💻',
            'testing': '🧪',
            'completed': '✅'
        }
        
        old_emoji = status_emojis.get(old_status, '📋')
        new_emoji = status_emojis.get(new_status, '📋')
        
        message = f"""
📊 <b>Order Status Updated</b>

📋 <b>Order Details:</b>
👤 <b>Name:</b> {order_data.get('name', 'N/A')}
🔖 <b>Tracking Code:</b> <code>{order_data.get('tracking_code', 'N/A')}</code>
📅 <b>Updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔄 <b>Status Change:</b>
{old_emoji} {old_status.title()} → {new_emoji} {new_status.title()}

🔗 <b>Track:</b> <a href="http://localhost:5000/status?tracking_code={order_data.get('tracking_code', '')}">View Order</a>
        """.strip()
        
        return send_telegram_notification(message)
        
    except Exception as e:
        print(f"❌ Error creating status update notification: {e}")
        return False
