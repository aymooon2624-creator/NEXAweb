#!/usr/bin/env python3
"""
Script to remove unwanted fields from MongoDB orders collection
Removes: details, original_filename
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

def cleanup_order_fields():
    """Remove unwanted fields from all orders in MongoDB"""
    try:
        print("🚀 Starting cleanup of MongoDB order fields...")
        
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
                    
                    # Check which fields to remove
                    fields_to_remove = {}
                    
                    if 'details' in order_data:
                        fields_to_remove['details'] = ""
                        print(f"📝 Found 'details' field in order {tracking_code}")
                    
                    if 'original_filename' in order_data:
                        fields_to_remove['original_filename'] = ""
                        print(f"📄 Found 'original_filename' field in order {tracking_code}")
                    
                    if fields_to_remove:
                        # Remove the unwanted fields using $unset
                        unset_fields = {}
                        for field in fields_to_remove.keys():
                            unset_fields[field] = ""
                        
                        result = mongo.db.orders.update_one(
                            {'_id': order_id},
                            {'$unset': unset_fields}
                        )
                        
                        if result.modified_count > 0:
                            print(f"✅ Removed fields from order {tracking_code}: {list(fields_to_remove.keys())}")
                            updated_count += 1
                        else:
                            print(f"⚠️ No changes made to order {tracking_code}")
                            failed_count += 1
                    else:
                        print(f"⏭️ No unwanted fields found in order {tracking_code}")
                
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
    """Verify that unwanted fields have been removed"""
    try:
        print("\n🔍 Verifying cleanup...")
        
        with app.app_context():
            mongo = init_mongo(app)
            
            # Check for remaining unwanted fields
            orders_with_details = mongo.db.orders.count_documents({'details': {'$exists': True}})
            orders_with_original_filename = mongo.db.orders.count_documents({'original_filename': {'$exists': True}})
            
            print(f"📊 Verification Results:")
            print(f"   📝 Orders still with 'details' field: {orders_with_details}")
            print(f"   📄 Orders still with 'original_filename' field: {orders_with_original_filename}")
            
            if orders_with_details == 0 and orders_with_original_filename == 0:
                print("✅ Cleanup successful! All unwanted fields have been removed.")
                return True
            else:
                print("⚠️ Some unwanted fields still exist. Cleanup may be incomplete.")
                return False
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    # Run cleanup
    updated, failed = cleanup_order_fields()
    
    # Verify cleanup
    success = verify_cleanup()
    
    if success:
        print("\n🎉 MongoDB field cleanup completed successfully!")
    else:
        print("\n⚠️ MongoDB field cleanup completed with issues.")
