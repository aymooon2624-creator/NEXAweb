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
app.config['SERVER_NAME'] = 'localhost:5000'
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'http'

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

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

def send_payment_notification(customer_name, tracking_code, amount, payment_type, transaction_id):
    """
    Send payment notification to Telegram with professional HTML formatting
    """
    import requests
    from datetime import datetime
    
    # Telegram configuration - get from environment variables
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Validate required environment variables
    if not TELEGRAM_BOT_TOKEN or not CHAT_ID:
        logger.error("Telegram configuration missing - check environment variables")
        return False
    
    # Determine payment type text in Arabic
    payment_type_text = "الأولى" if payment_type == "deposit" else "الثانية"
    
    # Format current date
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create HTML formatted message
    message = f"""
🔵 <b>إشعار دفع جديد (NEXAweb)</b>

👤 <b>الزبون:</b> {customer_name}
📋 <b>رمز التتبع:</b> {tracking_code}
💰 <b>المبلغ المدفوع:</b> ${amount}
💳 <b>نوع الدفعة:</b> {payment_type_text}
🆔 <b>رقم العملية:</b> {transaction_id}
📅 <b>التاريخ:</b> {current_date}
    """.strip()
    
    # Send message to Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram payment notification sent successfully")
            return True
        else:
            logger.error(f"Failed to send Telegram notification: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")
        return False

def send_telegram_photo(photo_file=None, photo_path=None, filename=None, caption=""):
    """Send photo to Telegram"""
    
    # Get Telegram credentials from environment
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logger.error("Telegram credentials not configured")
        return False
    
    try:
        # Send photo to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        
        if photo_file:
            # Send from file object (in memory)
            files = {'photo': (filename, photo_file, 'image/jpeg')}
        elif photo_path:
            # Send from file path
            files = {'photo': open(photo_path, 'rb')}
        else:
            logger.error("No photo file or path provided")
            return False
            
        data = {
            'chat_id': CHAT_ID,
            'caption': caption,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, files=files, data=data, timeout=10)
        
        if response.status_code == 200:
            logger.info("Telegram photo sent successfully")
            return True
        else:
            logger.error(f"Failed to send Telegram photo: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram photo: {str(e)}")
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
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("🚀 NEXAweb application initialized successfully")
    print("📦 Registered blueprints:")
    print("   - Main routes (/)")
    print("   - Auth routes (/login, /logout)")
    print("   - Admin routes (/admin)")
    print("   - Order routes (/order, /status)")
    
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
