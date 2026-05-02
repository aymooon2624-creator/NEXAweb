#!/usr/bin/env python3
"""
Migration script to move existing uploaded files to new order_attachments structure
"""

import os
import sys
import shutil
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Flask app to get database context
from app import app
from database import init_mongo

def migrate_attachments():
    """Migrate existing uploaded files to new order_attachments structure"""
    try:
        print("🚀 Starting migration of existing attachments...")
        
        # Initialize MongoDB connection with Flask app context
        with app.app_context():
            mongo = init_mongo(app)
            
            # Get all orders that have file_path
            orders_data = list(mongo.db.orders.find({
                'file_path': {'$exists': True, '$ne': None, '$ne': ''}
            }))
            
            print(f"📊 Found {len(orders_data)} orders with attachments to migrate")
            
            # Define paths
            old_uploads_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
            new_attachments_dir = os.path.join(os.path.dirname(__file__), 'order_attachments')
            
            migrated_count = 0
            failed_count = 0
            skipped_count = 0
            
            for order_data in orders_data:
                try:
                    tracking_code = order_data.get('tracking_code')
                    old_file_path = order_data.get('file_path', '')
                    original_filename = order_data.get('original_filename', '')
                    
                    if not tracking_code or not old_file_path:
                        print(f"⚠️ Skipping order - missing tracking code or file path")
                        skipped_count += 1
                        continue
                    
                    # Extract filename from old path
                    if '/' in old_file_path:
                        old_filename = old_file_path.split('/')[-1]
                    else:
                        old_filename = old_file_path
                    
                    # Old full path
                    old_full_path = os.path.join(old_uploads_dir, old_filename)
                    
                    # New directory and path
                    new_tracking_dir = os.path.join(new_attachments_dir, tracking_code)
                    os.makedirs(new_tracking_dir, exist_ok=True)
                    
                    # Use original filename if available, otherwise use the old filename
                    if original_filename and original_filename.strip():
                        new_filename = os.path.basename(original_filename)
                    else:
                        new_filename = old_filename
                    
                    new_full_path = os.path.join(new_tracking_dir, new_filename)
                    new_db_path = os.path.join('order_attachments', tracking_code, new_filename).replace('\\', '/')
                    
                    # Skip if file already exists in new location
                    if os.path.exists(new_full_path):
                        print(f"⏭️ File already exists for {tracking_code}, skipping...")
                        skipped_count += 1
                        continue
                    
                    # Skip if old file doesn't exist
                    if not os.path.exists(old_full_path):
                        print(f"⚠️ Old file not found for {tracking_code}: {old_full_path}")
                        failed_count += 1
                        continue
                    
                    # Copy file to new location
                    shutil.copy2(old_full_path, new_full_path)
                    
                    # Update database record
                    mongo.db.orders.update_one(
                        {'_id': order_data['_id']},
                        {'$set': {'file_path': new_db_path}}
                    )
                    
                    print(f"✅ Migrated attachment for {tracking_code}:")
                    print(f"   From: {old_full_path}")
                    print(f"   To: {new_full_path}")
                    
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"❌ Error migrating attachment for {order_data.get('tracking_code', 'Unknown')}: {e}")
                    failed_count += 1
            
            print(f"\n📈 Migration Summary:")
            print(f"   ✅ Successfully migrated: {migrated_count}")
            print(f"   ❌ Failed to migrate: {failed_count}")
            print(f"   ⏭️ Skipped: {skipped_count}")
            print(f"   📁 New attachments directory: {new_attachments_dir}")
            print(f"   📁 Old uploads directory: {old_uploads_dir}")
            
            return migrated_count, failed_count, skipped_count
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 0, 0, 0

if __name__ == "__main__":
    migrate_attachments()
