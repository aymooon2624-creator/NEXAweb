"""
Order routes for NEXAweb application
Handles order submission, tracking, and management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import os
import re
import html
import bleach
import logging
from datetime import datetime
from models import Order, Testimonial, generate_tracking_code
from database import get_mongo
from telegram_notifications import send_new_order_notification

# Configure logger
logger = logging.getLogger(__name__)

orders_bp = Blueprint('orders', __name__)

# File upload configuration
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
ALLOWED_MIME_TYPES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png'
}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = 'static/uploads'

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_upload(file):
    """Comprehensive file upload validation"""
    if not file or file.filename == '':
        return False, "No file selected"
    
    # Check file extension
    if not allowed_file(file.filename):
        return False, "File type not allowed"
    
    # Get file extension
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    
    # Check MIME type
    if hasattr(file, 'mimetype'):
        expected_mime = ALLOWED_MIME_TYPES.get(file_ext)
        if expected_mime and file.mimetype != expected_mime:
            return False, f"Invalid file type. Expected {expected_mime}, got {file.mimetype}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, "File validation passed"

def sanitize_input(text):
    """Strict input sanitization to prevent XSS"""
    if not text:
        return ""
    
    # Use bleach for HTML sanitization
    allowed_tags = []  # No HTML tags allowed
    allowed_attributes = {}
    
    # Clean the input
    clean_text = bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)
    
    # Additional sanitization for special characters
    clean_text = html.escape(clean_text)
    
    # Remove any remaining potentially dangerous patterns
    dangerous_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'expression\s*\(',
        r'@import',
        r'vbscript:',
    ]
    
    for pattern in dangerous_patterns:
        clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE | re.DOTALL)
    
    return clean_text.strip()


@orders_bp.route('/order')
def order_form():
    """Order submission form page"""
    return render_template('order.html')


@orders_bp.route('/submit_order', methods=['POST'])
def submit_order():
    """Handle order submission"""
    try:
        print("=" * 50)
        print("🚀 Starting order submission process...")
        
        # Get and sanitize form data
        name = sanitize_input(request.form.get('name', '').strip())
        email = sanitize_input(request.form.get('email', '').strip())
        phone = sanitize_input(request.form.get('phone', '').strip())
        project_type = sanitize_input(request.form.get('project_type', '').strip())
        details = sanitize_input(request.form.get('details', '').strip())
        
        # Set default price values (admin only controls these)
        total_price = 0.0
        deposit_amount = 0.0
        
        print(f"📝 Form data received: {name}, {email}, {project_type}")
        print(f"💰 Price data: Total=${total_price}, Deposit=${deposit_amount} (admin controlled)")
        
        # Validation
        if not all([name, email, phone, project_type, details, total_price >= 0, deposit_amount >= 0]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('orders.order_form'))
        
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('orders.order_form'))
        
        # Generate unique tracking code
        tracking_code = generate_tracking_code()
        print(f"🔢 Generated tracking code: {tracking_code}")
        
        # Handle optional image upload
        image_file = None
        image_filename = None
        
        if 'image' in request.files:
            image = request.files['image']
            if image and image.filename != '':
                try:
                    # Validate image
                    if not allowed_file(image.filename):
                        flash('Invalid image format. Allowed: JPG, JPEG, PNG, GIF', 'error')
                        return redirect(url_for('orders.order_form'))
                    
                    # Store image in memory for Telegram
                    image_file = image
                    image_filename = f"{tracking_code}.jpg"
                    print(f"🖼️ Image prepared for Telegram: {image_filename}")
                    
                except Exception as e:
                    print(f"❌ Error processing image upload: {e}")
                    flash('Error processing image upload. Please try again.', 'error')
                    return redirect(url_for('orders.order_form'))
        
        # Create order in MongoDB
        order_id = Order.create(
            name=name,
            email=email,
            phone=phone,
            project_type=project_type,
            details=details,
            tracking_code=tracking_code,
            original_filename=tracking_code,  # Set original_filename to tracking_code
            total_price=total_price,
            deposit_amount=deposit_amount
        )
        
        if order_id:
            print(f"✅ Order created successfully with ID: {order_id}")
            
            # Create project details content in memory
            project_details_content = f"""Project Details - Tracking Code: {tracking_code}
{"="*50}

