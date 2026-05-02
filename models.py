"""
MongoDB model classes for NEXAweb application
This module contains all the data models that interact with MongoDB collections
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from database import get_mongo, string_to_object_id
import secrets
import string


class User(UserMixin):
    """MongoDB-based User model for authentication"""
    
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.password_hash = user_data['password_hash']
    
    @staticmethod
    def find_by_username(username):
        """Find user by username in MongoDB"""
        mongo = get_mongo()
        return mongo.db.users.find_one({'username': username})
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID in MongoDB"""
        try:
            mongo = get_mongo()
            return mongo.db.users.find_one({'_id': string_to_object_id(user_id)})
        except:
            return None
    
    @staticmethod
    def create_user(username, password):
        """Create new user in MongoDB"""
        mongo = get_mongo()
        password_hash = generate_password_hash(password)
        user_data = {
            'username': username,
            'password_hash': password_hash,
            'created_at': datetime.utcnow()
        }
        result = mongo.db.users.insert_one(user_data)
        return result.inserted_id
    
    def set_password(self, password):
        """Update user password"""
        self.password_hash = generate_password_hash(password)
        mongo = get_mongo()
        mongo.db.users.update_one(
            {'_id': string_to_object_id(self.id)},
            {'$set': {'password_hash': self.password_hash}}
        )
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def count():
        """Count total users"""
        mongo = get_mongo()
        return mongo.db.users.count_documents({})


class Project:
    """MongoDB-based Project model for portfolio management"""
    
    def __init__(self, project_data):
        self.id = str(project_data['_id'])
        self.title = project_data['title']
        self.description = project_data['description']
        self.image_url = project_data.get('image_url', '')
        self.technologies = project_data['technologies']
        self.category = project_data['category']
        self.featured = project_data.get('featured', False)
        self.is_visible = project_data.get('is_visible', True)
        self.created_at = project_data.get('created_at', datetime.utcnow())
    
    @staticmethod
    def get_all():
        """Get all projects from MongoDB"""
        mongo = get_mongo()
        return list(mongo.db.projects.find().sort('created_at', -1))
    
    @staticmethod
    def get_featured():
        """Get featured projects from MongoDB"""
        mongo = get_mongo()
        return list(mongo.db.projects.find({'featured': True}))
    
    @staticmethod
    def get_visible():
        """Get visible projects from MongoDB"""
        mongo = get_mongo()
        return list(mongo.db.projects.find({'is_visible': True}).sort('created_at', -1))
    
    @staticmethod
    def get_by_id(project_id):
        """Get project by ID from MongoDB"""
        try:
            mongo = get_mongo()
            return mongo.db.projects.find_one({'_id': string_to_object_id(project_id)})
        except:
            return None
    
    @staticmethod
    def create(title, description, image_url, technologies, category, featured=False):
        """Create new project in MongoDB"""
        mongo = get_mongo()
        project_data = {
            'title': title,
            'description': description,
            'image_url': image_url,
            'technologies': technologies,
            'category': category,
            'featured': featured,
            'is_visible': True,
            'created_at': datetime.utcnow()
        }
        result = mongo.db.projects.insert_one(project_data)
        return result.inserted_id
    
    @staticmethod
    def update(project_id, update_data):
        """Update project in MongoDB"""
        try:
            mongo = get_mongo()
            mongo.db.projects.update_one(
                {'_id': string_to_object_id(project_id)},
                {'$set': update_data}
            )
            return True
        except:
            return False
    
    @staticmethod
    def delete(project_id):
        """Delete project from MongoDB"""
        try:
            mongo = get_mongo()
            mongo.db.projects.delete_one({'_id': string_to_object_id(project_id)})
            return True
        except:
            return False
    
    @staticmethod
    def count():
        """Count total projects"""
        mongo = get_mongo()
        return mongo.db.projects.count_documents({})
    
    def __repr__(self):
        return f'<Project {self.title}>'


class SecurityLog:
    """MongoDB-based SecurityLog model for login tracking"""
    
    def __init__(self, log_data):
        self.id = str(log_data['_id'])
        self.username = log_data['username']
        self.ip_address = log_data['ip_address']
        self.user_agent = log_data['user_agent']
        self.success = log_data.get('success', False)
        self.timestamp = log_data.get('timestamp', datetime.utcnow())
    
    @staticmethod
    def create(username, ip_address, user_agent, success=False):
        """Create new security log entry in MongoDB"""
        try:
            mongo = get_mongo()
            log_data = {
                'username': username,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'success': success,
                'timestamp': datetime.utcnow()
            }
            result = mongo.db.security_logs.insert_one(log_data)
            return result.inserted_id
        except Exception as e:
            # Log error securely without exposing sensitive data
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Security log creation failed for user: {username[:3]}...")
            return None
    
    @staticmethod
    def get_all(limit=100):
        """Get all security logs from MongoDB"""
        mongo = get_mongo()
        return list(mongo.db.security_logs.find().sort('timestamp', -1).limit(limit))
    
    @staticmethod
    def delete_all():
        """Delete all security logs from MongoDB"""
        try:
            mongo = get_mongo()
            result = mongo.db.security_logs.delete_many({})
            return result.deleted_count
        except:
            return 0
    
    @staticmethod
    def delete_by_id(log_id):
        """Delete specific security log by ID"""
        try:
            mongo = get_mongo()
            mongo.db.security_logs.delete_one({'_id': string_to_object_id(log_id)})
            return True
        except:
            return False
    
    def __repr__(self):
        return f'<SecurityLog {self.username} - {self.success}>'


