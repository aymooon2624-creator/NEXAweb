"""
NEXAweb Application Entry Point
Clean, minimal Flask application with blueprint registration
"""

import os
import logging
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Load environment variables FIRST
load_dotenv()

# Import database and models
from database import init_mongo
from models import User

# Import blueprints
from routes.main import main_bp
from routes.auth import auth_bp, load_user
from routes.admin import admin_bp
from routes.orders import orders_bp

# Create Flask application
app = Flask(__name__)

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration - force use of environment variable for security
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    raise ValueError("SECRET_KEY environment variable is required for security. Please set a strong secret key.")
app.secret_key = secret_key

# URL configuration for proper url_for generation
# app.config['SERVER_NAME'] = 'localhost:5000'  # Commented out for Render deployment
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'https'  # Updated for Render deployment

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Babel configuration for internationalization
app.config['LANGUAGES'] = ['en', 'ar']
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'

def get_locale():
    """Get locale from session or browser preference"""
    from flask import session, request
    
    # Check if language is set in session
    if 'lang' in session and session['lang'] in app.config['LANGUAGES']:
        return session['lang']
    
    # Fallback to browser language
    return request.accept_languages.best_match(app.config['LANGUAGES']) or app.config['BABEL_DEFAULT_LOCALE']

def send_tailored_payment_notification(customer_name, tracking_code, amount, payment_type, transaction_id, photo_file=None, photo_path=None):
    """
    Send tailored payment notification to Telegram with photo and conditional footer
    """
    import requests
    from datetime import datetime
    
    # Telegram configuration - get from environment variables
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    logger.info(f"=== send_tailored_payment_notification called ===")
    logger.info(f"TELEGRAM_TOKEN exists: {bool(TELEGRAM_TOKEN)}")
    logger.info(f"CHAT_ID exists: {bool(CHAT_ID)}")
    logger.info(f"Customer: {customer_name}, Tracking: {tracking_code}, Amount: {amount}")
    logger.info(f"Payment type: {payment_type}")
    logger.info(f"Transaction ID: {transaction_id}")
    logger.info(f"Photo file provided: {bool(photo_file)}")
    
    # Validate required environment variables
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logger.error("❌ Telegram configuration missing - check environment variables")
        logger.error(f"TELEGRAM_TOKEN: {TELEGRAM_TOKEN}")
        logger.error(f"CHAT_ID: {CHAT_ID}")
        return False
    
    # Determine payment type text in Arabic
    payment_type_text = "الأولى" if payment_type == "deposit" else "الثانية"
    
    # Format current date
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create caption for photo
    caption = f"""
🔵 <b>إشعار دفع جديد (NEXAweb)</b>

👤 <b>الزبون:</b> {customer_name}
📋 <b>رمز التتبع:</b> {tracking_code}
💰 <b>المبلغ المدفوع:</b> ${amount}
💳 <b>نوع الدفعة:</b> {payment_type_text}
🆔 <b>رقم العملية:</b> {transaction_id}
📅 <b>التاريخ:</b> {current_date}"""
    
    # Add footer for non-deposit payments
    if payment_type != 'deposit':
        caption += f"""

══════════════
<b>END OF PAYMENT</b>
══════════════"""
    
    caption = caption.strip()
    
    # Send photo with caption
    try:
        if photo_file:
            # Send with photo file
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            
            files = {'photo': (f"{tracking_code}.jpg", photo_file, 'image/jpeg')}
            data = {
                'chat_id': CHAT_ID,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            
            logger.info(f"Sending photo to URL: {url}")
            logger.info(f"Photo data: chat_id={CHAT_ID}, caption_length={len(caption)}")
            
            response = requests.post(url, files=files, data=data, timeout=10)
            logger.info(f"Photo response status: {response.status_code}")
            logger.info(f"Photo response body: {response.text}")
            
            if response.status_code == 200:
                logger.info("✅ Telegram payment notification with photo sent successfully")
                return True
            else:
                logger.error(f"❌ Failed to send Telegram photo: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        elif photo_path:
            # Send with photo path
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            
            with open(photo_path, 'rb') as f:
                files = {'photo': (f"{tracking_code}.jpg", f, 'image/jpeg')}
                data = {
                    'chat_id': CHAT_ID,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                logger.info(f"Sending photo to URL: {url}")
                logger.info(f"Photo data: chat_id={CHAT_ID}, caption_length={len(caption)}")
                
                response = requests.post(url, files=files, data=data, timeout=10)
                logger.info(f"Photo response status: {response.status_code}")
                logger.info(f"Photo response body: {response.text}")
                
                if response.status_code == 200:
                    logger.info("✅ Telegram payment notification with photo sent successfully")
                    return True
                else:
                    logger.error(f"❌ Failed to send Telegram photo: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False
        else:
            # Send text message only
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            
            payload = {
                'chat_id': CHAT_ID,
                'text': caption,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            logger.info(f"Sending text to URL: {url}")
            logger.info(f"Payload: {payload}")
            
            response = requests.post(url, json=payload, timeout=10)
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                logger.info("✅ Telegram payment notification sent successfully")
                return True
            else:
                logger.error(f"❌ Failed to send Telegram notification: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error sending Telegram notification: {str(e)}")
        return False

def send_order_confirmation_email(customer_email, customer_name):
    """Send order confirmation email to customer with memory optimization"""
    logger.info(f"=== send_order_confirmation_email called ===")
    logger.info(f"Customer: {customer_name}, Email: {customer_email}")
    
    # Validate required environment variables
    if not all([app.config.get('MAIL_SERVER'), app.config.get('MAIL_USERNAME'), app.config.get('MAIL_PASSWORD')]):
        logger.error("❌ Email configuration missing - check environment variables")
        return False
    
    try:
        # Import only when needed to reduce memory footprint
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Create lightweight HTML template (minimal memory usage)
        html_template = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Order Confirmation - NEXAweb</title>
<style>body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;line-height:1.6;color:#333;max-width:600px;margin:0 auto;padding:20px;background-color:#f8f9fa}
.container{background-color:#fff;padding:30px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1);border-left:5px solid #00d4aa}
.header{text-align:center;margin-bottom:30px;padding-bottom:20px;border-bottom:2px solid #e9ecef}
.logo{font-size:28px;font-weight:bold;color:#00d4aa;text-decoration:none;margin-bottom:10px}
.content{margin-bottom:30px}
.footer{text-align:center;margin-top:30px;padding-top:20px;border-top:2px solid #e9ecef;color:#6c757d;font-size:14px}
.highlight{background-color:#e8f5f0;padding:15px;border-radius:5px;margin:20px 0;border-left:4px solid #00d4aa}
</style></head><body><div class="container">
<div class="header"><a href="#" class="logo">NEXAweb</a><p style="color:#6c757d;margin:10px 0 0 0">Professional Web & Mobile Development</p></div>
<div class="content"><h2 style="color:#00d4aa;margin-bottom:20px">Order Received Successfully!</h2>
<p>Dear <strong>{customer_name}</strong>,</p>
<p>We are pleased to inform you that we have successfully received your order. Our team is currently reviewing the details, and we will get back to you shortly with the total project cost and required deposit amount.</p>
<div class="highlight"><p><strong>Please note:</strong> Once payment is completed, we will immediately begin working on your project.</p></div>
<p>Thank you for choosing <strong style="color:#00d4aa">NEXAweb</strong>. We look forward to working with you!</p></div>
<div class="footer"><p><strong>Best regards,<br>NEXAweb Team</strong></p><p style="margin-top:15px;font-size:12px">This is an automated message. Please do not reply to this email.</p></div></div></body></html>"""
        
        # Create email message efficiently
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Order Received Successfully - NEXAweb'
        msg['From'] = f"NEXAweb Team <{app.config['MAIL_USERNAME']}>"
        msg['To'] = customer_email
        
        # Attach HTML part
        html_part = MIMEText(html_template.format(customer_name=customer_name), 'html', 'utf-8')
        msg.attach(html_part)
        
        # Connect to SMTP with timeout and memory management
        server = None
        try:
            server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'], timeout=30)
            
            if app.config['MAIL_USE_TLS']:
                server.starttls()
            
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            
            logger.info(f"✅ Order confirmation email sent successfully to {customer_email}")
            return True
            
        except smtplib.SMTPException as smtp_error:
            logger.error(f"❌ SMTP Error: {str(smtp_error)}")
            return False
        except Exception as conn_error:
            logger.error(f"❌ Connection Error: {str(conn_error)}")
            return False
        finally:
            # Always close connection to free memory
            if server:
                try:
                    server.quit()
                except:
                    pass
        
    except MemoryError as mem_error:
        logger.error(f"❌ Memory Error: {str(mem_error)}")
        return False
    except Exception as e:
        logger.error(f"❌ General Error sending order confirmation email: {str(e)}")
        return False

def send_telegram_photo(photo_file=None, photo_path=None, filename=None, caption=""):
    """Send photo to Telegram"""
    
    # Get Telegram credentials from environment
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    logger.info(f"=== send_telegram_photo called ===")
    logger.info(f"TELEGRAM_TOKEN exists: {bool(TELEGRAM_TOKEN)}")
    logger.info(f"CHAT_ID exists: {bool(CHAT_ID)}")
    logger.info(f"Filename: {filename}")
    logger.info(f"Caption length: {len(caption)}")
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logger.error("❌ Telegram credentials not configured")
        logger.error(f"TELEGRAM_TOKEN: {TELEGRAM_TOKEN}")
        logger.error(f"CHAT_ID: {CHAT_ID}")
        return False
    
    try:
        # Send photo to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        logger.info(f"Sending photo to URL: {url}")
        
        if photo_file:
            # Send from file object (in memory)
            files = {'photo': (filename, photo_file, 'image/jpeg')}
            logger.info("Using file object (in memory)")
        elif photo_path:
            # Send from file path
            files = {'photo': open(photo_path, 'rb')}
            logger.info(f"Using file path: {photo_path}")
        else:
            logger.error("❌ No photo file or path provided")
            return False
            
        data = {
            'chat_id': CHAT_ID,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        
        logger.info(f"Photo data: chat_id={CHAT_ID}, caption_length={len(caption)}")
        
        response = requests.post(url, files=files, data=data, timeout=10)
        logger.info(f"Photo response status: {response.status_code}")
        logger.info(f"Photo response body: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ Telegram photo sent successfully")
            return True
        else:
            logger.error(f"❌ Failed to send Telegram photo: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending Telegram photo: {str(e)}")
        return False

def send_telegram_document(content, filename, caption=""):
    """Send document to Telegram"""
    
    # Get Telegram credentials from environment
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logger.error("Telegram credentials not configured")
        return False
    
    try:
        # Send document to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        
        from io import BytesIO
        document_bytes = BytesIO(content.encode('utf-8'))
        
        files = {
            'document': (filename, document_bytes, 'text/plain')
        }
        data = {
            'chat_id': CHAT_ID,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, files=files, data=data, timeout=10)
        
        if response.status_code == 200:
            logger.info("Telegram document sent successfully")
            return True
        else:
            logger.error(f"Failed to send Telegram document: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram document: {str(e)}")
        return False

def create_app():
    """Application factory function"""
    
    # Initialize MongoDB
    try:
        mongo = init_mongo(app)
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {str(e)}")
        raise
    
    # Initialize Babel
    babel = Babel(app, locale_selector=get_locale)
    app.jinja_env.globals['get_locale'] = get_locale
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.user_loader(load_user)
    
    # Initialize Rate Limiting
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Initialize CSRF Protection
    csrf = CSRFProtect(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.orders import orders_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    
    # Make limiter available to blueprints
    app.limiter = limiter
    
    # Disable strict slashes for all routes
    app.url_map.strict_slashes = False
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("🚀 NEXAweb application initialized successfully")
    print("📦 Registered blueprints:")
    print("   - Main routes (/)")
    print("   - Auth routes (/login, /logout)")
    print("   - Admin routes (/admin)")
    print("   - Order routes (/order, /status)")
    print("   - Strict slashes disabled for all routes")
    
    return app

# Create the application
app = create_app()

if __name__ == '__main__':
    print("🌟 Starting NEXAweb application...")
    
    # Get port from environment variable for Render deployment
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"🌐 Server will run on port {port}")
    print(f"🔧 Debug mode: {debug_mode}")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