Customer Name: {name}
Email: {email}
Phone: {phone}
Project Type: {project_type}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Project Details:
{"-"*20}
{details}

Pricing:
Total Price: ${total_price}
Deposit Amount: ${deposit_amount}
Remaining Amount: ${total_price - deposit_amount}
"""
            
            print(f"📄 Project details prepared for Telegram: {tracking_code}.txt")
            
            # Store tracking code in session for backup
            session['last_tracking_code'] = tracking_code
            
            # Send Telegram notification with project details as document
            print("📱 Sending Telegram notification with project details...")
            
            try:
                from app import send_telegram_document
                
                # Send project details as document
                doc_success = send_telegram_document(
                    content=project_details_content,
                    filename=f"{tracking_code}.txt",
                    caption=f"📄 Project Details for Order {tracking_code}\n\nCustomer: {name}\nProject: {project_type}"
                )
                
                if doc_success:
                    print("✅ Project details sent successfully")
                else:
                    print("❌ Failed to send project details")
                    
            except Exception as e:
                print(f"❌ Error sending project details: {e}")
            
            # Send image notification if image was uploaded
            if image_file:
                print("🖼️ Sending image notification to Telegram...")
                try:
                    from app import send_telegram_photo
                    photo_success = send_telegram_photo(
                        photo_file=image_file,
                        filename=image_filename,
                        caption=f"📸 Project Image for Order {tracking_code}\n\nCustomer: {name}\nProject: {project_type}"
                    )
                    if photo_success:
                        print("✅ Image notification sent successfully")
                    else:
                        print("❌ Failed to send image notification")
                except Exception as e:
                    print(f"❌ Error sending image notification: {e}")
            
            # Send basic text notification as backup
            print("📱 Sending basic Telegram notification...")
            order_data = {
                'name': name,
                'email': email,
                'phone': phone,
                'project_type': project_type,
                'tracking_code': tracking_code,
                'details': details
            }
            
            try:
                from utils.notifications import notify_new_order
                telegram_success = notify_new_order(order_data)
                if telegram_success:
                    print("✅ Basic Telegram notification sent successfully")
                else:
                    print("❌ Failed to send basic Telegram notification")
            except Exception as e:
                print(f"❌ Error creating basic notification: {e}")
            
            flash('Order submitted successfully! Your tracking code is: ' + tracking_code, 'success')
            return redirect(url_for('orders.success_page', tracking_code=tracking_code))
        else:
            flash('Error submitting order. Please try again.', 'error')
            return redirect(url_for('orders.order_form'))
            
    except Exception as e:
        logger.error(f"Error in submit_order: {type(e).__name__} - {str(e)}")
        print(f"❌ Error in submit_order: {type(e).__name__} - {str(e)}")
        flash('An error occurred while submitting your order. Please try again.', 'error')
        return redirect(url_for('orders.order_form'))


@orders_bp.route('/success')
def success_page():
    """Success page for order submission"""
    tracking_code = request.args.get('tracking_code', '')
    
    # Use session backup if URL parameter is empty
    if not tracking_code and 'last_tracking_code' in session:
        tracking_code = session['last_tracking_code']
    
    return render_template('success.html', tracking_code=tracking_code)


@orders_bp.route('/status')
def status():
    """Order tracking page that accepts tracking code as query parameter"""
    tracking_code = request.args.get('tracking_code', '').strip()
    
    if not tracking_code:
        flash('Please enter a tracking code', 'error')
        return redirect(url_for('main.home'))
    
    return redirect(url_for('orders.order_status', tracking_code=tracking_code))


@orders_bp.route('/track', methods=['GET', 'POST'])
def track_order():
    """Track order by tracking code"""
    if request.method == 'POST':
        tracking_code = request.form.get('tracking_code', '').strip()
        
        if not tracking_code:
            flash('Please enter a tracking code', 'error')
            return redirect(url_for('main.home'))
        
        return redirect(url_for('orders.order_status', tracking_code=tracking_code))
    
    return redirect(url_for('main.home'))


@orders_bp.route('/status/<tracking_code>')
def order_status(tracking_code):
    """Display order status by tracking code"""
    print(f"🔍 Fetching order status for tracking code: {tracking_code}")
    order_data = Order.get_by_tracking_code(tracking_code)
    
    if order_data:
        print(f"📊 Raw order data: {order_data}")
        order = Order(order_data)
        print(f"💰 Order prices - Total: {order.total_price}, Deposit: {order.deposit_amount}, Remaining: {order.remaining_amount}")
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return render_template('status.html', order=order, current_time=current_time)
    else:
        print(f"❌ No order found for tracking code: {tracking_code}")
        flash('Invalid tracking code. Please check and try again.', 'error')
        return redirect(url_for('main.home'))


@orders_bp.route('/update_status/<order_id>', methods=['POST'])
def update_status(order_id):
    """Update order status (admin only)"""
    try:
        new_status = request.form.get('status')
        
        if new_status not in ['new', 'analyzing', 'coding', 'testing', 'completed']:
            flash('Invalid status', 'error')
            return redirect(url_for('admin.admin_dashboard'))
        
        success = Order.update_status(order_id, new_status)
        
        if success:
            # Send email notification if status is changed to 'completed'
            if new_status == 'completed':
                try:
                    # Get order details for email
                    mongo = get_mongo()
                    order_data = mongo.db.orders.find_one({'_id': string_to_object_id(order_id)})
                    
                    if order_data:
                        customer_email = order_data.get('email')
                        customer_name = order_data.get('name')
                        tracking_code = order_data.get('tracking_code')
                        project_type = order_data.get('project_type')
                        
                        if customer_email:
                            from utils.notifications import send_project_completion_email
                            email_sent = send_project_completion_email(
                                customer_email=customer_email,
                                customer_name=customer_name,
                                tracking_code=tracking_code,
                                project_type=project_type
                            )
                            
                            if email_sent:
                                print(f"✅ Project completion email sent to {customer_email}")
                                flash('Order status updated successfully! Customer has been notified via email.', 'success')
                            else:
                                print(f"❌ Failed to send project completion email to {customer_email}")
                                flash('Order status updated successfully! (Email notification failed)', 'warning')
                        else:
                            print(f"❌ No email address found for order {order_id}")
                            flash('Order status updated successfully! (No email address on file)', 'warning')
                    else:
                        print(f"❌ Order not found: {order_id}")
                        flash('Order status updated successfully!', 'success')
                        
                except Exception as e:
                    print(f"❌ Error sending completion email: {e}")
                    flash('Order status updated successfully! (Email notification error)', 'warning')
            else:
                flash('Order status updated successfully!', 'success')
        else:
            flash('Error updating order status', 'error')
        
        return redirect(url_for('admin.admin_dashboard'))
        
    except Exception as e:
        logger.error(f"Error updating order status: {type(e).__name__}")
        flash(f'Error updating order status. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@orders_bp.route('/delete_order/<order_id>', methods=['POST'])
def delete_order(order_id):
    """Delete order (admin only)"""
    try:
        # Get order data before deletion to clean up files
        mongo = get_mongo()
        from models import string_to_object_id
        
        order_data = mongo.db.orders.find_one({'_id': string_to_object_id(order_id)})
        
        if order_data:
            tracking_code = order_data.get('tracking_code')
            print(f"🗑️ Deleting order {order_id} with tracking code: {tracking_code}")
            
            # Delete order attachments folder
            if tracking_code:
                attachments_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'order_attachments', tracking_code)
                if os.path.exists(attachments_dir):
                    try:
                        import shutil
                        shutil.rmtree(attachments_dir)
                        print(f"📁 Deleted attachments folder: {attachments_dir}")
                    except Exception as e:
                        print(f"❌ Error deleting attachments folder: {e}")
                
                # Delete order details file
                details_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'order_data', f"{tracking_code}.txt")
                if os.path.exists(details_file):
                    try:
                        os.remove(details_file)
                        print(f"📄 Deleted details file: {details_file}")
                    except Exception as e:
                        print(f"❌ Error deleting details file: {e}")
        
        # Delete order from database
        success = Order.delete(order_id)
        
        if success:
            flash('Order and all associated files deleted successfully!', 'success')
            print(f"✅ Order {order_id} deleted successfully")
        else:
            flash('Error deleting order from database', 'error')
            print(f"❌ Failed to delete order {order_id}")
        
        return redirect(url_for('admin.admin_dashboard'))
        
    except Exception as e:
        logger.error(f"Error deleting order: {type(e).__name__}")
        flash('Error deleting order. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@orders_bp.route('/update_order_price', methods=['POST'])
def update_order_price():
    """Update order total_price and deposit_amount (AJAX endpoint)"""
    try:
        order_id = request.form.get('order_id')
        total_price = request.form.get('total_price', '0')
        deposit_amount = request.form.get('deposit_amount', '0')
        
        if not order_id:
            return jsonify({'success': False, 'message': 'Order ID is required'}), 400
        
        success = Order.update_prices(order_id, total_price, deposit_amount)
        
        if success:
            return jsonify({'success': True, 'message': 'Prices updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update prices'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': 'Server error'}), 500


@orders_bp.route('/api/capture-payment', methods=['POST'])
def capture_payment():
    """Handle PayPal payment capture and update database"""
    try:
        order_id = request.form.get('order_id')
        payment_type = request.form.get('payment_type')  # 'deposit' or 'full'
        payment_id = request.form.get('payment_id')
        
        print(f"🔍 Capture payment request:")
        print(f"   Order ID: {order_id}")
        print(f"   Payment Type: {payment_type}")
        print(f"   Payment ID: {payment_id}")
        print(f"   Form data: {dict(request.form)}")
        
        if not order_id or not payment_type:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Update payment status
        if payment_type == 'deposit':
            success = Order.update_payment_status(order_id, deposit_paid=True)
        elif payment_type == 'full':
            success = Order.update_payment_status(order_id, full_paid=True)
        else:
            return jsonify({'success': False, 'message': 'Invalid payment type'}), 400
        
        if success:
            return jsonify({'success': True, 'message': 'Payment processed successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update payment status'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': 'Payment processing failed'}), 500


@orders_bp.route('/update_payment', methods=['POST'])
def update_payment():
    """Handle payment updates for deposit and final payments (legacy)"""
    try:
        order_id = request.form.get('order_id')
        payment_type = request.form.get('payment_type')
        
        if not order_id or not payment_type:
            flash('Missing required fields', 'error')
            return redirect(url_for('admin.admin_dashboard'))
        
        # Update payment status
        if payment_type == 'deposit':
            success = Order.update_payment_status(order_id, deposit_paid=True)
        elif payment_type == 'full':
            success = Order.update_payment_status(order_id, full_paid=True)
        else:
            flash('Invalid payment type', 'error')
            return redirect(url_for('admin.admin_dashboard'))
        
        if success:
            flash('Payment status updated successfully!', 'success')
        else:
            flash('Error updating payment status', 'error')
        
        return redirect(url_for('admin.admin_dashboard'))
        
    except Exception as e:
        logger.error(f"Error in update_payment: {type(e).__name__}")
        flash('Error updating payment. Please try again.', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@orders_bp.route('/feedback/<tracking_code>')
def feedback_form(tracking_code):
    """Secure feedback form - only accessible for completed orders"""
    try:
        order_data = Order.get_by_tracking_code(tracking_code)
        
        if not order_data:
            return render_template('access_denied.html'), 404
        
        order = Order(order_data)
        
        # Only allow feedback for completed orders
        if order.status not in ['completed', 'Paid']:
            return render_template('access_denied.html'), 403
        
        return render_template('feedback.html', order=order, tracking_code=tracking_code)
        
    except Exception as e:
        logger.error(f"Error in feedback_form: {type(e).__name__}")
        return render_template('access_denied.html'), 500


@orders_bp.route('/submit_testimonial/<tracking_code>', methods=['POST'])
def submit_testimonial(tracking_code):
    """Submit testimonial with security validations"""
    try:
        order_data = Order.get_by_tracking_code(tracking_code)
        
        if not order_data:
            flash('Invalid order', 'error')
            return redirect(url_for('main.home'))
        
        order = Order(order_data)
        
        # Only allow testimonials for completed orders
        if order.status not in ['completed', 'Paid']:
            flash('Testimonials can only be submitted for completed orders', 'error')
            return redirect(url_for('main.home'))
        
        # Get form data
        customer_name = sanitize_input(request.form.get('customer_name', '').strip())
        content = sanitize_input(request.form.get('content', '').strip())
        rating = int(request.form.get('rating', 1))
        
        # Validation
        if not customer_name or not content:
            flash('Name and testimonial are required', 'error')
            return redirect(url_for('orders.feedback_form', tracking_code=tracking_code))
        
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5', 'error')
            return redirect(url_for('orders.feedback_form', tracking_code=tracking_code))
        
        # Get client IP for rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        
        # Create testimonial
        testimonial_id = Testimonial.create(
            order_id=str(order.id),
            customer_name=customer_name,
            content=content,
            rating=rating,
            ip_address=client_ip
        )
        
        if testimonial_id:
            flash('Testimonial submitted successfully! It will be reviewed before being published.', 'success')
            return redirect(url_for('orders.testimonial_success'))
        else:
            flash('Error submitting testimonial. Please try again.', 'error')
            return redirect(url_for('orders.feedback_form', tracking_code=tracking_code))
        
    except Exception as e:
        logger.error(f"Error in submit_testimonial: {type(e).__name__}")
        flash('An error occurred while submitting your testimonial. Please try again.', 'error')
        return redirect(url_for('orders.feedback_form', tracking_code=tracking_code))


@orders_bp.route('/testimonial/success')
def testimonial_success():
    """Testimonial submission success page"""
    return render_template('testimonial_success.html')


@orders_bp.route('/api/zaincash-payment', methods=['POST'])
def zaincash_payment():
    """Handle Zain Cash payment confirmation"""
    try:
        from flask import request, jsonify
        from werkzeug.utils import secure_filename
        from models import string_to_object_id
        
        # Get form data
        order_id = request.form.get('order_id')
        tracking_code = request.form.get('tracking_code')
        payment_type = request.form.get('payment_type', 'deposit')  # deposit or final
        
        print(f"📱 Zain Cash payment received:")
        print(f"   Order ID: {order_id}")
        print(f"   Tracking Code: {tracking_code}")
        print(f"   Payment Type: {payment_type}")
        
        if not order_id or not tracking_code:
            return jsonify({'success': False, 'message': 'Order ID and tracking code are required'}), 400
        
        # Handle file upload
        receipt_file = None
        receipt_filename = None
        
        if 'receipt' not in request.files:
            return jsonify({'success': False, 'message': 'Payment receipt is required'}), 400
        
        file = request.files['receipt']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Check file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'message': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, PDF'}), 400
        
        # Create payment directory structure
        order_payment_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'order_payment')
        os.makedirs(order_payment_dir, exist_ok=True)
        
        # Save receipt file with tracking code as filename
        receipt_filename = f"{tracking_code}.jpg"
        receipt_filepath = os.path.join(order_payment_dir, receipt_filename)
        
        file.save(receipt_filepath)
        
        # Store relative path in database
        receipt_path = os.path.join('order_payment', receipt_filename).replace('\\', '/')
        
        print(f"📄 Payment receipt saved: {receipt_filepath}")
        print(f"📁 Database path: {receipt_path}")
        
        # Update database
        mongo = get_mongo()
        
        if payment_type == 'deposit':
            # Update deposit payment status
            update_data = {
                'is_deposit_paid': True,
                'deposit_receipt_path': receipt_path,
                'deposit_payment_method': 'zaincash',
                'deposit_paid_at': datetime.utcnow()
            }
        else:
            # Update final payment status
            update_data = {
                'is_full_paid': True,
                'final_receipt_path': receipt_path,
                'final_payment_method': 'zaincash',
                'final_paid_at': datetime.utcnow()
            }
        
        result = mongo.db.orders.update_one(
            {'_id': string_to_object_id(order_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            print(f"✅ Zain Cash payment processed successfully for order {order_id}")
            
            # Send Telegram payment notification
            try:
                order_data = mongo.db.orders.find_one({'_id': string_to_object_id(order_id)})
                if order_data:
                    # Import the notification function from app
                    from app import send_payment_notification
                    
                    # Determine amount based on payment type
                    if payment_type == 'deposit':
                        amount = order_data.get('deposit_amount', 0.0)
                    else:
                        # For final payment, use remaining_balance first, then fallback to calculation
                        remaining_balance = order_data.get('remaining_balance')
                        if remaining_balance is not None:
                            amount = float(remaining_balance)
                        else:
                            # Calculate remaining amount
                            total_price = float(order_data.get('total_price', 0.0))
                            deposit_amount = float(order_data.get('deposit_amount', 0.0))
                            amount = max(0.0, total_price - deposit_amount)
                    
                    # Generate transaction ID
                    transaction_id = f"ZAINCASH_{payment_type.upper()}_{tracking_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    # Send notification
                    notification_success = send_payment_notification(
                        customer_name=order_data.get('name', 'Unknown'),
                        tracking_code=tracking_code,
                        amount=f"{amount:.2f}",
                        payment_type=payment_type,
                        transaction_id=transaction_id
                    )
                    
                    if notification_success:
                        print("✅ Telegram payment notification sent successfully")
                    else:
                        print("❌ Failed to send Telegram payment notification")
            except Exception as e:
                print(f"❌ Error sending Telegram payment notification: {e}")
            
            return jsonify({
                'success': True, 
                'message': 'Payment received successfully! We will verify your payment and update your order status.',
                'receipt_path': receipt_path
            })
        else:
            print(f"❌ Failed to update order {order_id}")
            return jsonify({'success': False, 'message': 'Failed to update order status'}), 500
            
    except Exception as e:
        print(f"❌ Error processing Zain Cash payment: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500


@orders_bp.route('/api/paypal-payment', methods=['POST'])
def paypal_payment():
    """Handle PayPal payment confirmation"""
    try:
        from flask import request, jsonify
        from werkzeug.utils import secure_filename
        from models import string_to_object_id
        
        # Check if this is form data (with file upload) or JSON
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle file upload
            order_id = request.form.get('order_id')
            tracking_code = request.form.get('tracking_code')
            payment_type = request.form.get('payment_type', 'deposit')
            
            # Handle file upload
            receipt_path = None
            if 'receipt' in request.files:
                file = request.files['receipt']
                if file.filename != '':
                    # Check file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
                    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                        return jsonify({'success': False, 'message': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, PDF'}), 400
                    
                    # Create payment directory structure
                    order_payment_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'order_payment')
                    tracking_code_dir = os.path.join(order_payment_dir, tracking_code)
                    os.makedirs(tracking_code_dir, exist_ok=True)
                    
                    # Save receipt file
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    receipt_filename = f"paypal_{payment_type}_{timestamp}_{filename}"
                    
                    receipt_filepath = os.path.join(tracking_code_dir, receipt_filename)
                    file.save(receipt_filepath)
                    
                    # Store relative path in database
                    receipt_path = os.path.join('order_payment', tracking_code, receipt_filename).replace('\\', '/')
                    
                    print(f"📄 PayPal receipt saved: {receipt_filepath}")
        else:
            # Handle JSON data (no file upload)
            data = request.get_json()
            order_id = data.get('order_id')
            tracking_code = data.get('tracking_code')
            payment_type = data.get('payment_type', 'deposit')
            receipt_path = None
        
        print(f"💰 PayPal payment confirmation received:")
        print(f"   Order ID: {order_id}")
        print(f"   Tracking Code: {tracking_code}")
        print(f"   Payment Type: {payment_type}")
        print(f"   Receipt Path: {receipt_path}")
        
        if not order_id or not tracking_code:
            return jsonify({'success': False, 'message': 'Order ID and tracking code are required'}), 400
        
        # Update database
        mongo = get_mongo()
        
        if payment_type == 'deposit':
            # Update deposit payment status
            update_data = {
                'is_deposit_paid': True,
                'deposit_payment_method': 'paypal',
                'deposit_paid_at': datetime.utcnow()
            }
            if receipt_path:
                update_data['deposit_receipt_path'] = receipt_path
        else:
            # Update final payment status
            update_data = {
                'is_full_paid': True,
                'final_payment_method': 'paypal',
                'final_paid_at': datetime.utcnow()
            }
            if receipt_path:
                update_data['final_receipt_path'] = receipt_path
        
        result = mongo.db.orders.update_one(
            {'_id': string_to_object_id(order_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            print(f"✅ PayPal payment processed successfully for order {order_id}")
            
            # Send Telegram payment notification
            try:
                order_data = mongo.db.orders.find_one({'_id': string_to_object_id(order_id)})
                if order_data:
                    # Import the notification function from app
                    from app import send_payment_notification
                    
                    # Determine amount based on payment type
                    if payment_type == 'deposit':
                        amount = order_data.get('deposit_amount', 0.0)
                    else:
                        # For final payment, use remaining_balance first, then fallback to calculation
                        remaining_balance = order_data.get('remaining_balance')
                        if remaining_balance is not None:
                            amount = float(remaining_balance)
                        else:
                            # Calculate remaining amount
                            total_price = float(order_data.get('total_price', 0.0))
                            deposit_amount = float(order_data.get('deposit_amount', 0.0))
                            amount = max(0.0, total_price - deposit_amount)
                    
                    # Generate transaction ID
                    transaction_id = f"PAYPAL_{payment_type.upper()}_{tracking_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    # Send notification
                    notification_success = send_payment_notification(
                        customer_name=order_data.get('name', 'Unknown'),
                        tracking_code=tracking_code,
                        amount=f"{amount:.2f}",
                        payment_type=payment_type,
                        transaction_id=transaction_id
                    )
                    
                    if notification_success:
                        print("✅ Telegram payment notification sent successfully")
                    else:
                        print("❌ Failed to send Telegram payment notification")
            except Exception as e:
                print(f"❌ Error sending Telegram payment notification: {e}")
            
            message = 'Payment confirmed successfully! Your order status has been updated.'
            if receipt_path:
                message += ' Receipt uploaded successfully.'
            
            return jsonify({
                'success': True, 
                'message': message,
                'receipt_path': receipt_path
            })
        else:
            print(f"❌ Failed to update order {order_id}")
            return jsonify({'success': False, 'message': 'Failed to update order status'}), 500
            
    except Exception as e:
        print(f"❌ Error processing PayPal payment: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500