class Order:
    """MongoDB-based Order model for order management"""
    
    def __init__(self, order_data):
        # Store original data for remaining_amount access
        self._data = order_data
        
        self.id = str(order_data['_id'])
        self.name = order_data['name']
        self.email = order_data['email']
        self.phone = order_data['phone']
        self.project_type = order_data['project_type']
        self.details = order_data.get('details', '')
        self.tracking_code = order_data['tracking_code']
        self.status = order_data.get('status', 'new')
        self.file_path = order_data.get('file_path')
        self.original_filename = order_data.get('original_filename')
        self.created_at = order_data.get('created_at', datetime.utcnow())
        
        # Payment fields
        self.total_price = order_data.get('total_price', 0.0)
        self.deposit_amount = order_data.get('deposit_amount', 0.0)
        self.is_deposit_paid = order_data.get('is_deposit_paid', False)
        self.is_full_paid = order_data.get('is_full_paid', False)
    
    @staticmethod
    def create(name, email, phone, project_type, details, tracking_code, file_path=None, original_filename=None, total_price=0.0, deposit_amount=0.0):
        """Create new order in MongoDB"""
        mongo = get_mongo()
        order_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'project_type': project_type,
            'tracking_code': tracking_code,
            'status': 'new',
            'file_path': file_path,
            'original_filename': original_filename,
            'created_at': datetime.utcnow(),
            'total_price': float(total_price),
            'deposit_amount': float(deposit_amount),
            'is_deposit_paid': False,
            'is_full_paid': False
        }
        result = mongo.db.orders.insert_one(order_data)
        return result.inserted_id
    
    @staticmethod
    def get_by_tracking_code(tracking_code):
        """Get order by tracking code from MongoDB"""
        mongo = get_mongo()
        return mongo.db.orders.find_one({'tracking_code': tracking_code.upper()})
    
    @staticmethod
    def get_by_id(order_id):
        """Get order by ID from MongoDB"""
        try:
            mongo = get_mongo()
            return mongo.db.orders.find_one({'_id': string_to_object_id(order_id)})
        except:
            return None
    
    @staticmethod
    def get_all():
        """Get all orders from MongoDB"""
        mongo = get_mongo()
        return list(mongo.db.orders.find().sort('created_at', -1))
    
    @staticmethod
    def update_status(order_id, new_status):
        """Update order status in MongoDB"""
        try:
            mongo = get_mongo()
            mongo.db.orders.update_one(
                {'_id': string_to_object_id(order_id)},
                {'$set': {'status': new_status}}
            )
            return True
        except:
            return False
    
    @staticmethod
    def update_prices(order_id, total_price, deposit_amount):
        """Update order prices in MongoDB"""
        try:
            mongo = get_mongo()
            total = float(total_price or 0.0)
            deposit = float(deposit_amount or 0.0)
            
            if total < 0 or deposit < 0:
                return False
            
            if deposit > total:
                deposit = total
            
            mongo.db.orders.update_one(
                {'_id': string_to_object_id(order_id)},
                {'$set': {
                    'total_price': total,
                    'deposit_amount': deposit
                }}
            )
            return True
        except:
            return False
    
    @staticmethod
    def update_payment_status(order_id, deposit_paid=None, full_paid=None):
        """Update payment status in MongoDB"""
        try:
            mongo = get_mongo()
            update_data = {}
            if deposit_paid is not None:
                update_data['is_deposit_paid'] = deposit_paid
            if full_paid is not None:
                update_data['is_full_paid'] = full_paid
            
            if update_data:
                mongo.db.orders.update_one(
                    {'_id': string_to_object_id(order_id)},
                    {'$set': update_data}
                )
            return True
        except:
            return False
    
    @staticmethod
    def delete(order_id):
        """Delete order from MongoDB"""
        try:
            mongo = get_mongo()
            mongo.db.orders.delete_one({'_id': string_to_object_id(order_id)})
            return True
        except:
            return False
    
    @staticmethod
    def count():
        """Count total orders"""
        mongo = get_mongo()
        return mongo.db.orders.count_documents({})
    
    @staticmethod
    def count_by_status(status):
        """Count orders by status"""
        mongo = get_mongo()
        return mongo.db.orders.count_documents({'status': status})
    
    @property
    def remaining_amount(self):
        """Get remaining balance from MongoDB or calculate if not stored"""
        # Try to get from stored data first
        if hasattr(self, '_data') and 'remaining_balance' in self._data:
            stored_remaining = float(self._data.get('remaining_balance', 0.0))
            return stored_remaining
        
        # Fall back to calculation
        total = float(self.total_price or 0.0)
        deposit = float(self.deposit_amount or 0.0)
        calculated_remaining = max(0.0, total - deposit)
        return calculated_remaining
    
    @property
    def needs_deposit_payment(self):
        """Check if deposit payment is needed"""
        total_price = float(self.total_price or 0.0)
        deposit_amount = float(self.deposit_amount or 0.0)
        return not self.is_deposit_paid and total_price > 0 and deposit_amount > 0
    
    @property
    def needs_final_payment(self):
        """Check if final payment is needed"""
        total_price = float(self.total_price or 0.0)
        remaining_amount = float(self.remaining_amount or 0.0)
        return (self.is_deposit_paid and 
                not self.is_full_paid and 
                self.status == 'completed' and 
                total_price > 0 and 
                remaining_amount > 0)
    
    def __repr__(self):
        return f'<Order {self.name} - {self.project_type}>'


