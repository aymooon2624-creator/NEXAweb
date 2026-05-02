"""
Admin routes for NEXAweb application
Handles admin dashboard, project management, and security logs
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Project, Order, SecurityLog, Testimonial
from database import get_mongo

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
def admin_dashboard():
    """Main admin dashboard with statistics"""
    try:
        # Get search and filter parameters
        from flask import request
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        
        # Get statistics
        total_orders = Order.count()
        completed_orders = Order.count_by_status('completed')
        
        # Project type statistics
        mongo = get_mongo()
        project_type_counts = {
            'web': mongo.db.orders.count_documents({'project_type': 'web'}),
            'mobile': mongo.db.orders.count_documents({'project_type': 'mobile'}),
            'other': mongo.db.orders.count_documents({'project_type': 'other'})
        }
        
        # Failed login attempts
        failed_logins = mongo.db.security_logs.count_documents({'success': False})
        
        # Build query for recent orders
        query = {}
        if search:
            query['$or'] = [
                {'name': {'$regex': search, '$options': 'i'}},
                {'email': {'$regex': search, '$options': 'i'}}
            ]
        if status_filter:
            query['status'] = status_filter
        
        # Get ALL orders without filtering for the table
        all_orders_data = list(mongo.db.orders.find().sort('created_at', -1))
        all_orders = [Order(order_data) for order_data in all_orders_data]
        
        # Also get recent orders for statistics (limited to 10)
        recent_orders_data = all_orders_data[:10]
        recent_orders = [Order(order_data) for order_data in recent_orders_data]
        
        # Get pending testimonials
        pending_testimonials_data = Testimonial.get_pending()[:5]
        pending_testimonials = [Testimonial(testimonial_data) for testimonial_data in pending_testimonials_data]
        
        # Payment statistics
        mongo = get_mongo()
        total_revenue = 0.0
        deposit_revenue = 0.0
        
        # Calculate revenue from paid orders
        paid_orders = list(mongo.db.orders.find({'is_full_paid': True}))
        for order_data in paid_orders:
            total_revenue += float(order_data.get('total_price', 0.0))
        
        # Calculate deposit revenue
        deposit_orders = list(mongo.db.orders.find({'is_deposit_paid': True}))
        for order_data in deposit_orders:
            deposit_revenue += float(order_data.get('deposit_amount', 0.0))
        
        pending_deposits = mongo.db.orders.count_documents({
            'is_deposit_paid': False,
            'deposit_amount': {'$gt': 0}
        })
        
        return render_template('admin.html',
                             total_orders=total_orders,
                             completed_orders=completed_orders,
                             project_type_counts=project_type_counts,
                             failed_logins=failed_logins,
                             all_orders=all_orders,
                             recent_orders=recent_orders,
                             pending_testimonials=pending_testimonials,
                             total_revenue=total_revenue,
                             deposit_revenue=deposit_revenue,
                             pending_deposits=pending_deposits,
                             search=search,
                             status_filter=status_filter)
        
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('admin.html',
                             total_orders=0,
                             completed_orders=0,
                             project_type_counts={'web': 0, 'mobile': 0, 'other': 0},
                             failed_logins=0,
                             all_orders=[],
                             recent_orders=[],
                             pending_testimonials=[],
                             total_revenue=0.0,
                             deposit_revenue=0.0,
                             pending_deposits=0,
                             search='',
                             status_filter='')


@admin_bp.route('/projects')
@login_required
def manage_projects():
    """Project management page"""
    try:
        print("🔍 Loading manage_projects page...")
        projects_data = Project.get_all()
        print(f"📊 Found {len(projects_data)} projects")
        projects = [Project(project_data) for project_data in projects_data]
        print(f"🏗️ Created {len(projects)} Project objects")
        print("📄 Rendering project_manager.html template...")
        return render_template('project_manager.html', projects=projects)
    except Exception as e:
        print(f"❌ Error in manage_projects: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        flash(f'Error loading projects: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/manage-projects')
@login_required
def manage_projects_page():
    """Manage projects page - alternative route"""
    try:
        print("🔍 Loading manage-projects page...")
        projects_data = Project.get_all()
        print(f"📊 Found {len(projects_data)} projects")
        projects = [Project(project_data) for project_data in projects_data]
        print(f"🏗️ Created {len(projects)} Project objects")
        print("📄 Rendering project_manager.html template...")
        return render_template('project_manager.html', projects=projects)
    except Exception as e:
        print(f"❌ Error in manage_projects_page: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        flash(f'Error loading projects: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/projects/add', methods=['POST'])
@login_required
def add_project():
    """Add new project"""
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        technologies = request.form.get('technologies', '').strip()
        category = request.form.get('category', '').strip()
        featured = request.form.get('featured') == 'on'
        
        # Validation
        if not title or not description or not technologies or not category:
            flash('Title, description, technologies, and category are required', 'error')
            return redirect(url_for('admin.manage_projects'))
        
        # Create project
        project_id = Project.create(
            title=title,
            description=description,
            image_url=image_url,
            technologies=technologies,
            category=category,
            featured=featured
        )
        
        if project_id:
            flash('Project added successfully!', 'success')
        else:
            flash('Error adding project', 'error')
        
        return redirect(url_for('admin.manage_projects'))
        
    except Exception as e:
        flash(f'Error adding project: {str(e)}', 'error')
        return redirect(url_for('admin.manage_projects'))


@admin_bp.route('/projects/edit/<project_id>', methods=['POST'])
@login_required
def edit_project(project_id):
    """Edit existing project"""
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        technologies = request.form.get('technologies', '').strip()
        category = request.form.get('category', '').strip()
        featured = request.form.get('featured') == 'on'
        
        # Validation
        if not title or not description or not technologies or not category:
            flash('Title, description, technologies, and category are required', 'error')
            return redirect(url_for('admin.manage_projects'))
        
        # Update project
        update_data = {
            'title': title,
            'description': description,
            'image_url': image_url,
            'technologies': technologies,
            'category': category,
            'featured': featured
        }
        
        success = Project.update(project_id, update_data)
        
        if success:
            flash('Project updated successfully!', 'success')
        else:
            flash('Error updating project', 'error')
        
        return redirect(url_for('admin.manage_projects'))
        
    except Exception as e:
        flash(f'Error updating project: {str(e)}', 'error')
        return redirect(url_for('admin.manage_projects'))


@admin_bp.route('/projects/toggle-visibility/<project_id>', methods=['POST'])
@login_required
def toggle_project_visibility(project_id):
    """Toggle project visibility"""
    try:
        # Get current visibility from request
        data = request.get_json() if request.is_json else {}
        new_visibility = data.get('is_visible', True)
        
        # Update project visibility
        update_data = {'is_visible': new_visibility}
        success = Project.update(project_id, update_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Project visibility updated to {"visible" if new_visibility else "hidden"}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update project visibility'
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating visibility: {str(e)}'
        }), 500


@admin_bp.route('/projects/delete/<project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    """Delete project"""
    try:
        success = Project.delete(project_id)
        
        if success:
            flash('Project deleted successfully!', 'success')
        else:
            flash('Error deleting project', 'error')
        
        return redirect(url_for('admin.manage_projects'))
        
    except Exception as e:
        flash(f'Error deleting project: {str(e)}', 'error')
        return redirect(url_for('admin.manage_projects'))


@admin_bp.route('/logs')
@login_required
def view_logs():
    """Security logs page"""
    try:
        print("🔍 Fetching security logs using direct MongoDB query...")
        
        # Direct MongoDB query
        mongo = get_mongo()
        logs_data = list(mongo.db.security_logs.find().sort('timestamp', -1))
        
        print(f"📊 Direct MongoDB query returned {len(logs_data)} logs")
        
        if logs_data:
            print(f"📝 Sample log from MongoDB: {logs_data[0]}")
        else:
            print("⚠️ No logs found in security_logs collection")
        
        return render_template('security_logs.html', logs=logs_data)
    except Exception as e:
        print(f"🚨 Error fetching security logs: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        flash(f'Error fetching security logs: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))








@admin_bp.route('/security-logs')
@login_required
def security_logs():
    """Security logs route as requested by user"""
    try:
        print("🔍 Fetching security logs from /security-logs route...")
        
        # Direct MongoDB check first
        mongo = get_mongo()
        collection_names = mongo.db.list_collection_names()
        print(f"🗄️ Available collections: {collection_names}")
        
        if 'security_logs' in collection_names:
            direct_count = mongo.db.security_logs.count_documents({})
            print(f"📊 Direct MongoDB count: {direct_count}")
            
            if direct_count > 0:
                sample_log = mongo.db.security_logs.find_one()
                print(f"📝 Sample raw log: {sample_log}")
            else:
                print("⚠️ Security logs collection is empty")
        else:
            print("❌ Security logs collection not found")
        
        # Use SecurityLog model
        logs_data = SecurityLog.get_all(limit=100)
        print(f"📊 Raw logs data count: {len(logs_data)}")
        
        logs = [SecurityLog(log_data) for log_data in logs_data]
        print(f"📋 Processed logs count: {len(logs)}")
        
        if logs:
            print(f"📝 Sample log: {logs[0].username} at {logs[0].timestamp}")
        else:
            print("⚠️ No logs found in database")
        
        return render_template('security_logs.html', logs=logs)
    except Exception as e:
        print(f"🚨 Error fetching security logs: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        flash(f'Error fetching security logs: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/delete-logs', methods=['POST'])
@login_required
def delete_logs():
    """Delete security logs - either all logs or individual log"""
    try:
        action = request.form.get('action')
        log_id = request.form.get('log_id')
        
        if action == 'delete_all':
            # Delete all logs (admin only)
            deleted_count = SecurityLog.delete_all()
            flash(f'All {deleted_count} security logs deleted successfully', 'success')
        
        elif action == 'delete_one' and log_id:
            # Delete individual log
            success = SecurityLog.delete_by_id(log_id)
            if success:
                flash('Security log deleted successfully', 'success')
            else:
                flash('Error deleting security log', 'error')
        
        return redirect(url_for('admin.view_logs'))
        
    except Exception as e:
        flash(f'Error deleting logs: {str(e)}', 'error')
        return redirect(url_for('admin.view_logs'))


@admin_bp.route('/testimonials')
@login_required
def manage_testimonials():
    """Admin testimonial management"""
    try:
        # Get all testimonials
        testimonials_data = Testimonial.get_all()
        testimonials = [Testimonial(testimonial_data) for testimonial_data in testimonials_data]
        
        # Calculate statistics from MongoDB
        mongo = get_mongo()
        
        total_count = mongo.db.testimonials.count_documents({})
        pending_count = mongo.db.testimonials.count_documents({'status': 'pending'})
        approved_count = mongo.db.testimonials.count_documents({'status': 'approved'})
        rejected_count = mongo.db.testimonials.count_documents({'status': 'rejected'})
        
        print(f"📊 Testimonials Statistics:")
        print(f"   Total: {total_count}")
        print(f"   Pending: {pending_count}")
        print(f"   Approved: {approved_count}")
        print(f"   Rejected: {rejected_count}")
        
        return render_template('manage_testimonials.html', 
                             testimonials=testimonials,
                             total_count=total_count,
                             pending_count=pending_count,
                             approved_count=approved_count,
                             rejected_count=rejected_count)
    except Exception as e:
        flash(f'Error loading testimonials: {str(e)}', 'error')
        return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/testimonial/<testimonial_id>/approve', methods=['POST'])
@login_required
def approve_testimonial(testimonial_id):
    """Approve a testimonial"""
    try:
        success = Testimonial.update_status(testimonial_id, 'approved')
        
        if success:
            flash('Testimonial approved successfully!', 'success')
        else:
            flash('Error approving testimonial', 'error')
        
        return redirect(url_for('admin.manage_testimonials'))
        
    except Exception as e:
        flash(f'Error approving testimonial: {str(e)}', 'error')
        return redirect(url_for('admin.manage_testimonials'))


@admin_bp.route('/testimonial/<testimonial_id>/reject', methods=['POST'])
@login_required
def reject_testimonial(testimonial_id):
    """Reject a testimonial"""
    try:
        success = Testimonial.update_status(testimonial_id, 'rejected')
        
        if success:
            flash('Testimonial rejected successfully!', 'success')
        else:
            flash('Error rejecting testimonial', 'error')
        
        return redirect(url_for('admin.manage_testimonials'))
        
    except Exception as e:
        flash(f'Error rejecting testimonial: {str(e)}', 'error')
        return redirect(url_for('admin.manage_testimonials'))


@admin_bp.route('/testimonial/<testimonial_id>/delete', methods=['POST'])
@login_required
def delete_testimonial(testimonial_id):
    """Delete a testimonial"""
    try:
        success = Testimonial.delete(testimonial_id)
        
        if success:
            flash('Testimonial deleted successfully!', 'success')
        else:
            flash('Error deleting testimonial', 'error')
        
        return redirect(url_for('admin.manage_testimonials'))
        
    except Exception as e:
        flash(f'Error deleting testimonial: {str(e)}', 'error')
        return redirect(url_for('admin.manage_testimonials'))


@admin_bp.route('/update_order_amounts', methods=['POST'])
@login_required
def update_order_amounts():
    """Update order total_price, deposit_amount, and remaining_balance"""
    try:
        from flask import request, jsonify
        
        # Get form data
        order_id = request.form.get('order_id')
        total_price = request.form.get('total_price', '0')
        deposit_amount = request.form.get('deposit_amount', '0')
        
        if not order_id:
            return jsonify({'success': False, 'message': 'Order ID is required'}), 400
        
        # Convert to float with safety checks
        try:
            total = float(total_price)
            deposit = float(deposit_amount)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid price values'}), 400
        
        # Validate values
        if total < 0 or deposit < 0:
            return jsonify({'success': False, 'message': 'Prices cannot be negative'}), 400
        
        if deposit > total:
            return jsonify({'success': False, 'message': 'Deposit cannot exceed total price'}), 400
        
        # Calculate remaining amount
        remaining = total - deposit
        
        # Update MongoDB
        mongo = get_mongo()
        from models import string_to_object_id
        
        result = mongo.db.orders.update_one(
            {'_id': string_to_object_id(order_id)},
            {'$set': {
                'total_price': total,
                'deposit_amount': deposit,
                'remaining_balance': remaining
            }}
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Order amounts updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Order not found or no changes made'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500


@admin_bp.route('/auto_update_order_amounts', methods=['POST'])
@admin_bp.route('/update_order_amounts', methods=['POST'])
@login_required
def auto_update_order_amounts():
    """Auto-update order amounts immediately without page refresh"""
    try:
        from flask import request, jsonify
        from flask_wtf.csrf import validate_csrf
        import logging
        
        logging.info(f"=== auto_update_order_amounts called ===")
        logging.info(f"Request method: {request.method}")
        logging.info(f"Content-Type: {request.content_type}")
        logging.info(f"Is JSON: {request.is_json}")
        
        # Get JSON data
        if not request.is_json:
            logging.error("Request is not JSON")
            return jsonify({'success': False, 'message': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            logging.error("No JSON data provided")
            return jsonify({'success': False, 'message': 'No JSON data provided'}), 400
        
        logging.info(f"Received data: {data}")
        
        # Validate CSRF token
        try:
            validate_csrf(data.get('csrf_token'))
            logging.info("CSRF token validated successfully")
        except Exception as e:
            logging.error(f"CSRF token validation failed: {str(e)}")
            return jsonify({'success': False, 'message': 'Invalid CSRF token'}), 400
        
        # Get JSON data
        order_id = data.get('order_id')
        total_price = data.get('total_price', '0')
        deposit_amount = data.get('deposit_amount', '0')
        
        logging.info(f"Order ID: {order_id}, Total: {total_price}, Deposit: {deposit_amount}")
        
        if not order_id:
            return jsonify({'success': False, 'message': 'Order ID is required'}), 400
        
        # Convert to float with safety checks
        try:
            total = float(total_price)
            deposit = float(deposit_amount)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid price values'}), 400
        
        # Validate values
        if total < 0 or deposit < 0:
            return jsonify({'success': False, 'message': 'Prices cannot be negative'}), 400
        
        if deposit > total:
            return jsonify({'success': False, 'message': 'Deposit cannot exceed total price'}), 400
        
        # Calculate remaining amount
        remaining = total - deposit
        
        # Update MongoDB
        mongo = get_mongo()
        from models import string_to_object_id
        
        # First check if order exists
        order_data = mongo.db.orders.find_one({'_id': string_to_object_id(order_id)})
        if not order_data:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        update_data = {
            'total_price': total,
            'deposit_amount': deposit,
            'remaining_balance': remaining
        }
        
        result = mongo.db.orders.update_one(
            {'_id': string_to_object_id(order_id)},
            {'$set': update_data}
        )
        
        if result.modified_count > 0:
            logging.info(f"Order {order_id} updated successfully")
            return jsonify({
                'success': True, 
                'message': 'Order amounts updated successfully',
                'remaining_balance': remaining
            })
        else:
            logging.warning(f"Order {order_id} not found or no changes made")
            return jsonify({'success': False, 'message': 'Order not found or no changes made'}), 404
            
    except Exception as e:
        import logging
        logging.error(f"Error in auto_update_order_amounts: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500
