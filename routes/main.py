"""
Main routes for NEXAweb application
Handles homepage, visitor tracking, and general pages
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import secrets
import os
from models import Project, Testimonial
from database import get_mongo

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """Homepage with projects and testimonials"""
    try:
        # Skip visitor tracking for authenticated admin users
        if current_user.is_authenticated and current_user.username == 'admin':
            projects_data = Project.get_all()
            projects = [Project(project_data) for project_data in projects_data]
            
            testimonials_data = Testimonial.get_approved()
            testimonials = [Testimonial(testimonial_data) for testimonial_data in testimonials_data]
            
            return render_template('index.html', projects=projects, testimonials=testimonials)
        
        # Get visible projects for homepage
        projects_data = Project.get_visible()
        projects = [Project(project_data) for project_data in projects_data]
        
        # Get approved testimonials for carousel
        testimonials_data = Testimonial.get_approved()
        testimonials = [Testimonial(testimonial_data) for testimonial_data in testimonials_data]
        
        return render_template('index.html', projects=projects, testimonials=testimonials)
        
    except Exception as e:
        print(f"Error in home route: {e}")
        # Fallback to basic homepage without visitor tracking
        projects_data = Project.get_visible()
        projects = [Project(project_data) for project_data in projects_data[:6]]  # Limit to 6 projects
        
        testimonials_data = Testimonial.get_approved()
        testimonials = [Testimonial(testimonial_data) for testimonial_data in testimonials_data[:3]]  # Limit to 3 testimonials
        
        return render_template('index.html', projects=projects, testimonials=testimonials)


@main_bp.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')


@main_bp.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')




@main_bp.route('/api/project_stats')
def get_project_stats():
    """Get project statistics for admin dashboard"""
    try:
        total_projects = Project.count()
        
        mongo = get_mongo()
        project_stats = mongo.db.projects.aggregate([
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        category_stats = list(project_stats)
        
        return jsonify({
            'total_projects': total_projects,
            'category_stats': category_stats
        })
    except Exception as e:
        print(f"Error getting project stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@main_bp.route('/api/order_stats')
def get_order_stats():
    """Get order statistics for admin dashboard"""
    try:
        total_orders = Order.count()
        completed_orders = Order.count_by_status('completed')
        
        # Get orders by status
        mongo = get_mongo()
        status_stats = mongo.db.orders.aggregate([
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ])
        
        status_data = list(status_stats)
        
        # Payment statistics
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
        
        return jsonify({
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'status_stats': status_data,
            'total_revenue': total_revenue,
            'deposit_revenue': deposit_revenue,
            'pending_deposits': pending_deposits
        })
    except Exception as e:
        print(f"Error getting order stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@main_bp.route('/api/testimonial_stats')
def get_testimonial_stats():
    """Get testimonial statistics for admin dashboard"""
    try:
        total_testimonials = Testimonial.get_all().__len__()
        pending_testimonials = Testimonial.count_by_status('pending')
        approved_testimonials = Testimonial.count_by_status('approved')
        rejected_testimonials = Testimonial.count_by_status('rejected')
        
        return jsonify({
            'total_testimonials': total_testimonials,
            'pending_testimonials': pending_testimonials,
            'approved_testimonials': approved_testimonials,
            'rejected_testimonials': rejected_testimonials
        })
    except Exception as e:
        print(f"Error getting testimonial stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@main_bp.route('/setup_database')
def setup_database():
    """Setup initial database with sample data (development only)"""
    try:
        # Check if admin exists
        admin_count = User.count()
        
        if admin_count == 0:
            # Create admin user
            admin_id = User.create_user('admin', 'admin123')
            if admin_id:
                print("👤 Admin user created: admin/admin123")
            else:
                print("❌ Failed to create admin user")
        else:
            print("👤 Admin user already exists")
        
        # Create sample projects if none exist
        project_count = Project.count()
        
        if project_count == 0:
            print("📁 Creating sample projects...")
            sample_projects = [
                {
                    'title': 'E-Commerce Platform',
                    'description': 'A full-featured e-commerce platform with payment integration, inventory management, and analytics dashboard.',
                    'image_url': 'https://via.placeholder.com/400x300/4F46E5/FFFFFF?text=E-Commerce',
                    'technologies': 'React, Node.js, MongoDB, Stripe',
                    'category': 'web',
                    'featured': True
                },
                {
                    'title': 'Mobile Banking App',
                    'description': 'Secure mobile banking application with biometric authentication, real-time transactions, and budget tracking.',
                    'image_url': 'https://via.placeholder.com/400x300/10B981/FFFFFF?text=Banking+App',
                    'technologies': 'React Native, Firebase, Node.js',
                    'category': 'mobile',
                    'featured': True
                },
                {
                    'title': 'AI Content Generator',
                    'description': 'Machine learning powered content generation platform with natural language processing capabilities.',
                    'image_url': 'https://via.placeholder.com/400x300/F59E0B/FFFFFF?text=AI+Generator',
                    'technologies': 'Python, TensorFlow, React, FastAPI',
                    'category': 'ai',
                    'featured': False
                }
            ]
            
            for project in sample_projects:
                Project.create(
                    title=project['title'],
                    description=project['description'],
                    image_url=project['image_url'],
                    technologies=project['technologies'],
                    category=project['category'],
                    featured=project['featured']
                )
            
            print(f"📁 Created {len(sample_projects)} sample projects")
        else:
            print(f"📁 Found {project_count} existing projects")
        
        flash('Database setup completed successfully!', 'success')
        return redirect(url_for('main.home'))
        
    except Exception as e:
        print(f"❌ Error during database setup: {e}")
        flash(f'Error during database setup: {str(e)}', 'error')
        return redirect(url_for('main.home'))


@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        mongo = get_mongo()
        mongo.db.command('ping')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'disconnected',
            'error': str(e)
        }), 500
