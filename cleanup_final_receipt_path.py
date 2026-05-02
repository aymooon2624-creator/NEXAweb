#!/usr/bin/env python3
"""
Script to remove final_receipt_path field from MongoDB orders collection
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Flask app to get database context
from app import app
from database import init_mongo

def cleanup_final_receipt_path():
    """Remove final_receipt_path field from all orders in MongoDB"""
    try:
        print("🚀 Starting cleanup of final_receipt_path field...")
        
        # Initialize MongoDB connection with Flask app context
        with app.app_context():
            mongo = init_mongo(app)
            
            # Get all orders
            orders_data = list(mongo.db.orders.find({}))
            
            print(f"📊 Found {len(orders_data)} orders to process")
            
            updated_count = 0
            failed_count = 0
            
            for order_data in orders_data:
                try:
                    order_id = order_data.get('_id')
                    tracking_code = order_data.get('tracking_code', 'Unknown')
                    
                    # Check if field exists
                    if 'final_receipt_path' in order_data:
                        print(f"📄 Found 'final_receipt_path' field in order {tracking_code}")
                        
                        # Remove the field using $unset
                        result = mongo.db.orders.update_one(
                            {'_id': order_id},
                            {'$unset': {'final_receipt_path': ''}}
                        )
                        
                        if result.modified_count > 0:
                            print(f"✅ Removed final_receipt_path from order {tracking_code}")
                            updated_count += 1
                        else:
                            print(f"⚠️ No changes made to order {tracking_code}")
                            failed_count += 1
                    else:
                        print(f"⏭️ No final_receipt_path field found in order {tracking_code}")
                
                except Exception as e:
                    print(f"❌ Error processing order {order_data.get('tracking_code', 'Unknown')}: {e}")
                    failed_count += 1
            
            print(f"\n📈 Cleanup Summary:")
            print(f"   ✅ Successfully updated: {updated_count}")
            print(f"   ❌ Failed to update: {failed_count}")
            print(f"   📊 Total orders processed: {len(orders_data)}")
            
            return updated_count, failed_count
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return 0, 0

def verify_cleanup():
    """Verify that final_receipt_path field has been removed"""
    try:
        print("\n🔍 Verifying cleanup...")
        
        with app.app_context():
            mongo = init_mongo(app)
            
            # Check for remaining final_receipt_path fields
            orders_with_final_receipt = mongo.db.orders.count_documents({'final_receipt_path': {'$exists': True}})
            
            print(f"📊 Verification Results:")
            print(f"   📄 Orders still with 'final_receipt_path' field: {orders_with_final_receipt}")
            
            if orders_with_final_receipt == 0:
                print("✅ Cleanup successful! All final_receipt_path fields have been removed.")
                return True
            else:
                print("⚠️ Some final_receipt_path fields still exist. Cleanup may be incomplete.")
                return False
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    # Run cleanup
    updated, failed = cleanup_final_receipt_path()
    
    # Verify cleanup
    success = verify_cleanup()
    
    if success:
        print("\n🎉 final_receipt_path cleanup completed successfully!")
    else:
        print("\n⚠️ final_receipt_path cleanup completed with issues.")
