#!/usr/bin/env python3
"""
Script to remove file-related fields from MongoDB orders
"""

from pymongo import MongoClient

def remove_file_fields_from_orders():
    """Remove file_path, original_filename, and receipt fields from all orders"""
    
    try:
        # Connect to MongoDB Atlas (replace with your actual URI)
        mongo = MongoClient("mongodb+srv://username:password@cluster.mongodb.net/nexaweb?retryWrites=true&w=majority")
        db = mongo.nexaweb
        orders_collection = db.orders
        
        print("🔍 Connected to MongoDB Atlas")
        
        # Get all orders
        orders = list(orders_collection.find())
        print(f"📊 Found {len(orders)} orders")
        
        updated_count = 0
        
        for order in orders:
            tracking_code = order.get('tracking_code', 'Unknown')
            order_id = order.get('_id')
            
            # Fields to remove
            fields_to_remove = [
                'file_path',
                'original_filename', 
                'deposit_receipt_path',
                'final_receipt_path'
            ]
            
            # Check if any file fields exist
            has_file_fields = any(field in order for field in fields_to_remove)
            
            if has_file_fields:
                print(f"🗑️  Removing file fields from order: {tracking_code}")
                
                # Create update operation
                update_fields = {}
                for field in fields_to_remove:
                    if field in order:
                        update_fields[field] = ""
                        print(f"   - Removing {field}: {order[field]}")
                
                if update_fields:
                    # Remove the fields
                    result = orders_collection.update_one(
                        {'_id': order_id},
                        {'$unset': update_fields}
                    )
                    
                    if result.modified_count > 0:
                        updated_count += 1
                        print(f"   ✅ Updated successfully")
                    else:
                        print(f"   ❌ Update failed")
            else:
                print(f"ℹ️  No file fields in order: {tracking_code}")
        
        print(f"\n📊 Summary:")
        print(f"   Total orders: {len(orders)}")
        print(f"   Orders updated: {updated_count}")
        print(f"   Orders without file fields: {len(orders) - updated_count}")
        
        mongo.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔄 Starting removal of file fields from orders...")
    remove_file_fields_from_orders()
    print("✅ Process completed!")
