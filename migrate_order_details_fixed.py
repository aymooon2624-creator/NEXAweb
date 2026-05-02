#!/usr/bin/env python3
"""
Migration script to save existing order details to text files
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Flask app to get database context
from app import app
from database import init_mongo

def migrate_existing_orders():
    """Migrate existing orders to save details to text files"""
    try:
        print("🚀 Starting migration of existing order details...")
        
        # Initialize MongoDB connection with Flask app context
        with app.app_context():
            mongo = init_mongo(app)
            
            # Get all orders that have details
            orders_data = list(mongo.db.orders.find({
                'details': {'$exists': True, '$ne': ''}
            }))
            
            print(f"📊 Found {len(orders_data)} orders with details to migrate")
            
            order_data_dir = os.path.join(os.path.dirname(__file__), 'order_data')
            os.makedirs(order_data_dir, exist_ok=True)
            
            migrated_count = 0
            failed_count = 0
            
            for order_data in orders_data:
                try:
                    tracking_code = order_data.get('tracking_code')
                    details = order_data.get('details', '')
                    
                    if not tracking_code or not details:
                        print(f"⚠️ Skipping order - missing tracking code or details")
                        failed_count += 1
                        continue
                    
                    # Create filename
                    details_filename = f"{tracking_code}_details.txt"
                    details_filepath = os.path.join(order_data_dir, details_filename)
                    
                    # Skip if file already exists
                    if os.path.exists(details_filepath):
                        print(f"⏭️ File already exists for {tracking_code}, skipping...")
                        continue
                    
                    # Write details to file
                    with open(details_filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Order Details - Tracking Code: {tracking_code}\n")
                        f.write(f"{"="*50}\n\n")
                        f.write(f"Customer Name: {order_data.get('name', 'N/A')}\n")
                        f.write(f"Email: {order_data.get('email', 'N/A')}\n")
                        f.write(f"Phone: {order_data.get('phone', 'N/A')}\n")
                        f.write(f"Project Type: {order_data.get('project_type', 'N/A')}\n")
                        
                        # Format creation date
                        created_at = order_data.get('created_at')
                        if created_at:
                            if isinstance(created_at, str):
                                f.write(f"Date: {created_at}\n")
                            else:
                                f.write(f"Date: {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        else:
                            f.write(f"Date: N/A\n")
                        
                        f.write(f"\nProject Details:\n")
                        f.write(f"{"-"*20}\n")
                        f.write(f"{details}\n")
                    
                    print(f"✅ Migrated order {tracking_code} to {details_filename}")
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"❌ Error migrating order {order_data.get('tracking_code', 'Unknown')}: {e}")
                    failed_count += 1
            
            print(f"\n📈 Migration Summary:")
            print(f"   ✅ Successfully migrated: {migrated_count}")
            print(f"   ❌ Failed to migrate: {failed_count}")
            print(f"   📁 Files saved in: {order_data_dir}")
            
            return migrated_count, failed_count
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 0, 0

if __name__ == "__main__":
    migrate_existing_orders()