class Testimonial:
    """MongoDB-based Testimonial model for customer feedback"""
    
    def __init__(self, testimonial_data):
        self.id = str(testimonial_data['_id'])
        self.order_id = testimonial_data['order_id']
        self.customer_name = testimonial_data['customer_name']
        self.content = testimonial_data['content']
        self.rating = testimonial_data['rating']
        self.status = testimonial_data.get('status', 'pending')
        self.created_at = testimonial_data.get('created_at', datetime.utcnow())
        self.ip_address = testimonial_data.get('ip_address')
        self._order_data = None
    
    @property
    def order(self):
        """Get the associated Order object"""
        if self._order_data is None and self.order_id:
            from models import Order
            self._order_data = Order.get_by_id(self.order_id)
        return self._order_data
    
    @staticmethod
    def create(order_id, customer_name, content, rating, ip_address=None):
        """Create new testimonial in MongoDB"""
        mongo = get_mongo()
        testimonial_data = {
            'order_id': order_id,
            'customer_name': customer_name,
            'content': content,
            'rating': rating,
            'status': 'pending',
            'created_at': datetime.utcnow(),
            'ip_address': ip_address
        }
        result = mongo.db.testimonials.insert_one(testimonial_data)
        return result.inserted_id
    
    @staticmethod
    def get_all():
        """Get all testimonials from MongoDB"""
        mongo = get_mongo()
        return list(mongo.db.testimonials.find().sort('created_at', -1))
    
    @staticmethod
    def get_by_id(testimonial_id):
        """Get testimonial by ID from MongoDB"""
        try:
            mongo = get_mongo()
            return mongo.db.testimonials.find_one({'_id': string_to_object_id(testimonial_id)})
        except:
            return None
    
    @staticmethod
    def get_by_order_id(order_id):
        """Get testimonials by order ID from MongoDB"""
        mongo = get_mongo()
        return list(mongo.db.testimonials.find({'order_id': order_id}))
    
    @staticmethod
    def get_pending():
        """Get pending testimonials from MongoDB"""
        mongo = get_mongo()
        return list(mongo.db.testimonials.find({'status': 'pending'}).sort('created_at', -1))
    
    @staticmethod
    def get_approved():
        """Get approved testimonials from MongoDB"""
        mongo = get_mongo()
        return list(mongo.db.testimonials.find({'status': 'approved'}).sort('created_at', -1))
    
    @staticmethod
    def update_status(testimonial_id, new_status):
        """Update testimonial status in MongoDB"""
        try:
            mongo = get_mongo()
            mongo.db.testimonials.update_one(
                {'_id': string_to_object_id(testimonial_id)},
                {'$set': {'status': new_status}}
            )
            return True
        except:
            return False
    
    @staticmethod
    def delete(testimonial_id):
        """Delete testimonial from MongoDB"""
        try:
            mongo = get_mongo()
            mongo.db.testimonials.delete_one({'_id': string_to_object_id(testimonial_id)})
            return True
        except:
            return False
    
    @staticmethod
    def count_by_status(status):
        """Count testimonials by status"""
        mongo = get_mongo()
        return mongo.db.testimonials.count_documents({'status': status})
    
    def __repr__(self):
        return f'<Testimonial {self.customer_name} - {self.rating} stars>'




# Helper function to generate tracking codes
def generate_tracking_code():
    """Generate a unique 8-character tracking code"""
    characters = string.ascii_uppercase + string.digits
    mongo = get_mongo()
    
    while True:
        code = ''.join(secrets.choice(characters) for _ in range(8))
        # Check if code already exists in MongoDB
        if not mongo.db.orders.find_one({'tracking_code': code}):
            return code
